"""Chunking de texto limpio → Chunk (CU-01).

Usa RecursiveCharacterTextSplitter (LangChain): respeta límites naturales
(párrafos, frases) con solape configurable. CHUNK_SIZE/CHUNK_OVERLAP por env.
"""
from __future__ import annotations

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.domain.entities import Chunk

log = structlog.get_logger(__name__)


class TextChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, text: str, source_url: str) -> list[Chunk]:
        """Partir el texto limpio en chunks anclados a su URL de origen."""
        pieces = [p.strip() for p in self._splitter.split_text(text) if p.strip()]
        chunks = [Chunk(content=piece, source_url=source_url) for piece in pieces]
        log.info("chunked", url=source_url, chunks=len(chunks))
        return chunks
