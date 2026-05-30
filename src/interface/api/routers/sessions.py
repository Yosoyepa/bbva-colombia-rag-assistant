"""Router de sesiones y mensajes persistidos (CU-03)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.interface.api.dependencies import get_container
from src.interface.api.schemas import ChatMessageResponse, SessionSummaryResponse
from src.interface.container import Container

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=list[SessionSummaryResponse])
def sessions(
    container: Annotated[Container, Depends(get_container)],
    limit: int = 20,
) -> list[SessionSummaryResponse]:
    """Lista conversaciones recientes con título, conteo y timestamps."""
    rows = container.memory_repo.list_sessions(limit=max(1, min(limit, 100)))
    return [
        SessionSummaryResponse(
            session_id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            message_count=row.message_count,
            title=row.title,
        )
        for row in rows
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def session_messages(
    session_id: UUID,
    container: Annotated[Container, Depends(get_container)],
    limit: int = 100,
) -> list[ChatMessageResponse]:
    """Carga los mensajes de una conversación persistida."""
    rows = container.memory_repo.get_recent_messages(session_id, max(1, min(limit, 500)))
    return [
        ChatMessageResponse(
            role=row.role,
            content=row.content,
            sources=row.sources,
            created_at=row.created_at,
        )
        for row in rows
    ]
