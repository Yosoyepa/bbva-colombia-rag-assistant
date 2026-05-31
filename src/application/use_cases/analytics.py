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
    top_sources: list[tuple[str, int]]  # (source_url, veces citada)
    avg_messages_per_session: float


class AnalyticsUseCase:
    def __init__(self, memory: ChatMemoryRepository) -> None:
        self._memory = memory

    def execute(self) -> AnalyticsReport:
        """Recorrer el histórico real y agregar métricas de impacto."""
        total_sessions = self._memory.count_sessions()
        total_messages = self._memory.count_messages()
        avg_messages = total_messages / total_sessions if total_sessions else 0.0
        return AnalyticsReport(
            total_sessions=total_sessions,
            total_messages=total_messages,
            top_sources=self._memory.top_sources(limit=10),
            avg_messages_per_session=avg_messages,
        )
