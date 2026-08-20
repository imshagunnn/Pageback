from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from novels.models import Collection, Novel, NovelStatus
from reading.models import ReadingProgress

def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "web/landing.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


def demo(request):
    return render(request, "web/demo.html")


@login_required
def dashboard(request):
    novels = list(request.user.novels.prefetch_related("chapters", "reading_progress__current_chapter", "collections")) if hasattr(request.user, "novels") else []
    all_novels = novels[:]
    for novel in all_novels:
        progress = novel.reading_progress.first()
        novel.current_reading_chapter = progress.current_chapter if progress else None
        novel.progress_percent = round((progress.boundary_chapter_number / novel.total_chapters) * 100) if progress and novel.total_chapters else 0
        novel.is_currently_reading = bool(progress and progress.boundary_chapter_number and novel.status == NovelStatus.ACTIVE)
        novel.is_completed = novel.status == NovelStatus.COMPLETED or novel.progress_percent >= 100
    section = request.GET.get("section", "all")
    query = request.GET.get("q", "").strip()
    collection_id = request.GET.get("collection", "")
    if query:
        novels = [novel for novel in novels if query.casefold() in novel.title.casefold() or query.casefold() in novel.author.casefold()]
    if section == "reading":
        novels = [novel for novel in novels if novel.is_currently_reading]
    elif section == "completed":
        novels = [novel for novel in novels if novel.is_completed]
    elif section == "favorites":
        novels = [novel for novel in novels if novel.is_favorite and novel.status != NovelStatus.TRASHED]
    elif section == "archive":
        novels = [novel for novel in novels if novel.status == NovelStatus.ARCHIVED]
    elif section == "trash":
        novels = [novel for novel in novels if novel.status == NovelStatus.TRASHED]
    else:
        novels = [novel for novel in novels if novel.status in {NovelStatus.ACTIVE, NovelStatus.COMPLETED}]
    if collection_id:
        try:
            collection = request.user.book_collections.get(id=int(collection_id))
            novels = [novel for novel in novels if collection in novel.collections.all()]
        except (ValueError, Collection.DoesNotExist):
            collection = None
    else:
        collection = None
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        novels.sort(key=lambda novel: novel.title.casefold())
    elif sort == "author":
        novels.sort(key=lambda novel: novel.author.casefold())
    elif sort == "progress":
        novels.sort(key=lambda novel: novel.progress_percent, reverse=True)
    else:
        novels.sort(key=lambda novel: novel.last_opened_at or novel.updated_at, reverse=True)
    collections = list(request.user.book_collections.all())
    total_chapters = sum(novel.total_chapters for novel in novels)
    counts = {
        "all": request.user.novels.exclude(status=NovelStatus.TRASHED).exclude(status=NovelStatus.ARCHIVED).count(),
        "reading": sum(novel.is_currently_reading for novel in all_novels),
        "completed": request.user.novels.filter(status=NovelStatus.COMPLETED).count(),
        "favorites": request.user.novels.filter(is_favorite=True).exclude(status=NovelStatus.TRASHED).count(),
        "archive": request.user.novels.filter(status=NovelStatus.ARCHIVED).count(),
        "trash": request.user.novels.filter(status=NovelStatus.TRASHED).count(),
    }
    return render(request, "web/dashboard.html", {"novels": novels, "total_chapters": total_chapters, "collections": collections, "section": section, "query": query, "sort": sort, "selected_collection": collection, "counts": counts})


@login_required
def library_action(request, novel_id):
    novel = get_object_or_404(request.user.novels, id=novel_id)
    action = request.POST.get("action")
    if action == "archive":
        novel.status = NovelStatus.ARCHIVED
    elif action == "trash":
        novel.status = NovelStatus.TRASHED
        novel.deleted_at = timezone.now()
    elif action == "restore":
        progress = novel.reading_progress.first()
        novel.status = NovelStatus.COMPLETED if progress and progress.boundary_chapter_number >= novel.total_chapters else NovelStatus.ACTIVE
        novel.deleted_at = None
    elif action == "favorite":
        novel.is_favorite = not novel.is_favorite
    elif action == "collections":
        collection_ids = request.POST.getlist("collection_ids")
        owned_collections = request.user.book_collections.filter(id__in=collection_ids)
        novel.collections.set(owned_collections)
    elif action == "restart":
        progress = novel.reading_progress.first()
        if progress:
            progress.current_chapter = None
            progress.reading_status = "not_started"
            progress.save(update_fields=["current_chapter", "reading_status"])
        novel.status = NovelStatus.ACTIVE
        novel.completed_at = None
    elif action == "permanent_delete":
        if novel.cover_image:
            novel.cover_image.delete(save=False)
        novel.delete()
        return redirect("dashboard")
    novel.save(update_fields=["status", "deleted_at", "is_favorite", "completed_at", "updated_at"])
    return redirect(request.POST.get("next") or "dashboard")


@login_required
def create_collection(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            collection, _ = Collection.objects.get_or_create(owner=request.user, name=name, defaults={"description": request.POST.get("description", "")})
            return redirect(request.POST.get("next") or "dashboard")
    return redirect("dashboard")


@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(request.user.book_collections, id=collection_id)
    if request.method == "POST":
        novel = get_object_or_404(request.user.novels, id=request.POST.get("novel_id"))
        collection.novels.remove(novel)
        return redirect("collection_detail", collection_id=collection.id)
    novels = list(collection.novels.prefetch_related("chapters", "reading_progress__current_chapter"))
    for novel in novels:
        progress = novel.reading_progress.first()
        novel.current_reading_chapter = progress.current_chapter if progress else None
        novel.progress_percent = round((progress.boundary_chapter_number / novel.total_chapters) * 100) if progress and novel.total_chapters else 0
    return render(request, "web/collection_detail.html", {"collection": collection, "novels": novels})
