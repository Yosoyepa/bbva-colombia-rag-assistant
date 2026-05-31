"""Port: vectorización de texto (embeddings)."""

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Contrato para convertir texto en vectores.

    El mismo Embedder se usa para indexar chunks (CU-01) y para embeber la
    query (CU-02), garantizando el mismo espacio vectorial. Implementación
    concreta (sentence-transformers, CPU) en infrastructure/embeddings.
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Vector de un único texto."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Vectores de un lote de textos (acelera la ingesta)."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión del vector; debe coincidir con VECTOR(N) en la DB."""
        ...
