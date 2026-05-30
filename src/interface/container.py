"""Composition Root — construye e inyecta las dependencias desde Settings.

Única capa que conoce a la vez application e infrastructure. El embedder (modelo
CPU) y el pool se crean una sola vez; el LLM se construye perezosamente (permite
arrancar la API y /health aunque aún no haya GOOGLE_API_KEY configurada).
"""
from __future__ import annotations

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
        self._cache_repo = None
        self._retrieval = None
        self._llm = None

    @property
    def embedder(self):
        if self._embedder is None:
            from src.infrastructure.embeddings import CachedEmbedder, SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(self.settings.embedding_model)
            if self.settings.embedding_cache_enabled:
                embedder = CachedEmbedder(
                    embedder,
                    self.cache_repo,
                    model_name=self.settings.embedding_model,
                )
            self._embedder = embedder
        return self._embedder

    @property
    def knowledge_repo(self):
        if self._knowledge_repo is None:
            from src.infrastructure.persistence import PgVectorKnowledgeRepository

            self._knowledge_repo = PgVectorKnowledgeRepository(self.pool)
        return self._knowledge_repo

    @property
    def memory_repo(self):
        if self._memory_repo is None:
            from src.infrastructure.persistence import PgChatMemoryRepository

            self._memory_repo = PgChatMemoryRepository(self.pool)
        return self._memory_repo

    @property
    def cache_repo(self):
        if self._cache_repo is None:
            from src.infrastructure.persistence import PgCacheRepository

            self._cache_repo = PgCacheRepository(self.pool)
        return self._cache_repo

    @property
    def retrieval(self):
        if self._retrieval is None:
            from src.infrastructure.retrieval import DenseRetrieval, HybridRetrieval, RerankRetrieval

            if self.settings.rerank_enabled:
                self._retrieval = RerankRetrieval(
                    self.embedder,
                    self.knowledge_repo,
                    model_name=self.settings.rerank_model,
                )
            elif self.settings.retrieval_mode.lower() == "hybrid":
                self._retrieval = HybridRetrieval(
                    self.embedder,
                    self.knowledge_repo,
                    dense_weight=self.settings.hybrid_dense_weight,
                    bm25_weight=self.settings.hybrid_bm25_weight,
                )
            else:
                self._retrieval = DenseRetrieval(self.embedder, self.knowledge_repo)
        return self._retrieval

    @property
    def llm(self):
        """LLM construido bajo demanda: cadena de fallback (activo + respaldos) con
        Circuit Breaker por proveedor. Falla claro si ninguno tiene credenciales."""
        if self._llm is None:
            from src.infrastructure.llm import LLMFactory

            s = self.settings
            self._llm = LLMFactory.create_with_fallback(
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
        return self._llm

    def answer_use_case(self) -> AnswerQueryUseCase:
        return AnswerQueryUseCase(
            retrieval=self.retrieval,
            llm=self.llm,
            memory=self.memory_repo,
            top_k=self.settings.top_k,
            n_history_messages=self.settings.n_history_messages,
            answer_cache=self.cache_repo,
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
