"""CLI de analítica (`bbva-analytics`, CU-04).

Recorre el histórico real de conversaciones para extraer métricas de impacto
(sesiones, mensajes, fuentes más citadas). Ver SPEC-CU04.
"""
from __future__ import annotations

import typer

from src.interface.container import Container

app = typer.Typer(help="Métricas de impacto del histórico de conversaciones (CU-04).")


@app.command()
def report(limit: int = typer.Option(10, help="Máximo de fuentes a mostrar.")) -> None:
    """Genera el reporte de métricas del histórico."""
    container = Container()
    try:
        analytics_report = container.analytics_use_case().execute()
    finally:
        container.close()

    typer.echo("Reporte de analítica BBVA RAG")
    typer.echo(f"Sesiones totales: {analytics_report.total_sessions}")
    typer.echo(f"Mensajes totales: {analytics_report.total_messages}")
    typer.echo(
        "Mensajes promedio por sesión: "
        f"{analytics_report.avg_messages_per_session:.2f}"
    )
    typer.echo("Fuentes más citadas:")
    for source_url, citations in analytics_report.top_sources[:limit]:
        typer.echo(f"- {source_url}: {citations}")
    if not analytics_report.top_sources:
        typer.echo("- Sin fuentes citadas todavía.")


if __name__ == "__main__":
    app()
