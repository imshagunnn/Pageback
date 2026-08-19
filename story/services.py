from story.models import Character, ImportantDetail, ThemeMotif


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