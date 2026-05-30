"""Casos de uso: flujos de negocio que orquestan dominio + ports.

Detalle de responsabilidades y reglas en `AGENTS.md` de esta carpeta.
"""
from src.application.use_cases.analytics import AnalyticsReport, AnalyticsUseCase
from src.application.use_cases.answer_query import Answer, AnswerQueryUseCase
from src.application.use_cases.ingest_data import IngestDataUseCase, IngestResult

__all__ = [
    "AnalyticsReport",
    "AnalyticsUseCase",
    "Answer",
    "AnswerQueryUseCase",
    "IngestDataUseCase",
    "IngestResult",
]
