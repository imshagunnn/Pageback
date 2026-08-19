import json
from typing import Any

from google import genai
from google.genai import types

from ai.client import AIProvider, AIResponseError, AIUnavailableError


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str, embedding_model: str):
        if not api_key:
            raise AIUnavailableError("GEMINI_API_KEY is not configured.")
        self.model = model
        self.embedding_model = embedding_model
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000),
        )

    def generate(self, prompt: str, context: str = "") -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{prompt}\n\nContext:\n{context}",
        )
        if not response.text:
            raise AIResponseError("Gemini returned an empty response.")
        return response.text

    def generate_structured(self, prompt: str, context: str = "") -> dict[str, Any]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{prompt}\n\nContext:\n{context}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        if not response.text:
            raise AIResponseError("Gemini returned an empty structured response.")
        try:
            value = json.loads(response.text)
        except json.JSONDecodeError as error:
            raise AIResponseError("Gemini returned invalid JSON.") from error
        if not isinstance(value, dict):
            raise AIResponseError("Gemini structured response was not an object.")
        return value

    def embed(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
        )
        if not response.embeddings:
            raise AIResponseError("Gemini returned no embedding.")
        return list(response.embeddings[0].values)