"""CU-02: responder una query con RAG anclado a fuentes (+ memoria CU-03)."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from uuid import UUID

from src.application.ports import (
    AnswerCacheRepository,
    CachedAnswer,
    ChatMemoryRepository,
    LargeLanguageModel,
    RetrievalStrategy,
)
from src.application.prompt_builder import PromptBuilder
from src.domain.entities import ChatMessage, Chunk


@dataclass
class AnswerObservability:
    total_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    prompt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    persistence_latency_ms: float = 0.0
    provider: str | None = None
    cache_hit: bool = False


@dataclass
class Answer:
    """Respuesta anclada: texto + fuentes + trazabilidad."""

    session_id: UUID
    content: str
    sources: list[str] = field(default_factory=list)
    used_chunks: list[Chunk] = field(default_factory=list)
    observability: AnswerObservability = field(default_factory=AnswerObservability)


class AnswerQueryUseCase:
    def __init__(
        self,
        retrieval: RetrievalStrategy,
        llm: LargeLanguageModel,
        memory: ChatMemoryRepository,
        top_k: int,
        n_history_messages: int,
        answer_cache: AnswerCacheRepository | None = None,
        answer_cache_enabled: bool = False,
        answer_cache_ttl_seconds: int = 3600,
        cache_namespace: str = "",
    ) -> None:
        self._retrieval = retrieval
        self._llm = llm
        self._memory = memory
        self._top_k = top_k
        self._n_history_messages = n_history_messages
        self._answer_cache = answer_cache
        self._answer_cache_enabled = answer_cache_enabled
        self._answer_cache_ttl_seconds = answer_cache_ttl_seconds
        self._cache_namespace = cache_namespace

    def execute(self, session_id: UUID | None, query: str) -> Answer:
        """Recuperar contexto + historial, construir prompt, generar respuesta anclada."""
        started = time.monotonic()
        observability = AnswerObservability()
        session = self._memory.get_or_create_session(session_id)
        cache_key = self._cache_key(query)

        cached = self._get_cached_answer(cache_key)
        if cached:
            user_msg = ChatMessage(session_id=session.id, role="user", content=query)
            persist_started = time.monotonic()
            self._memory.add_message(user_msg)
            self._memory.add_message(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=cached.content,
                    sources=cached.sources,
                )
            )
            observability.cache_hit = True
            observability.provider = "answer_cache"
            observability.persistence_latency_ms = self._elapsed_ms(persist_started)
            observability.total_latency_ms = self._elapsed_ms(started)
            return Answer(
                session_id=session.id,
                content=cached.content,
                sources=cached.sources,
                used_chunks=cached.chunks,
                observability=observability,
            )

        retrieval_started = time.monotonic()
        context = self._retrieval.retrieve(query, self._top_k)
        observability.retrieval_latency_ms = self._elapsed_ms(retrieval_started)
        sources = PromptBuilder.sources_of(context)

        history = self._memory.get_recent_messages(session.id, self._n_history_messages)
        user_msg = ChatMessage(session_id=session.id, role="user", content=query)
        messages = history + [user_msg]

        if not context:
            content = (
                "No encontré información en el corpus indexado para responder esa pregunta "
                "con fuentes confiables."
            )
            persist_started = time.monotonic()
            self._memory.add_message(user_msg)
            self._memory.add_message(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=content,
                    sources=[],
                )
            )
            observability.persistence_latency_ms = self._elapsed_ms(persist_started)
            observability.total_latency_ms = self._elapsed_ms(started)
            return Answer(
                session_id=session.id,
                content=content,
                sources=[],
                used_chunks=[],
                observability=observability,
            )

        prompt_started = time.monotonic()
        system_prompt = PromptBuilder.build_system(context)
        observability.prompt_latency_ms = self._elapsed_ms(prompt_started)

        llm_started = time.monotonic()
        content = self._llm.generate(system_prompt, messages)
        observability.llm_latency_ms = self._elapsed_ms(llm_started)
        observability.provider = getattr(self._llm, "last_provider", None) or getattr(
            self._llm, "name", self._llm.__class__.__name__
        )

        persist_started = time.monotonic()
        self._memory.add_message(user_msg)
        self._memory.add_message(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=content,
                sources=sources,
            )
        )
        observability.persistence_latency_ms = self._elapsed_ms(persist_started)
        self._set_cached_answer(cache_key, content, sources, context)
        observability.total_latency_ms = self._elapsed_ms(started)
        return Answer(
            session_id=session.id,
            content=content,
            sources=sources,
            used_chunks=context,
            observability=observability,
        )

    def _cache_key(self, query: str) -> str:
        normalized = " ".join(query.lower().split())
        raw = f"{self._cache_namespace}:{self._top_k}:{normalized}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_cached_answer(self, cache_key: str) -> CachedAnswer | None:
        if not self._answer_cache_enabled or self._answer_cache is None:
            return None
        return self._answer_cache.get_answer(cache_key, self._answer_cache_ttl_seconds)

    def _set_cached_answer(
        self,
        cache_key: str,
        content: str,
        sources: list[str],
        chunks: list[Chunk],
    ) -> None:
        if not self._answer_cache_enabled or self._answer_cache is None:
            return
        self._answer_cache.set_answer(
            cache_key,
            CachedAnswer(content=content, sources=sources, chunks=chunks),
        )

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.monotonic() - started) * 1000, 3)
