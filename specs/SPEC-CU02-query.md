# SPEC-CU02 — Consulta conversacional (RAG anclado)

**Traza a:** `prueba_tecnica_IAML.md` líneas 12, 18 (interfaz conversacional sobre el contenido) + bonus reranker (44).
**Capas:** `interface/api` → `application/use_cases/AnswerQueryUseCase` → `infrastructure/retrieval` + `infrastructure/llm`.

## Objetivo
Responder una pregunta del usuario usando solo el contenido indexado, anclando la respuesta
a sus fuentes y admitiendo desconocimiento cuando el contexto no la soporta.

## Actor
Usuario del chat (vía Streamlit → FastAPI `POST /chat`).

## Precondiciones
- CU-01 ejecutado (hay chunks indexados).
- `.env` con `MODEL_PROVIDER` + clave del proveedor, `LLM_MODEL`, `TOP_K`, `RERANK_ENABLED`.

## Flujo principal
1. Se recibe `{session_id, message}`.
2. `RetrievalStrategy.retrieve(query, TOP_K)` devuelve los chunks relevantes
   (Dense; si `RERANK_ENABLED`, Cross-Encoder reordena).
3. `PromptBuilder` arma: system defensivo + ventana de N mensajes (CU-03) + contexto + query.
4. `LargeLanguageModel.generate` produce la respuesta (con fallback transparente entre proveedores).
5. Se devuelve `Answer{content, sources}` y se persisten los mensajes (CU-03).

## Criterios de aceptación
- [ ] Pregunta cuya respuesta está en el sitio → respuesta correcta **con fuente(s)** citada(s).
- [ ] Pregunta fuera del corpus → el asistente **admite que no sabe** (no alucina).
- [ ] `sources` contiene URLs reales de chunks recuperados.
- [ ] Cambiar `MODEL_PROVIDER` cambia el backend sin tocar código.
- [ ] Con `RERANK_ENABLED=true` el orden de los chunks puede diferir del dense puro.
- [ ] `POST /chat` responde 200 con `{content, sources}`; soporta streaming.

## Casos borde
- Todos los proveedores caen → Circuit Breaker abre → error claro (HTTP 502), no cuelga.
- Retrieval vacío → respuesta de "no encontré información", nunca inventada.
