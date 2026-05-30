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


class RetrievalTraceItem(BaseModel):
    rank: int | None = None
    source_url: str
    distance: float | None = None
    similarity_score: float | None = None
    rerank_score: float | None = None
    dense_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
    content_preview: str


class ChatObservabilityResponse(BaseModel):
    total_latency_ms: float
    retrieval_latency_ms: float
    prompt_latency_ms: float
    llm_latency_ms: float
    persistence_latency_ms: float
    provider: str | None = None
    cache_hit: bool = False


class ChatResponse(BaseModel):
    session_id: UUID
    content: str
    sources: list[str]
    retrieval_trace: list[RetrievalTraceItem] = Field(default_factory=list)
    observability: ChatObservabilityResponse | None = None


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
