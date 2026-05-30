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

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[Chunk]:
        """Devolver los `top_k` chunks más similares al embedding de la query."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Número de chunks indexados (útil para verificación de ingesta)."""
        ...
