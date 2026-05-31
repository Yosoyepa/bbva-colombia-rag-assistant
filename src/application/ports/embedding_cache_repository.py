"""Port: cache persistente de embeddings."""

from abc import ABC, abstractmethod


class EmbeddingCacheRepository(ABC):
    @abstractmethod
    def get_embedding(self, cache_key: str) -> list[float] | None:
        """Recuperar un embedding cacheado por clave estable."""
        ...

    @abstractmethod
    def set_embedding(
        self,
        cache_key: str,
        model_name: str,
        text_hash: str,
        embedding: list[float],
    ) -> None:
        """Persistir un embedding para reutilización."""
        ...
