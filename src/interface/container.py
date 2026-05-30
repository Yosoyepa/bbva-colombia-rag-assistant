"""Composition Root — construye e inyecta las dependencias desde Settings.

Única capa que conoce a la vez application e infrastructure. El embedder (modelo
CPU) y el pool se crean una sola vez; el LLM se construye perezosamente (permite
arrancar la API y /health aunque aún no haya GOOGLE_API_KEY configurada).
"""
from __future__ import annotations

import structlog

from src.application.use_cases import AnswerQueryUseCase, IngestDataUseCase
from src.interface.config import Settings, get_settings

log = structlog.get_logger(__name__)


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        from src.infrastructure.embeddings import SentenceTransformerEmbedder
        from src.infrastructure.persistence import (
            PgChatMemoryRepository,
            PgVectorKnowledgeRepository,
            create_pool,
        )
        from src.infrastructure.retrieval import DenseRetrieval

        self.pool = create_pool(self.settings.pg_dsn)
        self.embedder = SentenceTransformerEmbedder(self.settings.embedding_model)
        self.knowledge_repo = PgVectorKnowledgeRepository(self.pool)
        self.memory_repo = PgChatMemoryRepository(self.pool)
        self.retrieval = DenseRetrieval(self.embedder, self.knowledge_repo)
        self._llm = None

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
        )

    def ingest_use_case(self) -> IngestDataUseCase:
        return IngestDataUseCase(
            embedder=self.embedder,
            knowledge_repo=self.knowledge_repo,
        )

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
