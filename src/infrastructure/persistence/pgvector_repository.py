"""Repositorio de conocimiento sobre pgvector (adapta VectorKnowledgeRepository).

Persiste chunks con embedding y busca top-K por similitud coseno (índice HNSW).
Todo el SQL vive aquí; el núcleo solo ve entidades de dominio.
"""
from __future__ import annotations

import structlog
from psycopg_pool import ConnectionPool

from src.application.ports import VectorKnowledgeRepository
from src.domain.entities import Chunk

log = structlog.get_logger(__name__)


class PgVectorKnowledgeRepository(VectorKnowledgeRepository):
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        rows = [
            (str(c.id), c.content, c.embedding, c.source_url)
            for c in chunks
            if c.embedding  # no indexar chunks sin embedding
        ]
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO document_chunks (id, content_cleaned, vector_embedding, source_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                rows,
            )
        log.info("chunks_inserted", count=len(rows))

    def search(self, query_embedding: list[float], top_k: int) -> list[Chunk]:
        # Literal de vector + cast explícito: en ORDER BY el tipo no se infiere y
        # una list se adaptaría como double precision[] (sin operador <=>).
        vector_literal = "[" + ",".join(repr(float(x)) for x in query_embedding) + "]"
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    content_cleaned,
                    source_url,
                    vector_embedding <=> %s::vector AS distance
                FROM document_chunks
                ORDER BY distance ASC
                LIMIT %s
                """,
                (vector_literal, top_k),
            )
            rows = cur.fetchall()
        return [
            Chunk(
                id=row[0],
                content=row[1],
                source_url=row[2],
                embedding=[],
                rank=index,
                distance=float(row[3]),
                similarity_score=1.0 - float(row[3]),
            )
            for index, row in enumerate(rows, start=1)
        ]

    def count(self) -> int:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM document_chunks")
            return cur.fetchone()[0]
