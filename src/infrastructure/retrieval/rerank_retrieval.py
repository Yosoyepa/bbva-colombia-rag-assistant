"""RerankRetrieval (Strategy) con Cross-Encoder en CPU.

Recupera más candidatos desde una estrategia base y luego reordena con un
Cross-Encoder. Si no se inyecta estrategia base, usa el camino denso histórico
para mantener compatibilidad.
"""

from __future__ import annotations

from src.application.ports import Embedder, RetrievalStrategy, VectorKnowledgeRepository
from src.domain.entities import Chunk


class RerankRetrieval(RetrievalStrategy):
    def __init__(
        self,
        embedder: Embedder,
        repository: VectorKnowledgeRepository,
        model_name: str,
        candidate_multiplier: int = 4,
        cross_encoder=None,
        base_retrieval: RetrievalStrategy | None = None,
    ) -> None:
        self._embedder = embedder
        self._repository = repository
        self._model_name = model_name
        self._candidate_multiplier = max(candidate_multiplier, 1)
        self._cross_encoder = cross_encoder
        self._base_retrieval = base_retrieval

    @property
    def cross_encoder(self):
        if self._cross_encoder is None:
            from sentence_transformers import CrossEncoder

            self._cross_encoder = CrossEncoder(self._model_name)
        return self._cross_encoder

    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        candidate_k = max(top_k * self._candidate_multiplier, top_k)
        if self._base_retrieval is None:
            query_embedding = self._embedder.embed_text(query)
            candidates = self._repository.search(query_embedding, candidate_k)
        else:
            candidates = self._base_retrieval.retrieve(query, candidate_k)
        if not candidates:
            return []

        pairs = [(query, chunk.content) for chunk in candidates]
        scores = list(self.cross_encoder.predict(pairs))
        ranked = sorted(
            zip(candidates, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        result = []
        for rank, (chunk, score) in enumerate(ranked[:top_k], start=1):
            chunk.rank = rank
            chunk.rerank_score = float(score)
            result.append(chunk)
        return result
