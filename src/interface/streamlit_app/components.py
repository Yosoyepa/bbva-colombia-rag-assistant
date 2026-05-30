"""Streamlit visual components."""
from __future__ import annotations

import streamlit as st

from src.interface.streamlit_app.api_client import ApiClient
from src.interface.streamlit_app.state import (
    append_message,
    reset_conversation,
    set_conversation,
    short_id,
    short_title,
)


def render_sidebar(client: ApiClient) -> None:
    with st.sidebar:
        st.subheader("Estado")
        try:
            health = client.health()
            st.success(
                f"API ok · DB={health['db']} · proveedor={health['provider']}"
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"API no disponible: {exc}")

        if st.button("Nueva conversación", width="stretch"):
            reset_conversation()
            st.rerun()

        st.divider()
        st.subheader("Conversaciones")
        st.caption(f"Actual: `{short_id(st.session_state.session_id)}`")
        try:
            sessions = client.list_sessions(limit=20)
            if not sessions:
                st.caption("Aún no hay conversaciones guardadas.")
            for item in sessions:
                _render_session_button(client, item)
        except Exception as exc:  # noqa: BLE001
            st.warning(f"No pude cargar conversaciones: {exc}")


def render_chat_tab(client: ApiClient) -> None:
    for message in st.session_state.messages:
        _render_message(message)

    if prompt := st.chat_input("Pregunta sobre BBVA…"):
        append_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                data = client.chat(prompt, st.session_state.session_id)
                st.session_state.session_id = data["session_id"]
                st.markdown(data["content"])
                _render_sources(data.get("sources", []))
                _render_retrieval_trace(data.get("retrieval_trace", []))
                append_message(
                    "assistant",
                    data["content"],
                    sources=data.get("sources", []),
                    retrieval_trace=data.get("retrieval_trace", []),
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error consultando la API: {exc}")


def render_analytics_tab(client: ApiClient) -> None:
    st.subheader("Observabilidad del MVP")
    st.caption("Métricas calculadas desde el histórico persistido de conversaciones.")
    try:
        report = client.analytics()
        col1, col2, col3 = st.columns(3)
        col1.metric("Sesiones", report["total_sessions"])
        col2.metric("Mensajes", report["total_messages"])
        col3.metric("Promedio por sesión", f"{report['avg_messages_per_session']:.2f}")

        st.subheader("Fuentes más citadas")
        top_sources = report.get("top_sources", [])
        if top_sources:
            st.dataframe(top_sources, width="stretch", hide_index=True)
            st.bar_chart(top_sources, x="source_url", y="citations")
        else:
            st.info("Aún no hay fuentes citadas por respuestas del asistente.")

        _render_recent_sessions(client)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No pude cargar la analítica: {exc}")


def _render_session_button(client: ApiClient, item: dict) -> None:
    session_id = item["session_id"]
    selected = session_id == st.session_state.session_id
    label = f"{short_title(item['title'])} ({item['message_count']})"
    if st.button(
        label,
        key=f"session-{session_id}",
        type="primary" if selected else "secondary",
        width="stretch",
        help=session_id,
    ):
        set_conversation(session_id, client.load_messages(session_id))
        st.rerun()


def _render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _render_sources(message.get("sources", []))
        _render_retrieval_trace(message.get("retrieval_trace", []))


def _render_sources(sources: list[str]) -> None:
    if sources:
        st.caption("Fuentes: " + ", ".join(sources))


def _render_retrieval_trace(trace: list[dict]) -> None:
    if not trace:
        return

    with st.expander("Trazabilidad de retrieval", expanded=False):
        table = [
            {
                "rank": item.get("rank"),
                "source_url": item.get("source_url"),
                "similarity_score": _round_or_none(item.get("similarity_score")),
                "distance": _round_or_none(item.get("distance")),
                "rerank_score": _round_or_none(item.get("rerank_score")),
            }
            for item in trace
        ]
        st.dataframe(table, width="stretch", hide_index=True)
        for item in trace:
            st.markdown(f"**#{item.get('rank')} · {item.get('source_url')}**")
            st.caption(item.get("content_preview", ""))


def _render_recent_sessions(client: ApiClient) -> None:
    st.subheader("Conversaciones recientes")
    sessions = client.list_sessions(limit=10)
    if not sessions:
        st.info("Aún no hay conversaciones registradas.")
        return
    st.dataframe(
        [
            {
                "session_id": short_id(item["session_id"]),
                "mensajes": item["message_count"],
                "actualizada": item.get("updated_at") or item.get("created_at"),
                "título": item["title"],
            }
            for item in sessions
        ],
        width="stretch",
        hide_index=True,
    )


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)
