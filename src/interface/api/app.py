"""API FastAPI — expone el motor RAG por REST (CU-02/03/04).

Frontera pública que consume Streamlit. No contiene lógica de negocio: traduce
HTTP ↔ casos de uso (DTO) y serializa. El Container se crea una vez (lifespan).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
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


class HealthResponse(BaseModel):
    status: str
    db: bool
    provider: str


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
        answer = use_case.execute(sid, req.message)  # type: ignore[arg-type]
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
