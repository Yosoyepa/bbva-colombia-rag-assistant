"""Dependencias FastAPI para acceder al Composition Root."""
from __future__ import annotations

from fastapi import Request

from src.interface.container import Container


def get_container(request: Request) -> Container:
    """Retorna el contenedor construido en el lifespan de la aplicación."""
    return request.app.state.container
