# Observabilidad y analitica

## Trazabilidad de retrieval

`POST /chat` devuelve `retrieval_trace`, una lista de chunks usados para construir la
respuesta.

Campos principales:

- `rank`
- `source_url`
- `distance`
- `similarity_score`
- `rerank_score`
- `dense_score`
- `bm25_score`
- `hybrid_score`
- `content_preview`

Streamlit muestra esta traza en un panel desplegable por respuesta para auditar si el
sistema uso evidencia real del indice.

## Latencias

`POST /chat` incluye `observability`:

- `total_latency_ms`
- `retrieval_latency_ms`
- `prompt_latency_ms`
- `llm_latency_ms`
- `persistence_latency_ms`
- `provider`
- `cache_hit`

Se eligio observabilidad embebida y logs estructurados porque son suficientes para el MVP
sin sumar Prometheus, OpenTelemetry ni infraestructura adicional.

## Analitica historica

La analitica se calcula desde `chat_sessions` y `chat_messages`, incluyendo fuentes citadas
por respuestas del asistente.

Disponible en:

- Streamlit, pestaña **Analitica**.
- `GET /analytics`.
- CLI `bbva-analytics`.

Metricas:

- total de sesiones,
- total de mensajes,
- promedio de mensajes por sesion,
- fuentes mas citadas,
- conversaciones recientes.
