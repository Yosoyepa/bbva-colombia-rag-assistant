"""Cliente Anthropic Claude (adapta el port LargeLanguageModel).

Mapea ChatMessage al formato Messages API (roles user/assistant) y pasa el
contexto recuperado como `system`. Import diferido para no exigir el SDK salvo
que este proveedor se use de verdad.
"""

from __future__ import annotations

from collections.abc import Iterator

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class AnthropicClient(LargeLanguageModel):
    def __init__(self, api_key: str, model: str, max_tokens: int = 1024) -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY vacío: no se puede instanciar AnthropicClient")
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def _to_messages(self, messages: list[ChatMessage]) -> list[dict]:
        # Claude solo acepta user/assistant en `messages`; system va aparte.
        role_map = {"user": "user", "assistant": "assistant", "system": "user"}
        return [{"role": role_map.get(m.role, "user"), "content": m.content} for m in messages]

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=self._to_messages(messages),
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=self._to_messages(messages),
        ) as stream:
            for text in stream.text_stream:
                yield text
