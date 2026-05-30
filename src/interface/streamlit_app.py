"""UI de chat (Streamlit) que CONSUME la API FastAPI por HTTP.

No importa el motor RAG ni carga modelos: solo habla REST con la API. Mantiene el
session_id en el estado para conservar memoria conversacional (CU-03).
"""
from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

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
                {"role": "assistant", "content": data["content"], "sources": data.get("sources", [])}
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error consultando la API: {exc}")
