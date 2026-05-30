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

    def execute(self, chunks: list[Chunk]) -> IngestResult:
        """Embeber los chunks limpios e indexarlos en el vector repo.

        El scraping + limpieza + chunking (infrastructure/scraping) producen los
        `Chunk`; aquí se calcula el embedding y se persiste. TODO(Fase 1).
        """
        raise NotImplementedError
