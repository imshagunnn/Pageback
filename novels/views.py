from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from novels.forms import AnalysisForm, NovelImportForm
from novels.importers import extract_book_chapters
from novels.models import Chapter, Novel
from ai.analyzer import analyze_text, analyze_text_with_ai
from reading.services import cache_recaps, chapters_through_boundary, get_progress, set_reading_boundary
from story.services import persist_analysis


@login_required
def import_novel(request):
	if request.method == "POST":
		form = NovelImportForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				chapters = extract_book_chapters(form.cleaned_data["text_file"])
			except (UnicodeDecodeError, ValueError, Exception) as error:
				form.add_error("text_file", f"Could not read this book: {error}")
			else:
				if not chapters:
					form.add_error("text_file", "No readable text was found in this book.")
				else:
					with transaction.atomic():
						novel = Novel.objects.create(
							owner=request.user,
							title=form.cleaned_data["title"],
							author=form.cleaned_data["author"],
						)
						for chapter_number, content in enumerate(chapters, start=1):
							Chapter.objects.create(
								novel=novel,
								chapter_number=chapter_number,
								title=f"Chapter {chapter_number}",
								content=content,
							)
					return redirect("novel_detail", novel_id=novel.id)
	else:
		form = NovelImportForm()

	return render(request, "web/import.html", {"form": form})


@login_required
def novel_detail(request, novel_id):
	novel = request.user.novels.prefetch_related("chapters").get(id=novel_id)
	chapters = list(novel.chapters.all())
	progress = get_progress(request.user, novel)
	current_boundary = progress.boundary_chapter_number or novel.analysis_boundary
	if chapters and (not novel.analysis.get("summary") or "recaps" not in novel.analysis):
		novel.analysis = analyze_text(
			"\n\n".join(chapter.content for chapter in chapters_through_boundary(novel, current_boundary))
		)
	if request.method == "POST":
		form = AnalysisForm(request.POST)
		if form.is_valid() and form.cleaned_data["through_chapter"] <= len(chapters):
			start = form.cleaned_data["from_chapter"]
			boundary = form.cleaned_data["through_chapter"]
			if start > boundary:
				form.add_error("from_chapter", "The starting chapter must come before the ending chapter.")
				return render(request, "web/novel_detail.html", {"novel": novel, "chapters": chapters, "chapter_count": len(chapters), "progress": progress, "form": form})
			set_reading_boundary(request.user, novel, boundary)
			analysis = analyze_text_with_ai(
				"\n\n".join(chapter.content for chapter in chapters_through_boundary(novel, boundary, start)),
				novel.title,
				boundary,
			)
			allowed_chapters = chapters_through_boundary(novel, boundary, start)
			novel.analysis_boundary = boundary
			novel.analysis = analysis
			novel.save(update_fields=["analysis_boundary", "analysis", "updated_at"])
			persist_analysis(novel, list(allowed_chapters), analysis)
			cache_recaps(request.user, novel, start, boundary, analysis, allowed_chapters)
			return redirect("novel_detail", novel_id=novel.id)
		if form.is_valid():
			form.add_error("through_chapter", f"Choose a chapter from 1 to {len(chapters)}.")
	else:
		form = AnalysisForm(initial={"through_chapter": novel.analysis_boundary, "from_chapter": 1})
	return render(
		request,
		"web/novel_detail.html",
		{"novel": novel, "chapters": chapters, "chapter_count": len(chapters), "progress": progress, "form": form},
	)
