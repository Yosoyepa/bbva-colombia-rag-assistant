"""Persistencia PostgreSQL + pgvector. Ver AGENTS.md."""
from src.infrastructure.persistence.connection import create_pool
from src.infrastructure.persistence.pgvector_repository import PgVectorKnowledgeRepository

__all__ = ["create_pool", "PgVectorKnowledgeRepository"]
