"""Port: estrategia de recuperación de contexto (patrón Strategy)."""
from abc import ABC, abstractmethod

from src.domain.entities import Chunk


class RetrievalStrategy(ABC):
    """Contrato para recuperar el contexto relevante a una query.

    Implementaciones intercambiables (infrastructure/retrieval): DenseRetrieval
    (top-K por similitud) y RerankRetrieval (recupera K' y reordena con
    Cross-Encoder). Se inyecta en AnswerQueryUseCase; cambiar de estrategia no
    toca el caso de uso.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        """Devolver los chunks más relevantes para la query."""
        ...
