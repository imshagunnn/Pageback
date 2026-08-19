from django.utils import timezone

from novels.models import Chapter, Novel
from reading.models import ReadingProgress, ReadingStatus
from reading.models import Recap, RecapType


def get_progress(user, novel: Novel) -> ReadingProgress:
    progress, _ = ReadingProgress.objects.get_or_create(user=user, novel=novel)
    return progress


def chapters_through_boundary(novel: Novel, boundary: int, start: int = 1):
    return novel.chapters.filter(
        chapter_number__gte=start,
        chapter_number__lte=boundary,
    ).order_by("chapter_number")


def set_reading_boundary(user, novel: Novel, boundary: int) -> ReadingProgress:
    chapter = novel.chapters.get(chapter_number=boundary)
    progress = get_progress(user, novel)
    progress.current_chapter = chapter
    progress.last_read_at = timezone.now()
    progress.reading_status = ReadingStatus.READING
    progress.save(update_fields=["current_chapter", "last_read_at", "reading_status"])
    return progress


def cache_recaps(user, novel: Novel, start: int, boundary: int, analysis: dict, chapters) -> None:
    latest_updated = chapters.last().updated_at
    recap_values = {
        RecapType.QUICK_30: analysis.get("recaps", {}).get("quick", analysis.get("summary", "")),
        RecapType.STANDARD_2MIN: analysis.get("recaps", {}).get("standard", analysis.get("summary", "")),
        RecapType.DETAILED_5MIN: analysis.get("recaps", {}).get("detailed", analysis.get("summary", "")),
    }
    for recap_type, content in recap_values.items():
        Recap.objects.update_or_create(
            user=user,
            novel=novel,
            from_chapter=start,
            to_chapter=boundary,
            recap_type=recap_type,
            defaults={
                "content": content,
                "structured_data": analysis,
                "source_updated_at": latest_updated,
            },
        )