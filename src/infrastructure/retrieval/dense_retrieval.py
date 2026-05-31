"""DenseRetrieval (patrón Strategy) — recuperación densa por similitud.

Embebe la query con el mismo Embedder de la ingesta y busca top-K en pgvector.
Camino base del MVP. RerankRetrieval (bonus) se añade en Fase 3 sin tocar el caso de uso.
"""

from __future__ import annotations

from src.application.ports import Embedder, RetrievalStrategy, VectorKnowledgeRepository
from src.domain.entities import Chunk


class DenseRetrieval(RetrievalStrategy):
    def __init__(self, embedder: Embedder, repository: VectorKnowledgeRepository) -> None:
        self._embedder = embedder
        self._repository = repository

    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        query_embedding = self._embedder.embed_text(query)
        return self._repository.search(query_embedding, top_k)
