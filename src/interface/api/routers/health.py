"""Router de healthcheck/readiness."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.interface.api.dependencies import get_container
from src.interface.api.schemas import HealthResponse
from src.interface.container import Container

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(container: Annotated[Container, Depends(get_container)]) -> HealthResponse:
    """Reporta estado de API, base de datos y proveedor activo."""
    db_ok = container.db_healthy()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db=db_ok,
        provider=container.settings.model_provider,
    )
