"""Embedder local (CPU) con sentence-transformers (adapta el port Embedder).

El modelo se carga una sola vez (es caro) y se reutiliza. Mismo embedder para
indexar (CU-01) y para la query (CU-02): mismo espacio vectorial.
"""

from __future__ import annotations

import structlog

from src.application.ports import Embedder

log = structlog.get_logger(__name__)


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str) -> None:
        # Import diferido: torch/sentence-transformers son pesados; solo al usarse.
        from sentence_transformers import SentenceTransformer

        log.info("loading_embedding_model", model=model_name)
        self._model = SentenceTransformer(model_name, device="cpu")
        self._dim = self._model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vecs = self._model.encode(
            texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
        )
        return [v.tolist() for v in vecs]

    @property
    def dimension(self) -> int:
        return self._dim
