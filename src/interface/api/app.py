"""Factory de la API FastAPI.

Este módulo solo ensambla la frontera REST: lifespan, manejo global de errores
y routers. Los DTOs, rutas y dependencias viven en módulos separados.
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from src.interface.api.errors import register_exception_handlers
from src.interface.api.routers import (
    analytics_router,
    chat_router,
    health_router,
    sessions_router,
)
from src.interface.container import Container

log = structlog.get_logger(__name__)


def create_app(container_factory: Callable[[], Container] = Container) -> FastAPI:
    """Crea la app FastAPI con dependencias y routers registrados."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container_factory()
        log.info("api_started")
        try:
            yield
        finally:
            app.state.container.close()

    app = FastAPI(title="BBVA RAG API", version="1.2.0", lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(sessions_router)
    app.include_router(analytics_router)
    return app


app = create_app()
