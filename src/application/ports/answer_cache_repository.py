"""Port: cache persistente de respuestas conversacionales."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.domain.entities import Chunk


@dataclass
class CachedAnswer:
    content: str
    sources: list[str] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)


class AnswerCacheRepository(ABC):
    @abstractmethod
    def get_answer(self, cache_key: str, ttl_seconds: int) -> CachedAnswer | None:
        """Recuperar una respuesta cacheada si existe y no expiró."""
        ...

    @abstractmethod
    def set_answer(self, cache_key: str, answer: CachedAnswer) -> None:
        """Persistir una respuesta generada para reutilización opt-in."""
        ...
