# AGENTS.md — `src/infrastructure/retrieval/`

Estrategias de recuperación. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Implementar `RetrievalStrategy`: dada una query, devolver el contexto más relevante.

- `DenseRetrieval` — embeber query → top-K por similitud en pgvector (camino base del MVP).
- `RerankRetrieval` (bonus) — recupera K' candidatos y los reordena con un **Cross-Encoder**;
  activable por `RERANK_ENABLED`.

## Regla de dependencia

- Implementa `application.ports.RetrievalStrategy`. Usa el `VectorKnowledgeRepository` y el
  `Embedder` (inyectados). El Cross-Encoder vive aquí, no en el núcleo.

## Patrones / decisiones

- **Strategy**: `AnswerQueryUseCase` recibe la estrategia por inyección; cambiar de dense a
  rerank no toca el caso de uso.
- **Null Object** (`NullReranker`) como opción natural cuando `RERANK_ENABLED=false`.
- `TOP_K` es config; el reranker corre en CPU (entorno sin GPU) → mantener K' acotado.

## Para conservar

Añadir una estrategia nueva (p. ej. híbrida BM25+denso) = nueva clase que implementa el port,
sin tocar `application`.
