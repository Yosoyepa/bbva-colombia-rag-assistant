"""Manejo global de excepciones de la frontera REST.

La lógica de negocio no vive aquí; este módulo solo traduce fallos de aplicación,
configuración o infraestructura a respuestas HTTP consistentes.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra el mapeo centralizado de excepciones a códigos HTTP."""

    @app.exception_handler(NotImplementedError)
    async def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
        log.warning("api_not_implemented", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=501, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        log.warning("api_configuration_error", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        status_code = 503 if _looks_like_storage_error(exc) else 502
        detail = (
            "error leyendo una dependencia del sistema"
            if status_code == 503
            else "error generando la respuesta"
        )
        log.error(
            "api_unhandled_error",
            path=request.url.path,
            status_code=status_code,
            error=str(exc),
        )
        return JSONResponse(status_code=status_code, content={"detail": detail})


def _looks_like_storage_error(exc: Exception) -> bool:
    module = type(exc).__module__
    text = str(exc).lower()
    return module.startswith("psycopg") or "connection" in text or "database" in text
