"""HTTP client used by Streamlit.

The UI intentionally talks to FastAPI instead of importing the RAG engine. This keeps
Streamlit as a replaceable interface adapter.
"""

from __future__ import annotations

from uuid import UUID

import httpx


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def health(self) -> dict:
        response = httpx.get(f"{self._base_url}/health", timeout=5)
        response.raise_for_status()
        return response.json()

    def list_sessions(self, limit: int = 20) -> list[dict]:
        response = httpx.get(
            f"{self._base_url}/sessions",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def load_messages(self, session_id: str | UUID) -> list[dict]:
        response = httpx.get(
            f"{self._base_url}/sessions/{session_id}/messages",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def chat(self, message: str, session_id: str | UUID | None) -> dict:
        payload = {"message": message}
        if session_id:
            payload["session_id"] = str(session_id)
        response = httpx.post(f"{self._base_url}/chat", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def analytics(self) -> dict:
        response = httpx.get(f"{self._base_url}/analytics", timeout=10)
        response.raise_for_status()
        return response.json()
