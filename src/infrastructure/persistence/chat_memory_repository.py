"""Memoria conversacional sobre PostgreSQL (adapta ChatMemoryRepository, CU-03).

Sesiones por ID, mensajes persistidos y ventana de últimos N (N por env).
"""
from __future__ import annotations

from uuid import UUID

import structlog
from psycopg_pool import ConnectionPool

from src.application.ports import ChatMemoryRepository
from src.domain.entities import ChatMessage, ChatSession

log = structlog.get_logger(__name__)


class PgChatMemoryRepository(ChatMemoryRepository):
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def get_or_create_session(self, session_id: UUID | None = None) -> ChatSession:
        session = ChatSession() if session_id is None else ChatSession(id=session_id)
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (session_id, created_at)
                VALUES (%s, %s)
                ON CONFLICT (session_id) DO NOTHING
                """,
                (str(session.id), session.created_at),
            )
        return session

    def add_message(self, message: ChatMessage) -> None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_messages
                    (id, session_id, message_role, content, sources, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(message.id),
                    str(message.session_id),
                    message.role,
                    message.content,
                    list(message.sources),  # psycopg adapta list[str] → TEXT[]
                    message.created_at,
                ),
            )

    def get_recent_messages(self, session_id: UUID, limit: int) -> list[ChatMessage]:
        with self._pool.connection() as conn, conn.cursor() as cur:
            # Últimos `limit` por tiempo descendente; se invierten a orden cronológico.
            cur.execute(
                """
                SELECT id, session_id, message_role, content, sources, created_at
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (str(session_id), limit),
            )
            rows = cur.fetchall()
        rows.reverse()
        return [
            ChatMessage(
                id=r[0],
                session_id=r[1],
                role=r[2],
                content=r[3],
                sources=list(r[4] or []),
                created_at=r[5],
            )
            for r in rows
        ]

    def count_sessions(self) -> int:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chat_sessions")
            return cur.fetchone()[0]

    def count_messages(self) -> int:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chat_messages")
            return cur.fetchone()[0]

    def top_sources(self, limit: int = 10) -> list[tuple[str, int]]:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_url, count(*) AS citations
                FROM chat_messages
                CROSS JOIN LATERAL unnest(sources) AS source_url
                WHERE message_role = 'assistant'
                GROUP BY source_url
                ORDER BY citations DESC, source_url ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
        return [(row[0], row[1]) for row in rows]
