from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


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
    novels = list(request.user.novels.prefetch_related("chapters", "reading_progress__current_chapter")) if hasattr(request.user, "novels") else []
    for novel in novels:
        progress = novel.reading_progress.first()
        novel.current_reading_chapter = progress.current_chapter if progress else None
        novel.progress_percent = round((progress.boundary_chapter_number / novel.total_chapters) * 100) if progress and novel.total_chapters else 0
    total_chapters = sum(novel.total_chapters for novel in novels)
    return render(request, "web/dashboard.html", {"novels": novels, "total_chapters": total_chapters})
