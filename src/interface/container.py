"""Composition Root — construye e inyecta las dependencias desde Settings.

Única capa que conoce a la vez application e infrastructure. El embedder (modelo
CPU) y el pool se crean una sola vez; el LLM se construye perezosamente (permite
arrancar la API y /health aunque aún no haya GOOGLE_API_KEY configurada).
"""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

import structlog

from src.application.use_cases import AnalyticsUseCase, AnswerQueryUseCase, IngestDataUseCase
from src.interface.config import Settings, get_settings

log = structlog.get_logger(__name__)


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        from src.infrastructure.persistence import create_pool

        self.pool = create_pool(self.settings.pg_dsn)
        self._embedder = None
        self._knowledge_repo = None
        self._memory_repo = None
        self._embedding_cache_repo = None
        self._answer_cache_repo = None
        self._retrieval = None
        self._llm = None
        self._lock = RLock()

    @property
    def embedder(self):
        def factory():
            from src.infrastructure.embeddings import CachedEmbedder, SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(self.settings.embedding_model)
            if self.settings.embedding_cache_enabled:
                embedder = CachedEmbedder(
                    embedder,
                    self.embedding_cache_repo,
                    model_name=self.settings.embedding_model,
                )
            return embedder

        return self._singleton("_embedder", factory)

    @property
    def knowledge_repo(self):
        def factory():
            from src.infrastructure.persistence import PgVectorKnowledgeRepository

            return PgVectorKnowledgeRepository(self.pool)

        return self._singleton("_knowledge_repo", factory)

    @property
    def memory_repo(self):
        def factory():
            from src.infrastructure.persistence import PgChatMemoryRepository

            return PgChatMemoryRepository(self.pool)

        return self._singleton("_memory_repo", factory)

    @property
    def embedding_cache_repo(self):
        def factory():
            from src.infrastructure.persistence import PgEmbeddingCacheRepository

            return PgEmbeddingCacheRepository(self.pool)

        return self._singleton("_embedding_cache_repo", factory)

    @property
    def answer_cache_repo(self):
        def factory():
            from src.infrastructure.persistence import PgAnswerCacheRepository

            return PgAnswerCacheRepository(self.pool)

        return self._singleton("_answer_cache_repo", factory)

    @property
    def retrieval(self):
        def factory():
            from src.infrastructure.retrieval import (
                DenseRetrieval,
                HybridRetrieval,
                RerankRetrieval,
            )

            if self.settings.retrieval_mode.lower() == "hybrid":
                base_retrieval = HybridRetrieval(
                    self.embedder,
                    self.knowledge_repo,
                    dense_weight=self.settings.hybrid_dense_weight,
                    bm25_weight=self.settings.hybrid_bm25_weight,
                )
            else:
                base_retrieval = DenseRetrieval(self.embedder, self.knowledge_repo)

            if self.settings.rerank_enabled:
                return RerankRetrieval(
                    self.embedder,
                    self.knowledge_repo,
                    model_name=self.settings.rerank_model,
                    base_retrieval=base_retrieval,
                )
            return base_retrieval

        return self._singleton("_retrieval", factory)

    @property
    def llm(self):
        """LLM construido bajo demanda: cadena de fallback (activo + respaldos) con
        Circuit Breaker por proveedor. Falla claro si ninguno tiene credenciales."""

        def factory():
            from src.infrastructure.llm import LLMFactory

            s = self.settings
            return LLMFactory.create_with_fallback(
                active_provider=s.model_provider,
                fallback_order=s.fallback_order,
                model=s.llm_model,
                google_model=s.google_model,
                anthropic_model=s.anthropic_model,
                ollama_model=s.ollama_model,
                google_api_key=s.google_api_key,
                anthropic_api_key=s.anthropic_api_key,
                aws_access_key_id=s.aws_access_key_id,
                aws_secret_access_key=s.aws_secret_access_key,
                aws_region=s.aws_region,
                bedrock_model_id=s.bedrock_model_id,
                ollama_host=s.ollama_host,
            )

        return self._singleton("_llm", factory)

    def answer_use_case(self) -> AnswerQueryUseCase:
        return AnswerQueryUseCase(
            retrieval=self.retrieval,
            llm=self.llm,
            memory=self.memory_repo,
            top_k=self.settings.top_k,
            n_history_messages=self.settings.n_history_messages,
            answer_cache=self.answer_cache_repo,
            answer_cache_enabled=self.settings.answer_cache_enabled,
            answer_cache_ttl_seconds=self.settings.answer_cache_ttl_seconds,
            cache_namespace=(
                f"{self.settings.llm_model}:"
                f"{self.settings.retrieval_mode}:"
                f"{self.knowledge_repo.corpus_version()}"
            ),
        )

    def ingest_use_case(self) -> IngestDataUseCase:
        return IngestDataUseCase(
            embedder=self.embedder,
            knowledge_repo=self.knowledge_repo,
        )

    def analytics_use_case(self) -> AnalyticsUseCase:
        return AnalyticsUseCase(memory=self.memory_repo)

    def db_healthy(self) -> bool:
        try:
            with self.pool.connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        except Exception as exc:  # noqa: BLE001
            log.warning("db_health_failed", error=str(exc))
            return False

    def close(self) -> None:
        self.pool.close()

    def _singleton(self, attr: str, factory: Callable[[], object]):
        instance = getattr(self, attr)
        if instance is not None:
            return instance
        with self._lock:
            instance = getattr(self, attr)
            if instance is None:
                instance = factory()
                setattr(self, attr, instance)
            return instance
