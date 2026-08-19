"""Provider interface for chat, structured JSON, and embeddings."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Vendor-neutral LLM access used by extractors, recaps, and chat."""

    @abstractmethod
    def generate(self, prompt: str, context: str = "") -> str:
        """Return free-text completion."""

    @abstractmethod
    def generate_structured(self, prompt: str, context: str = "") -> dict[str, Any]:
        """Return parsed JSON. Implementations must not execute the payload."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for retrieval."""


class AIUnavailableError(Exception):
    """Raised when the configured provider cannot be reached or has no key."""


class AIResponseError(Exception):
    """Raised when the provider returns empty, timed-out, or unusable output."""
