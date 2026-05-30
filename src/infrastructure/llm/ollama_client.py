"""Cliente Ollama (LLM local, adapta el port LargeLanguageModel).

Habla con un servidor Ollama por HTTP (`/api/chat`). El system prompt va como
primer mensaje con rol `system`. Útil offline / sin claves de API. Import de
httpx diferido al uso.
"""
from __future__ import annotations

from collections.abc import Iterator

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class OllamaClient(LargeLanguageModel):
    def __init__(self, host: str, model: str, timeout: float = 120.0) -> None:
        if not host:
            raise ValueError("OLLAMA_HOST vacío: no se puede instanciar OllamaClient")
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout

    def _payload(self, system_prompt: str, messages: list[ChatMessage]) -> dict:
        role_map = {"user": "user", "assistant": "assistant", "system": "system"}
        msgs = [{"role": "system", "content": system_prompt}]
        msgs += [
            {"role": role_map.get(m.role, "user"), "content": m.content}
            for m in messages
        ]
        return {"model": self._model, "messages": msgs}

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        import httpx

        payload = {**self._payload(system_prompt, messages), "stream": False}
        resp = httpx.post(f"{self._host}/api/chat", json=payload, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        import json

        import httpx

        payload = {**self._payload(system_prompt, messages), "stream": True}
        with httpx.stream(
            "POST", f"{self._host}/api/chat", json=payload, timeout=self._timeout
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                piece = chunk.get("message", {}).get("content")
                if piece:
                    yield piece
