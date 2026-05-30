"""UI de chat (Streamlit) que CONSUME la API FastAPI por HTTP.

No importa el motor RAG ni carga modelos: solo habla REST con la API. Mantiene el
session_id en el estado para conservar memoria conversacional (CU-03).
"""
from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _short_id(session_id: str | None) -> str:
    if not session_id:
        return "sin sesión"
    return session_id.split("-")[0]


def _short_title(title: str, max_chars: int = 42) -> str:
    clean = " ".join(title.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def _load_session(session_id: str) -> None:
    resp = httpx.get(f"{API_URL}/sessions/{session_id}/messages", timeout=10)
    resp.raise_for_status()
    st.session_state.session_id = session_id
    st.session_state.messages = [
        {
            "role": item["role"],
            "content": item["content"],
            "sources": item.get("sources", []),
        }
        for item in resp.json()
        if item["role"] in {"user", "assistant"}
    ]


def _load_analytics() -> dict:
    resp = httpx.get(f"{API_URL}/analytics", timeout=10)
    resp.raise_for_status()
    return resp.json()


st.set_page_config(page_title="Asistente BBVA", page_icon="💬")
st.title("💬 Asistente BBVA Colombia")
st.caption("RAG sobre información pública de bbva.com.co — respuestas ancladas a fuentes.")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Estado del backend.
with st.sidebar:
    st.subheader("Estado")
    try:
        h = httpx.get(f"{API_URL}/health", timeout=5).json()
        st.success(f"API ok · DB={h['db']} · proveedor={h['provider']}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"API no disponible: {exc}")
    if st.button("Nueva conversación"):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Conversaciones")
    st.caption(f"Actual: `{_short_id(st.session_state.session_id)}`")
    try:
        sessions = httpx.get(f"{API_URL}/sessions", params={"limit": 20}, timeout=10).json()
        if not sessions:
            st.caption("Aún no hay conversaciones guardadas.")
        for item in sessions:
            sid = item["session_id"]
            selected = sid == st.session_state.session_id
            label = f"{_short_title(item['title'])} ({item['message_count']})"
            if st.button(
                label,
                key=f"session-{sid}",
                type="primary" if selected else "secondary",
                use_container_width=True,
                help=sid,
            ):
                _load_session(sid)
                st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"No pude cargar conversaciones: {exc}")

chat_tab, analytics_tab = st.tabs(["Chat", "Analítica"])

with chat_tab:
    # Historial en pantalla.
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("sources"):
                st.caption("Fuentes: " + ", ".join(m["sources"]))

    # Entrada del usuario.
    if prompt := st.chat_input("Pregunta sobre BBVA…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                payload = {"message": prompt}
                if st.session_state.session_id:
                    payload["session_id"] = st.session_state.session_id
                resp = httpx.post(f"{API_URL}/chat", json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                st.session_state.session_id = data["session_id"]
                st.markdown(data["content"])
                if data.get("sources"):
                    st.caption("Fuentes: " + ", ".join(data["sources"]))
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": data["content"],
                        "sources": data.get("sources", []),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error consultando la API: {exc}")

with analytics_tab:
    st.subheader("Observabilidad del MVP")
    st.caption("Métricas calculadas desde el histórico persistido de conversaciones.")
    try:
        report = _load_analytics()
        col1, col2, col3 = st.columns(3)
        col1.metric("Sesiones", report["total_sessions"])
        col2.metric("Mensajes", report["total_messages"])
        col3.metric("Promedio por sesión", f"{report['avg_messages_per_session']:.2f}")

        st.subheader("Fuentes más citadas")
        top_sources = report.get("top_sources", [])
        if top_sources:
            st.dataframe(top_sources, use_container_width=True, hide_index=True)
            st.bar_chart(top_sources, x="source_url", y="citations")
        else:
            st.info("Aún no hay fuentes citadas por respuestas del asistente.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"No pude cargar la analítica: {exc}")
