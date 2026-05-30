"""Streamlit session-state helpers."""
from __future__ import annotations

import streamlit as st


def init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def reset_conversation() -> None:
    st.session_state.session_id = None
    st.session_state.messages = []


def set_conversation(session_id: str, messages: list[dict]) -> None:
    st.session_state.session_id = session_id
    st.session_state.messages = [
        {
            "role": item["role"],
            "content": item["content"],
            "sources": item.get("sources", []),
            "retrieval_trace": item.get("retrieval_trace", []),
        }
        for item in messages
        if item["role"] in {"user", "assistant"}
    ]


def append_message(
    role: str,
    content: str,
    sources: list[str] | None = None,
    retrieval_trace: list[dict] | None = None,
) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "sources": sources or [],
            "retrieval_trace": retrieval_trace or [],
        }
    )


def short_id(session_id: str | None) -> str:
    if not session_id:
        return "sin sesión"
    return session_id.split("-")[0]


def short_title(title: str, max_chars: int = 42) -> str:
    clean = " ".join(title.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"
