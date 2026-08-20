import re

from django.conf import settings

from ai.gemini import GeminiProvider


def _text_value(value, fallback="") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _normalise_analysis(analysis: dict, fallback_text: str) -> dict:
    if not isinstance(analysis, dict):
        raise ValueError("AI analysis must be a JSON object.")
    fallback = analyze_text(fallback_text)
    summary = _text_value(analysis.get("summary"), fallback["summary"])
    recaps = analysis.get("recaps") if isinstance(analysis.get("recaps"), dict) else {}
    character_details = analysis.get("character_details")
    if not isinstance(character_details, list):
        character_details = []
    character_details = [
        {"name": _text_value(item.get("name")), "detail": _text_value(item.get("detail"))}
        for item in character_details
        if isinstance(item, dict) and _text_value(item.get("name"))
    ]
    themes = analysis.get("themes") if isinstance(analysis.get("themes"), list) else []
    questions = analysis.get("questions") if isinstance(analysis.get("questions"), list) else []
    return {
        "summary": summary,
        "recaps": {
            "quick": _text_value(recaps.get("quick"), summary),
            "standard": _text_value(recaps.get("standard"), summary),
            "detailed": _text_value(recaps.get("detailed"), summary),
        },
        "characters": [item for item in analysis.get("characters", []) if isinstance(item, str)],
        "character_details": character_details,
        "themes": [item for item in themes if isinstance(item, str)],
        "questions": [item for item in questions if isinstance(item, dict)],
        "word_count": analysis.get("word_count", fallback["word_count"]),
        "sentence_count": analysis.get("sentence_count", fallback["sentence_count"]),
        "important_details": analysis.get("important_details", []),
        "relationships": analysis.get("relationships", []),
        "current_situation": _text_value(analysis.get("current_situation")),
        "provider": "gemini",
    }


def _build_recap_versions(sentences: list[str]) -> tuple[str, str, str]:
    if not sentences:
        return ("No readable text was found.", "No readable text was found.", "No readable text was found.")

    full_text = " ".join(sentences)

    quick_count = min(2, len(sentences))
    quick = " ".join(sentences[:quick_count]).strip()
    if len(quick) < 120 and len(sentences) > quick_count:
        quick = " ".join(sentences[: min(3, len(sentences))]).strip()
    quick = quick[:300].strip()

    standard_count = min(5, max(3, len(sentences)))
    standard = " ".join(sentences[:standard_count]).strip()
    if len(standard) <= len(quick):
        standard = " ".join(sentences[: min(6, len(sentences))]).strip() or full_text[:700].strip()
    standard = standard[:700].strip()

    detailed = full_text[:1200].strip()
    if len(detailed) <= len(standard):
        detailed = full_text[:1800].strip() or standard

    if len(quick) >= len(standard):
        quick = quick[: max(80, len(quick) // 2)].strip()
    if len(standard) >= len(detailed):
        detailed = (full_text[:1800] or standard).strip()

    return quick, standard, detailed


def analyze_text(text: str) -> dict:
    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    names = sorted(
        {
            match.group(0)
            for match in re.finditer(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b", text)
        }
    )[:20]
    quick, standard, detailed = _build_recap_versions(sentences)
    summary = standard
    character_details = [
        {"name": name, "detail": "Mentioned in the selected reading boundary."}
        for name in names
    ]
    questions = [
        {"question": "What should I remember from this section?", "answer": detailed},
        {"question": "Who appears in this section?", "answer": ", ".join(names) or "No character names were detected."},
        {"question": "What happens next?", "answer": "That is beyond your selected reading boundary."},
    ]
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "characters": names,
        "character_details": character_details,
        "themes": [],
        "summary": summary,
        "recaps": {"quick": quick, "standard": standard, "detailed": detailed},
        "questions": questions,
        "provider": "local",
    }


def analyze_text_with_ai(text: str, title: str, boundary: int) -> dict:
    config = settings.PAGEBACK_AI
    if not config["api_key"]:
        return analyze_text(text)

    try:
        prompt = (
            "Analyze only the supplied reading boundary. Return one valid JSON object and no markdown. "
            "Use only explicit evidence from the supplied text; do not predict or invent. "
            "Write naturally, calmly, and chronologically, like a helpful literary friend. "
            "Return these keys: summary (string), recaps (object with quick, standard, detailed strings), "
            "characters (array of important names only), character_details (array of name/detail objects), "
            "themes (array of supported strings), important_details (array of concise objects), "
            "relationships (array of supported objects), current_situation (string), "
            "questions (array of question/answer objects), word_count (integer), sentence_count (integer). "
            "The quick recap should be 5-8 concise bullet points and fit a 30-second refresh. "
            "The standard recap should cover chronological events, characters, relationships, details, "
            "and current situation in roughly 350-600 words when enough text exists. "
            "The detailed recap should cover the progression, development, unresolved conflicts, supported "
            "themes, atmosphere, and what to remember in roughly 800-1500 words when enough text exists. "
            "Do not pad short source material."
        )
        provider = GeminiProvider(
            api_key=config["api_key"],
            model=config["model"],
            embedding_model=config["embedding_model"],
        )
        analysis = provider.generate_structured(
            prompt,
            f"Book: {title}\nBoundary: chapter {boundary}\n\n{text[:100000]}",
        )
        return _normalise_analysis(analysis, text)
    except Exception as error:
        fallback = analyze_text(text)
        fallback["ai_error"] = f"AI analysis failed ({type(error).__name__}). Local analysis was used."
        if "insufficient_quota" in str(error) or "exceeded your current quota" in str(error):
            fallback["provider"] = "local"
            fallback["ai_error"] = "AI quota is exhausted. Add API billing or credits to enable AI analysis."
        return fallback