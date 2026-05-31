# Retrieval, reranking y cache

## Flujo de consulta

```text
pregunta
  -> embedding de query
  -> retrieval top-K
  -> rerank opcional
  -> PromptBuilder
  -> LLM
  -> respuesta con fuentes
```

Si no hay contexto suficiente, el caso de uso responde que no encontro informacion
confiable en el corpus.

## Modelos locales

La recuperacion usa modelos locales en CPU:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` para embeddings.
- Dimension `384`, alineada con `VECTOR(384)`.
- Embeddings normalizados para distancia coseno.
- `cross-encoder/ms-marco-MiniLM-L-6-v2` como reranker opcional.

La generacion queda en proveedores LLM configurables porque requiere mayor calidad
conversacional.

## Estrategias

| Estrategia | Configuracion | Descripcion |
|---|---|---|
| Densa | `RETRIEVAL_MODE=dense` | Embedding de query + pgvector. |
| Hibrida | `RETRIEVAL_MODE=hybrid` | Combina pgvector con full-text/BM25 PostgreSQL. |
| Rerank | `RERANK_ENABLED=true` | Cross-Encoder reordena candidatos densos o hibridos. |

Con `RETRIEVAL_MODE=hybrid` y `RERANK_ENABLED=true`, la traza conserva
`dense_score`, `bm25_score`, `hybrid_score` y agrega `rerank_score`.

## Cache

- `embedding_cache`: cache persistente por hash de texto/modelo.
- `answer_cache`: cache opt-in por pregunta normalizada, top-K, modelo y version de corpus.

La cache de embeddings esta pensada para ahorrar CPU. La cache de respuestas queda apagada
por defecto para no ocultar cambios durante evaluacion.

Variables:

- `EMBEDDING_CACHE_ENABLED`
- `ANSWER_CACHE_ENABLED`
- `ANSWER_CACHE_TTL_SECONDS`
