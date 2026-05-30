"""API FastAPI — expone el motor RAG por REST (CU-02/03/04).

Frontera pública que consume Streamlit. No contiene lógica de negocio: traduce
HTTP ↔ casos de uso (DTO) y serializa. El Container se crea una vez (lifespan).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.interface.container import Container

log = structlog.get_logger(__name__)


# ── DTOs ──────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: UUID | None = None


class ChatResponse(BaseModel):
    session_id: UUID
    content: str
    sources: list[str]


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    created_at: datetime
    updated_at: datetime | None
    message_count: int
    title: str


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    sources: list[str]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    db: bool
    provider: str


class SourceMetric(BaseModel):
    source_url: str
    citations: int


class AnalyticsResponse(BaseModel):
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    top_sources: list[SourceMetric]


# ── App ─────────────────────────────────────────────────────────────────────--
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()
    log.info("api_started")
    try:
        yield
    finally:
        app.state.container.close()


app = FastAPI(title="BBVA RAG API", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    c: Container = app.state.container
    db_ok = c.db_healthy()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db=db_ok,
        provider=c.settings.model_provider,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    c: Container = app.state.container
    try:
        use_case = c.answer_use_case()
        # session_id None => el caso de uso crea una sesión nueva.
        sid = req.session_id
        answer = use_case.execute(sid, req.message)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:  # p.ej. GOOGLE_API_KEY ausente
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log.error("chat_failed", error=str(exc))
        raise HTTPException(status_code=502, detail="error generando la respuesta") from exc

    return ChatResponse(
        session_id=answer.session_id, content=answer.content, sources=answer.sources
    )


@app.get("/sessions", response_model=list[SessionSummaryResponse])
def sessions(limit: int = 20) -> list[SessionSummaryResponse]:
    c: Container = app.state.container
    try:
        rows = c.memory_repo.list_sessions(limit=max(1, min(limit, 100)))
    except Exception as exc:  # noqa: BLE001
        log.error("sessions_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="error leyendo las sesiones") from exc
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


@app.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def session_messages(session_id: UUID, limit: int = 100) -> list[ChatMessageResponse]:
    c: Container = app.state.container
    try:
        rows = c.memory_repo.get_recent_messages(session_id, max(1, min(limit, 500)))
    except Exception as exc:  # noqa: BLE001
        log.error("session_messages_failed", session_id=str(session_id), error=str(exc))
        raise HTTPException(status_code=503, detail="error leyendo los mensajes") from exc
    return [
        ChatMessageResponse(
            role=row.role,
            content=row.content,
            sources=row.sources,
            created_at=row.created_at,
        )
        for row in rows
    ]


@app.get("/analytics", response_model=AnalyticsResponse)
def analytics() -> AnalyticsResponse:
    c: Container = app.state.container
    try:
        report = c.analytics_use_case().execute()
    except Exception as exc:  # noqa: BLE001
        log.error("analytics_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="error leyendo el histórico") from exc
    return AnalyticsResponse(
        total_sessions=report.total_sessions,
        total_messages=report.total_messages,
        avg_messages_per_session=report.avg_messages_per_session,
        top_sources=[
            SourceMetric(source_url=url, citations=count)
            for url, count in report.top_sources
        ],
    )
