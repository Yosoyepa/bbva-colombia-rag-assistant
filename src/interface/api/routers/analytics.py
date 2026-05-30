"""Router de analítica histórica (CU-04)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.interface.api.dependencies import get_container
from src.interface.api.schemas import AnalyticsResponse, SourceMetric
from src.interface.container import Container

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    container: Annotated[Container, Depends(get_container)],
) -> AnalyticsResponse:
    """Retorna métricas agregadas del histórico conversacional."""
    report = container.analytics_use_case().execute()
    return AnalyticsResponse(
        total_sessions=report.total_sessions,
        total_messages=report.total_messages,
        avg_messages_per_session=report.avg_messages_per_session,
        top_sources=[
            SourceMetric(source_url=url, citations=count)
            for url, count in report.top_sources
        ],
    )
