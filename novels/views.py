from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
import logging
import hashlib

from novels.forms import AnalysisForm, NovelImportForm
from novels.importers import extract_book_cover, extract_book_structure
from novels.models import Chapter, Novel
from ai.analyzer import analyze_text, analyze_text_with_ai
from reading.services import cache_recaps, chapters_through_boundary, get_cached_analysis, get_progress, set_reading_boundary
from story.services import persist_analysis


logger = logging.getLogger(__name__)


@login_required
def import_novel(request):
	if request.method == "POST":
		form = NovelImportForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				raw_upload = form.cleaned_data["text_file"].read()
				form.cleaned_data["text_file"].seek(0)
				fingerprint = hashlib.sha256(raw_upload).hexdigest()
				existing = request.user.novels.filter(source_fingerprint=fingerprint).first()
				if existing:
					form.add_error("text_file", "This book is already in your library.")
					return render(request, "web/import.html", {"form": form, "existing_novel": existing})
				import_summary = extract_book_structure(form.cleaned_data["text_file"])
				chapters = import_summary.sections
				cover = extract_book_cover(form.cleaned_data["text_file"])
				import_summary.cover_detected = cover is not None
				logger.info(
					"Imported %s: format=%s sections=%s front_matter=%s toc=%s cover=%s confidence=%s",
					form.cleaned_data["title"],
					import_summary.format,
					len(chapters),
					import_summary.front_matter_detected,
					import_summary.toc_detected,
					import_summary.cover_detected,
					import_summary.confidence,
				)
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
							source_fingerprint=fingerprint,
						)
						for chapter_number, section in enumerate(chapters, start=1):
							Chapter.objects.create(
								novel=novel,
								chapter_number=chapter_number,
								title=section.title or f"Section {chapter_number}",
								content=section.content,
								source_page_start=section.source_page_start,
								source_page_end=section.source_page_end,
								content_type=section.content_type,
								parent_title=section.parent_title,
							)
						if cover:
							novel.cover_image.save(cover.name, cover, save=True)
					return redirect("novel_detail", novel_id=novel.id)
	else:
		form = NovelImportForm()

	return render(request, "web/import.html", {"form": form})


@login_required
def novel_detail(request, novel_id):
	novel = request.user.novels.prefetch_related("chapters").get(id=novel_id)
	novel.last_opened_at = timezone.now()
	novel.save(update_fields=["last_opened_at", "updated_at"])
	chapters = list(novel.chapters.all())
	progress = get_progress(request.user, novel)
	progress_percent = round((progress.boundary_chapter_number / len(chapters)) * 100) if chapters and progress.boundary_chapter_number else 0
	current_boundary = progress.boundary_chapter_number or novel.analysis_boundary
	current_start = int(novel.analysis.get("from_chapter", 1))
	current_end = int(novel.analysis.get("through_chapter", current_boundary))
	if chapters and (not novel.analysis.get("summary") or "recaps" not in novel.analysis):
		novel.analysis = analyze_text(
			"\n\n".join(chapter.content for chapter in chapters_through_boundary(novel, current_boundary))
		)
		novel.analysis["from_chapter"] = 1
		novel.analysis["through_chapter"] = current_boundary
		novel.analysis["ai_error"] = "This analysis was created locally before AI was configured. Submit the boundary again to run AI analysis."
	elif novel.analysis.get("provider") == "local" and not novel.analysis.get("ai_error"):
		novel.analysis["ai_error"] = "This analysis was created locally before AI was configured. Submit the boundary again to run AI analysis."
	if request.method == "POST":
		form = AnalysisForm(request.POST)
		if form.is_valid() and form.cleaned_data["through_chapter"] <= len(chapters):
			start = form.cleaned_data["from_chapter"]
			boundary = form.cleaned_data["through_chapter"]
			if start > boundary:
				form.add_error("from_chapter", "The starting chapter must come before the ending chapter.")
				return render(request, "web/novel_detail.html", {"novel": novel, "chapters": chapters, "chapter_count": len(chapters), "progress": progress, "progress_percent": progress_percent, "form": form})
			set_reading_boundary(request.user, novel, boundary)
			allowed_chapters = chapters_through_boundary(novel, boundary, start)
			analysis = get_cached_analysis(request.user, novel, start, boundary, allowed_chapters)
			if analysis is None:
				analysis = analyze_text_with_ai(
					"\n\n".join(chapter.content for chapter in allowed_chapters),
					novel.title,
					boundary,
				)
			analysis["from_chapter"] = start
			analysis["through_chapter"] = boundary
			novel.analysis_boundary = boundary
			novel.analysis = analysis
			novel.save(update_fields=["analysis_boundary", "analysis", "updated_at"])
			persist_analysis(novel, list(allowed_chapters), analysis)
			cache_recaps(request.user, novel, start, boundary, analysis, allowed_chapters)
			return redirect("novel_detail", novel_id=novel.id)
		if form.is_valid():
			form.add_error("through_chapter", f"Choose a chapter from 1 to {len(chapters)}.")
	else:
		form = AnalysisForm(initial={"through_chapter": current_end, "from_chapter": current_start})
	return render(
		request,
		"web/novel_detail.html",
		{"novel": novel, "chapters": chapters, "chapter_count": len(chapters), "progress": progress, "progress_percent": progress_percent, "form": form},
	)
