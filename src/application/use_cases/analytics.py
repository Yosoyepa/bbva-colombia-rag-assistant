"""CU-04: analítica — recorrer el histórico y derivar métricas de impacto.

Stub: se completa en Fase 2. Lee el histórico de chat (memoria) y produce
métricas para demostrar el valor del asistente.
"""
from dataclasses import dataclass

from src.application.ports import ChatMemoryRepository


@dataclass
class AnalyticsReport:
    """Métricas de uso del histórico (CU-04)."""
    total_sessions: int
    total_messages: int
    top_sources: list[tuple[str, int]]   # (source_url, veces citada)
    avg_messages_per_session: float


class AnalyticsUseCase:
    def __init__(self, memory: ChatMemoryRepository) -> None:
        self._memory = memory

    def execute(self) -> AnalyticsReport:
        """Recorrer el histórico y agregar métricas. TODO(Fase 2)."""
        raise NotImplementedError
