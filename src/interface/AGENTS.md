# AGENTS.md — `src/interface/`

Puntos de entrada y **Composition Root**. Ver [contexto global](../../AGENTS.md).

## Responsabilidad

Exponer el sistema al exterior y **ensamblar** las dependencias:

- `api/` — FastAPI: expone el motor RAG por REST (`/chat`, `/sessions`, `/health`, `/analytics`).
- `streamlit_app.py` — UI de chat con streaming que **consume la API** (no llama al motor directo).
- `cli.py` — entrypoint de ingesta (`bbva-ingest`).
- `analytics.py` — reporte de métricas del histórico (`bbva-analytics`, CU-04).

## Regla de dependencia

- Es la **única** capa que conoce a la vez `application` e `infrastructure`: aquí se leen
  los settings (pydantic-settings ← `.env`), se construyen los adaptadores y se inyectan en
  los casos de uso (**Composition Root**).
- No contiene lógica de negocio: traduce HTTP/CLI ↔ casos de uso y serializa resultados (DTO).

## Patrones / decisiones

- **DTO** (modelos Pydantic) en los bordes HTTP; se mapean a/desde entidades del dominio.
- **Decisión de arquitectura**: Streamlit consume FastAPI vía HTTP. Esto desacopla UI de motor
  y deja la costura para escalar a servicios en el futuro sin reescribir la UI.
- **Singletons** (pool de DB, modelo de embeddings, Factory LLM) se crean una vez al arrancar y se inyectan.

## Para conservar

Si te ves escribiendo lógica de "cómo responde el bot" aquí, va en `application/use_cases/`.
La interface solo orquesta entrada/salida.
