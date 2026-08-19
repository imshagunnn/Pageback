import re

from django.conf import settings

from ai.gemini import GeminiProvider


def analyze_text(text: str) -> dict:
    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    names = sorted(
        {
            match.group(0)
            for match in re.finditer(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b", text)
        }
    )[:20]
    opening = " ".join(sentences[:3])[:800] or "No readable text was found."
    extended = " ".join(sentences[:8])[:1800] or opening
    detailed = " ".join(sentences[:16])[:3600] or extended
    character_details = [
        {"name": name, "detail": "Mentioned in the selected reading boundary."}
        for name in names
    ]
    questions = [
        {"question": "What should I remember from this section?", "answer": extended},
        {"question": "Who appears in this section?", "answer": ", ".join(names) or "No character names were detected."},
        {"question": "What happens next?", "answer": "That is beyond your selected reading boundary."},
    ]
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "characters": names,
        "character_details": character_details,
        "themes": [],
        "summary": opening,
        "recaps": {"quick": opening, "standard": extended, "detailed": detailed},
        "questions": questions,
        "provider": "local",
    }


def analyze_text_with_ai(text: str, title: str, boundary: int) -> dict:
    config = settings.PAGEBACK_AI
    if not config["api_key"]:
        return analyze_text(text)

    try:
        prompt = (
            "Analyze only the supplied reading boundary. Return JSON with exactly these keys: "
            "summary (string), recaps (object with quick, standard, detailed strings), "
            "characters (array of short names), character_details (array of name/detail objects), "
            "themes (array of short strings), questions (array of question/answer objects), "
            "word_count (integer), sentence_count (integer). Do not invent details."
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
        analysis.setdefault("recaps", {"quick": analysis.get("summary", ""), "standard": analysis.get("summary", ""), "detailed": analysis.get("summary", "")})
        analysis.setdefault("character_details", [{"name": name, "detail": "Appears in the selected boundary."} for name in analysis.get("characters", [])])
        analysis.setdefault("themes", [])
        analysis.setdefault("questions", [])
        analysis["provider"] = "gemini"
        return analysis
    except Exception as error:
        fallback = analyze_text(text)
        if "insufficient_quota" in str(error) or "exceeded your current quota" in str(error):
            fallback["provider"] = "local"
            fallback["ai_error"] = "AI quota is exhausted. Add API billing or credits to enable AI analysis."
        else:
            fallback["ai_error"] = "AI could not be reached, so local analysis was used."
        return fallback