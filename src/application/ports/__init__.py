"""Ports: contratos abstractos del núcleo (Ports & Adapters).

La infraestructura implementa estas interfaces; la aplicación solo las conoce a
ellas. Detalle de diseño y reglas en `AGENTS.md` de esta carpeta.
"""
from src.application.ports.chat_memory_repository import ChatMemoryRepository
from src.application.ports.embedder import Embedder
from src.application.ports.large_language_model import LargeLanguageModel
from src.application.ports.retrieval_strategy import RetrievalStrategy
from src.application.ports.vector_knowledge_repository import VectorKnowledgeRepository

__all__ = [
    "ChatMemoryRepository",
    "Embedder",
    "LargeLanguageModel",
    "RetrievalStrategy",
    "VectorKnowledgeRepository",
]
