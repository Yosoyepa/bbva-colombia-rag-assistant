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
                INSERT INTO chat_messages (id, session_id, message_role, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(message.id),
                    str(message.session_id),
                    message.role,
                    message.content,
                    message.created_at,
                ),
            )

    def get_recent_messages(self, session_id: UUID, limit: int) -> list[ChatMessage]:
        with self._pool.connection() as conn, conn.cursor() as cur:
            # Últimos `limit` por tiempo descendente; se invierten a orden cronológico.
            cur.execute(
                """
                SELECT id, session_id, message_role, content, created_at
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
                id=r[0], session_id=r[1], role=r[2], content=r[3], created_at=r[4]
            )
            for r in rows
        ]
