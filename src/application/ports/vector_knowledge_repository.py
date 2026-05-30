"""Port: persistencia y búsqueda vectorial del conocimiento (chunks)."""
from abc import ABC, abstractmethod

from src.domain.entities import Chunk


class VectorKnowledgeRepository(ABC):
    """Contrato para almacenar chunks vectorizados y recuperarlos por similitud.

    La implementación concreta (pgvector) vive en infrastructure/persistence.
    El núcleo solo conoce esta interfaz.
    """

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Persistir una colección de chunks (con su embedding ya calculado)."""
        ...

    def replace_chunks(self, chunks: list[Chunk], source_urls: list[str]) -> None:
        """Reemplazar los chunks existentes de un conjunto de URLs."""
        for source_url in source_urls:
            self.delete_by_source(source_url)
        self.add_chunks(chunks)

    def delete_by_source(self, source_url: str) -> None:
        """Eliminar chunks indexados para una URL concreta."""

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[Chunk]:
        """Devolver los `top_k` chunks más similares al embedding de la query."""
        ...

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: list[float],
        top_k: int,
        dense_weight: float,
        bm25_weight: float,
    ) -> list[Chunk]:
        """Devolver chunks combinando similitud densa y búsqueda textual."""
        return self.search(query_embedding, top_k)

    def corpus_version(self) -> str:
        """Huella ligera del corpus para invalidar caches de respuesta."""
        return "unknown"

    @abstractmethod
    def count(self) -> int:
        """Número de chunks indexados (útil para verificación de ingesta)."""
        ...
