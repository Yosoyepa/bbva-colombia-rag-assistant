"""DTOs REST de la API.

Son modelos Pydantic de entrada/salida: validan y serializan datos HTTP, sin
reglas de negocio ni acceso a servicios.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
