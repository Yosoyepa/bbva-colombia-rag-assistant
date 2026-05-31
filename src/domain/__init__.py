"""Dominio: entidades de negocio puras (sin dependencias externas).

Reglas en `AGENTS.md` de esta carpeta.
"""

from src.domain.entities import ChatMessage, ChatSession, Chunk, Document

__all__ = ["ChatMessage", "ChatSession", "Chunk", "Document"]
