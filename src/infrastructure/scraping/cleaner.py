"""Limpieza de HTML crudo → texto principal (CU-01).

trafilatura extrae el contenido relevante (descarta nav/footer/scripts) y se
guarda el **texto limpio** en disco (Store-and-Forward: reprocesable sin re-scrapear).
"""
from __future__ import annotations

from pathlib import Path

import structlog
import trafilatura

from src.domain.entities import Document
from src.infrastructure.scraping.scraper import _slugify

log = structlog.get_logger(__name__)


class TrafilaturaCleaner:
    def __init__(self, clean_dir: Path | str = "data/clean") -> None:
        self._clean_dir = Path(clean_dir)

    def clean(self, document: Document) -> str | None:
        """Devolver el texto principal del documento, o None si no hay contenido útil."""
        text = trafilatura.extract(
            document.raw_html,
            url=document.source_url,
            favor_recall=True,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if not text or not text.strip():
            log.warning("clean_empty", url=document.source_url)
            return None

        self._save_clean(document.source_url, text)
        log.info("cleaned", url=document.source_url, chars=len(text))
        return text

    def _save_clean(self, source_url: str, text: str) -> Path:
        self._clean_dir.mkdir(parents=True, exist_ok=True)
        path = self._clean_dir / f"{_slugify(source_url)}.txt"
        # Primera línea = source_url para trazabilidad crudo↔limpio↔chunk.
        path.write_text(f"{source_url}\n\n{text}", encoding="utf-8")
        return path
