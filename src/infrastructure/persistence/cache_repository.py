"""Caches y frescura sobre PostgreSQL.

Agrupa almacenamiento auxiliar del pipeline: embeddings, respuestas y páginas
scrapeadas. El SQL permanece en infraestructura.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from psycopg_pool import ConnectionPool

from src.application.ports import AnswerCacheRepository, CachedAnswer
from src.domain.entities import Chunk


class PgCacheRepository(AnswerCacheRepository):
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Crear tablas auxiliares cuando la DB ya existía antes de v1.3.0."""
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    cache_key        TEXT PRIMARY KEY,
                    model_name       TEXT NOT NULL,
                    text_hash        TEXT NOT NULL,
                    vector_embedding VECTOR(384) NOT NULL,
                    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS answer_cache (
                    cache_key       TEXT PRIMARY KEY,
                    content         TEXT NOT NULL,
                    sources         TEXT[] NOT NULL DEFAULT '{}',
                    retrieval_trace JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scraped_pages (
                    source_url   TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
                    changed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
                    status       VARCHAR(24) NOT NULL DEFAULT 'new'
                )
                """)

    def get_embedding(self, cache_key: str) -> list[float] | None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT vector_embedding::text FROM embedding_cache WHERE cache_key = %s",
                (cache_key,),
            )
            row = cur.fetchone()
        if not row:
            return None
        raw = str(row[0]).strip("[]")
        return [float(value) for value in raw.split(",") if value]

    def set_embedding(
        self,
        cache_key: str,
        model_name: str,
        text_hash: str,
        embedding: list[float],
    ) -> None:
        vector_literal = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO embedding_cache
                    (cache_key, model_name, text_hash, vector_embedding, created_at)
                VALUES (%s, %s, %s, %s::vector, now())
                ON CONFLICT (cache_key) DO UPDATE SET
                    vector_embedding = EXCLUDED.vector_embedding,
                    created_at = EXCLUDED.created_at
                """,
                (cache_key, model_name, text_hash, vector_literal),
            )

    def get_answer(self, cache_key: str, ttl_seconds: int) -> CachedAnswer | None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT content, sources, retrieval_trace
                FROM answer_cache
                WHERE cache_key = %s
                  AND created_at >= now() - (%s || ' seconds')::interval
                """,
                (cache_key, ttl_seconds),
            )
            row = cur.fetchone()
        if not row:
            return None

        trace = row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]")
        chunks = [
            Chunk(
                content=item.get("content_preview", ""),
                source_url=item.get("source_url", ""),
                rank=item.get("rank"),
                distance=item.get("distance"),
                similarity_score=item.get("similarity_score"),
                rerank_score=item.get("rerank_score"),
                dense_score=item.get("dense_score"),
                bm25_score=item.get("bm25_score"),
                hybrid_score=item.get("hybrid_score"),
            )
            for item in trace
        ]
        return CachedAnswer(content=row[0], sources=list(row[1] or []), chunks=chunks)

    def set_answer(self, cache_key: str, answer: CachedAnswer) -> None:
        trace = [
            {
                "rank": chunk.rank,
                "source_url": chunk.source_url,
                "distance": chunk.distance,
                "similarity_score": chunk.similarity_score,
                "rerank_score": chunk.rerank_score,
                "dense_score": chunk.dense_score,
                "bm25_score": chunk.bm25_score,
                "hybrid_score": chunk.hybrid_score,
                "content_preview": " ".join(chunk.content.split())[:260],
            }
            for chunk in answer.chunks
        ]
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO answer_cache
                    (cache_key, content, sources, retrieval_trace, created_at)
                VALUES (%s, %s, %s, %s::jsonb, now())
                ON CONFLICT (cache_key) DO UPDATE SET
                    content = EXCLUDED.content,
                    sources = EXCLUDED.sources,
                    retrieval_trace = EXCLUDED.retrieval_trace,
                    created_at = EXCLUDED.created_at
                """,
                (cache_key, answer.content, answer.sources, json.dumps(trace)),
            )

    def should_process_page(
        self,
        source_url: str,
        content_hash: str,
        freshness_hours: int,
        force_refresh: bool,
        changed_only: bool,
    ) -> bool:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT content_hash, fetched_at FROM scraped_pages WHERE source_url = %s",
                (source_url,),
            )
            row = cur.fetchone()
            now = datetime.utcnow()
            is_fresh = bool(
                row and now - row[1].replace(tzinfo=None) < timedelta(hours=freshness_hours)
            )
            unchanged = bool(row and row[0] == content_hash)

            if force_refresh:
                status, process = "forced", True
            elif unchanged and is_fresh:
                status, process = "fresh", False
            elif unchanged and changed_only:
                status, process = "unchanged", False
            else:
                status, process = "changed" if row else "new", True

            cur.execute(
                """
                INSERT INTO scraped_pages
                    (source_url, content_hash, fetched_at, changed_at, status)
                VALUES (%s, %s, now(), now(), %s)
                ON CONFLICT (source_url) DO UPDATE SET
                    content_hash = EXCLUDED.content_hash,
                    fetched_at = EXCLUDED.fetched_at,
                    changed_at = CASE
                        WHEN scraped_pages.content_hash <> EXCLUDED.content_hash
                             OR %s
                        THEN EXCLUDED.changed_at
                        ELSE scraped_pages.changed_at
                    END,
                    status = EXCLUDED.status
                """,
                (source_url, content_hash, status, force_refresh),
            )
        return process
