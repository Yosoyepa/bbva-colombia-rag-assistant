"""Cliente Google Gemini (adapta el port LargeLanguageModel).

Mapea el historial de ChatMessage al formato de Gemini (roles user/model) y pasa
el contexto como system_instruction. Proveedor por defecto del MVP.
"""
from __future__ import annotations

from collections.abc import Iterator

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class GeminiClient(LargeLanguageModel):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY vacío: no se puede instanciar GeminiClient")
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def _to_contents(self, messages: list[ChatMessage]) -> list[dict]:
        role_map = {"user": "user", "assistant": "model", "system": "user"}
        return [
            {"role": role_map.get(m.role, "user"), "parts": [m.content]}
            for m in messages
        ]

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        model = self._genai.GenerativeModel(
            self._model_name, system_instruction=system_prompt
        )
        response = model.generate_content(self._to_contents(messages))
        return response.text

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        model = self._genai.GenerativeModel(
            self._model_name, system_instruction=system_prompt
        )
        for event in model.generate_content(self._to_contents(messages), stream=True):
            if getattr(event, "text", None):
                yield event.text
