"""CU-01: ingesta — scrape → clean → chunk → embed → indexar.

Stub: la orquestación se completa en Fase 1. Define la forma del caso de uso y
sus dependencias (ports), inyectadas por el Composition Root.
"""
from dataclasses import dataclass

from src.application.ports import Embedder, VectorKnowledgeRepository
from src.domain.entities import Chunk


@dataclass
class IngestResult:
    """Resumen verificable de una corrida de ingesta (alimenta CU-01 spec)."""
    documents_scraped: int
    chunks_indexed: int


class IngestDataUseCase:
    def __init__(
        self,
        embedder: Embedder,
        knowledge_repo: VectorKnowledgeRepository,
    ) -> None:
        self._embedder = embedder
        self._knowledge_repo = knowledge_repo

    def execute(self, chunks: list[Chunk], documents_scraped: int = 0) -> IngestResult:
        """Embeber los chunks limpios (en lote) e indexarlos en el vector repo.

        El scraping + limpieza + chunking (infrastructure/scraping) producen los
        `Chunk`; aquí se calcula el embedding y se persiste (Store-and-Forward).
        """
        if chunks:
            vectors = self._embedder.embed_batch([c.content for c in chunks])
            for chunk, vector in zip(chunks, vectors, strict=True):
                chunk.embedding = vector
            self._knowledge_repo.add_chunks(chunks)
        return IngestResult(
            documents_scraped=documents_scraped,
            chunks_indexed=len(chunks),
        )
