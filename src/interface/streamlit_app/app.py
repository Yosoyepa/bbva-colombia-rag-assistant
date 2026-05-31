"""Streamlit entrypoint for the BBVA RAG assistant."""

from __future__ import annotations

import os

import streamlit as st

from src.interface.streamlit_app.api_client import ApiClient
from src.interface.streamlit_app.components import (
    render_analytics_tab,
    render_chat_tab,
    render_sidebar,
)
from src.interface.streamlit_app.state import init_state


def main() -> None:
    api_url = os.getenv("API_URL", "http://localhost:8000")
    client = ApiClient(api_url)

    st.set_page_config(page_title="Asistente BBVA", page_icon="💬")
    init_state()

    st.title("💬 Asistente BBVA Colombia")
    st.caption("RAG sobre información pública de bbva.com.co — respuestas ancladas a fuentes.")

    render_sidebar(client)

    chat_tab, analytics_tab = st.tabs(["Chat", "Analítica"])
    with chat_tab:
        render_chat_tab(client)
    with analytics_tab:
        render_analytics_tab(client)


if __name__ == "__main__":
    main()
