from story.models import Character, DetailCategory, Importance, ImportantDetail, ThemeMotif


def persist_analysis(novel, chapters, analysis: dict) -> None:
    chapter_by_number = {chapter.chapter_number: chapter for chapter in chapters}
    for character_data in analysis.get("character_details", []):
        name = character_data.get("name", "").strip()
        if not name:
            continue
        first_chapter = next(
            (chapter for chapter in chapters if name.lower() in chapter.content.lower()),
            None,
        )
        Character.objects.update_or_create(
            novel=novel,
            name=name,
            defaults={
                "description": character_data.get("detail", ""),
                "aliases": character_data.get("aliases", []) if isinstance(character_data.get("aliases", []), list) else [],
                "role": character_data.get("role", "") if isinstance(character_data.get("role", ""), str) else "",
                "first_appearance": first_chapter,
            },
        )

    for theme in analysis.get("themes", []):
        if not isinstance(theme, str) or not theme.strip():
            continue
        ThemeMotif.objects.get_or_create(
            novel=novel,
            chapter=chapter_by_number.get(novel.analysis_boundary, chapters[-1]),
            name=theme.strip()[:160],
            defaults={"description": "Detected within the selected reading boundary."},
        )

    for detail_data in analysis.get("important_details", []):
        if not isinstance(detail_data, dict):
            continue
        title = detail_data.get("title", "").strip()
        description = detail_data.get("description", "").strip()
        if not title or not description:
            continue
        chapter_number = detail_data.get("chapter", novel.analysis_boundary)
        chapter = chapter_by_number.get(chapter_number, chapters[-1] if chapters else None)
        if chapter is None:
            continue
        ImportantDetail.objects.update_or_create(
            novel=novel,
            chapter=chapter,
            title=title[:255],
            defaults={
                "description": description,
                "category": detail_data.get("category") if detail_data.get("category") in DetailCategory.values else DetailCategory.OTHER,
                "importance": detail_data.get("importance") if detail_data.get("importance") in Importance.values else Importance.MINOR,
                "evidence_reference": detail_data.get("evidence_reference", ""),
            },
        )