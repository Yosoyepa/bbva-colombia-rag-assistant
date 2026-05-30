"""CLI de analítica (`bbva-analytics`, CU-04). Implementación completa en Fase 2.

Recorrerá el histórico de conversaciones para extraer métricas de impacto
(sesiones, mensajes, fuentes más citadas). Ver SPEC-CU04.
"""
from __future__ import annotations

import typer

app = typer.Typer(help="Métricas de impacto del histórico de conversaciones (CU-04).")


@app.command()
def report() -> None:
    """Genera el reporte de métricas del histórico (disponible en Fase 2)."""
    typer.echo("CU-04 analítica: módulo en construcción (Fase 2).")


if __name__ == "__main__":
    app()
