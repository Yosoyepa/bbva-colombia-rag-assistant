"""Routers FastAPI separados por responsabilidad."""
from src.interface.api.routers.analytics import router as analytics_router
from src.interface.api.routers.chat import router as chat_router
from src.interface.api.routers.health import router as health_router
from src.interface.api.routers.sessions import router as sessions_router

__all__ = [
    "analytics_router",
    "chat_router",
    "health_router",
    "sessions_router",
]
