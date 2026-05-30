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
from src.application.prompt_builder import PromptBuilder
from src.domain.entities import ChatMessage, Chunk


@dataclass
class Answer:
    """Respuesta anclada: texto + las fuentes (URLs) que la soportan."""
    session_id: UUID
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

    def execute(self, session_id: UUID | None, query: str) -> Answer:
        """Recuperar contexto + historial, construir prompt, generar respuesta anclada."""
        session = self._memory.get_or_create_session(session_id)

        # 1) Contexto relevante (Strategy: dense/rerank).
        context = self._retrieval.retrieve(query, self._top_k)
        sources = PromptBuilder.sources_of(context)

        # 2) Ventana de N mensajes previos (CU-03) + la pregunta actual.
        history = self._memory.get_recent_messages(session.id, self._n_history_messages)
        user_msg = ChatMessage(session_id=session.id, role="user", content=query)
        messages = history + [user_msg]

        if not context:
            content = (
                "No encontré información en el corpus indexado para responder esa pregunta "
                "con fuentes confiables."
            )
            self._memory.add_message(user_msg)
            self._memory.add_message(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=content,
                    sources=[],
                )
            )
            return Answer(session_id=session.id, content=content, sources=[], used_chunks=[])

        # 3) System prompt defensivo con el contexto embebido (Builder).
        system_prompt = PromptBuilder.build_system(context)

        # 4) Generar (Factory + fallback transparente).
        content = self._llm.generate(system_prompt, messages)

        # 5) Persistir el turno (memoria) y anclar fuentes.
        self._memory.add_message(user_msg)
        self._memory.add_message(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=content,
                sources=sources,
            )
        )
        return Answer(
            session_id=session.id,
            content=content,
            sources=sources,
            used_chunks=context,
        )
