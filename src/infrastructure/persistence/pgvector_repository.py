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
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Crear índices de búsqueda cuando se actualiza una DB ya inicializada."""
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_fts
                    ON document_chunks USING gin (to_tsvector('spanish', content_cleaned))
                """
            )

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

    def replace_chunks(self, chunks: list[Chunk], source_urls: list[str]) -> None:
        if not source_urls:
            self.add_chunks(chunks)
            return
        rows = [
            (str(c.id), c.content, c.embedding, c.source_url)
            for c in chunks
            if c.embedding
        ]
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE source_url = ANY(%s)",
                (source_urls,),
            )
            if rows:
                cur.executemany(
                    """
                    INSERT INTO document_chunks
                        (id, content_cleaned, vector_embedding, source_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    rows,
                )
        log.info("chunks_replaced", sources=len(source_urls), count=len(rows))

    def delete_by_source(self, source_url: str) -> None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM document_chunks WHERE source_url = %s", (source_url,))

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
                dense_score=1.0 - float(row[3]),
            )
            for index, row in enumerate(rows, start=1)
        ]

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: list[float],
        top_k: int,
        dense_weight: float,
        bm25_weight: float,
    ) -> list[Chunk]:
        vector_literal = "[" + ",".join(repr(float(x)) for x in query_embedding) + "]"
        candidate_k = max(top_k * 4, top_k)
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                WITH
                dense AS (
                    SELECT
                        id,
                        content_cleaned,
                        source_url,
                        vector_embedding <=> %s::vector AS distance,
                        1.0 - (vector_embedding <=> %s::vector) AS dense_score,
                        0.0::float AS bm25_score
                    FROM document_chunks
                    ORDER BY distance ASC
                    LIMIT %s
                ),
                lexical AS (
                    SELECT
                        id,
                        content_cleaned,
                        source_url,
                        NULL::float AS distance,
                        0.0::float AS dense_score,
                        ts_rank_cd(
                            to_tsvector('spanish', content_cleaned),
                            plainto_tsquery('spanish', %s)
                        ) AS bm25_score
                    FROM document_chunks
                    WHERE to_tsvector('spanish', content_cleaned)
                          @@ plainto_tsquery('spanish', %s)
                    ORDER BY bm25_score DESC
                    LIMIT %s
                ),
                combined AS (
                    SELECT * FROM dense
                    UNION ALL
                    SELECT * FROM lexical
                ),
                aggregated AS (
                    SELECT
                        id,
                        max(content_cleaned) AS content_cleaned,
                        max(source_url) AS source_url,
                        min(distance) AS distance,
                        max(dense_score) AS dense_score,
                        max(bm25_score / NULLIF(bm25_score + 1.0, 0.0)) AS bm25_score
                    FROM combined
                    GROUP BY id
                )
                SELECT
                    id,
                    content_cleaned,
                    source_url,
                    distance,
                    dense_score,
                    bm25_score,
                    (%s * dense_score + %s * bm25_score) AS hybrid_score
                FROM aggregated
                ORDER BY hybrid_score DESC
                LIMIT %s
                """,
                (
                    vector_literal,
                    vector_literal,
                    candidate_k,
                    query_text,
                    query_text,
                    candidate_k,
                    dense_weight,
                    bm25_weight,
                    top_k,
                ),
            )
            rows = cur.fetchall()
        return [
            Chunk(
                id=row[0],
                content=row[1],
                source_url=row[2],
                embedding=[],
                rank=index,
                distance=float(row[3]) if row[3] is not None else None,
                similarity_score=float(row[4]) if row[4] is not None else None,
                dense_score=float(row[4]) if row[4] is not None else None,
                bm25_score=float(row[5]) if row[5] is not None else None,
                hybrid_score=float(row[6]) if row[6] is not None else None,
            )
            for index, row in enumerate(rows, start=1)
        ]

    def corpus_version(self) -> str:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*)::text || ':' || COALESCE(max(created_at)::text, '')
                FROM document_chunks
                """
            )
            return cur.fetchone()[0]

    def count(self) -> int:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM document_chunks")
            return cur.fetchone()[0]
