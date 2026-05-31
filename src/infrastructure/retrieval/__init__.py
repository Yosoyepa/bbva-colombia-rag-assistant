"""Estrategias de recuperación (Strategy). Ver AGENTS.md."""

from src.infrastructure.retrieval.dense_retrieval import DenseRetrieval
from src.infrastructure.retrieval.hybrid_retrieval import HybridRetrieval
from src.infrastructure.retrieval.rerank_retrieval import RerankRetrieval

__all__ = ["DenseRetrieval", "HybridRetrieval", "RerankRetrieval"]
