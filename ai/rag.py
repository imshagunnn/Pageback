"""Spoiler-safe retrieval.

Retrieval must filter by novel_id and chapter_number <= reading boundary
in the query itself, not only in the LLM prompt.
"""


from novels.models import EmbeddingChunk


def retrieve(novel, boundary: int, query: str = "", limit: int = 8):
    """Return only chunks at or before the reader's boundary.

    The spoiler predicate is part of the queryset before any ranking or slicing.
    A lexical fallback keeps this useful before a vector provider is configured.
    """
    chunks = EmbeddingChunk.objects.filter(
        chapter__novel=novel,
        chapter__chapter_number__lte=boundary,
    )
    if query.strip():
        terms = {term.lower() for term in query.split() if term.strip()}
        ranked = []
        for chunk in chunks:
            score = sum(chunk.text.lower().count(term) for term in terms)
            ranked.append((score, chunk))
        ranked.sort(key=lambda item: (-item[0], item[1].chapter.chapter_number, item[1].chunk_index))
        return [chunk for _, chunk in ranked[:limit]]
    return list(chunks[:limit])
