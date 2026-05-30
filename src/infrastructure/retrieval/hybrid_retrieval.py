"""HybridRetrieval (Strategy) — combina BM25 PostgreSQL + similitud densa."""
from __future__ import annotations

from src.application.ports import Embedder, RetrievalStrategy, VectorKnowledgeRepository
from src.domain.entities import Chunk


class HybridRetrieval(RetrievalStrategy):
    def __init__(
        self,
        embedder: Embedder,
        repository: VectorKnowledgeRepository,
        dense_weight: float = 0.65,
        bm25_weight: float = 0.35,
    ) -> None:
        self._embedder = embedder
        self._repository = repository
        self._dense_weight = dense_weight
        self._bm25_weight = bm25_weight

    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        query_embedding = self._embedder.embed_text(query)
        return self._repository.search_hybrid(
            query_text=query,
            query_embedding=query_embedding,
            top_k=top_k,
            dense_weight=self._dense_weight,
            bm25_weight=self._bm25_weight,
        )
