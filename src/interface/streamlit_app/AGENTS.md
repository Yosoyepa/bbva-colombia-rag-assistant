# AGENTS.md — `src/interface/streamlit_app/`

UI Streamlit del sistema RAG. Ver [contexto de interface](../AGENTS.md).

## Responsabilidad

Presentar chat, conversaciones persistidas y analítica operacional consumiendo la API
FastAPI por HTTP. Esta carpeta no ejecuta casos de uso ni instancia adaptadores.

## Regla de dependencia

- Puede importar `streamlit`, `httpx` y helpers locales de esta carpeta.
- No importa `application`, `domain` ni `infrastructure`.
- El contrato público de datos viene de la API: `/health`, `/chat`, `/sessions`,
  `/sessions/{id}/messages` y `/analytics`.

## Organización

- `app.py` — entrypoint mínimo de Streamlit.
- `api_client.py` — cliente HTTP tipado de forma ligera.
- `state.py` — estado de sesión de Streamlit y helpers de presentación.
- `components.py` — render de sidebar, chat, trazas de retrieval y analítica.

## Para conservar

Si aparece lógica de negocio RAG aquí, debe moverse al backend. Streamlit solo coordina
interacción visual y serializa/deserializa payloads HTTP.
