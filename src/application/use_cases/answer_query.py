"""CU-02: responder una query con RAG anclado a fuentes (+ memoria CU-03).

Stub: la orquestación se completa en Fase 1. Coordina retrieval (Strategy),
memoria (N mensajes) y el LLM (Factory + fallback). Regla de negocio: si el
contexto no soporta la respuesta, admitir "no lo sé" (anti-alucinación).
"""
from dataclasses import dataclass, field
from uuid import UUID

from src.application.ports import (
    ChatMemoryRepository,
    LargeLanguageModel,
    RetrievalStrategy,
)
from src.domain.entities import Chunk


@dataclass
class Answer:
    """Respuesta anclada: texto + las fuentes (URLs) que la soportan."""
    content: str
    sources: list[str] = field(default_factory=list)
    used_chunks: list[Chunk] = field(default_factory=list)


class AnswerQueryUseCase:
    def __init__(
        self,
        retrieval: RetrievalStrategy,
        llm: LargeLanguageModel,
        memory: ChatMemoryRepository,
        top_k: int,
        n_history_messages: int,
    ) -> None:
        self._retrieval = retrieval
        self._llm = llm
        self._memory = memory
        self._top_k = top_k
        self._n_history_messages = n_history_messages

    def execute(self, session_id: UUID, query: str) -> Answer:
        """Recuperar contexto + historial, construir prompt, generar respuesta.

        TODO(Fase 1): retrieve top-K → PromptBuilder(system + N msgs + contexto +
        query) → llm.generate → anclar fuentes → persistir mensajes en memoria.
        """
        raise NotImplementedError
