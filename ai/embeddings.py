"""Small, replaceable embedding storage helpers."""

from django.conf import settings

from ai.gemini import GeminiProvider
from novels.models import EmbeddingChunk


def chunk_text(text: str, words_per_chunk: int = 500) -> list[str]:
    words = text.split()
    return [" ".join(words[start:start + words_per_chunk]) for start in range(0, len(words), words_per_chunk)]


def store_chapter_chunks(chapter, chunks: list[str], vectors: list[list[float]] | None = None) -> None:
    vectors = vectors or [[] for _ in chunks]
    EmbeddingChunk.objects.filter(chapter=chapter).delete()
    EmbeddingChunk.objects.bulk_create(
        [EmbeddingChunk(chapter=chapter, chunk_index=index, text=text, vector=vectors[index]) for index, text in enumerate(chunks)]
    )


def embed_with_gemini(text: str) -> list[float]:
    config = settings.PAGEBACK_AI
    provider = GeminiProvider(
        api_key=config["api_key"],
        model=config["model"],
        embedding_model=config["embedding_model"],
    )
    return provider.embed(text)
