"""Scraper de bbva.com.co con SeleniumBase UC (CU-01, Store-and-Forward).

Navega secciones públicas sorteando Cloudflare/WAF (uc=True) y guarda el HTML
**crudo** en disco. No limpia ni chunkea: ese es trabajo del cleaner/chunker.
Reglas de la capa en `AGENTS.md` de esta carpeta.
"""
from __future__ import annotations

import hashlib
import re
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import structlog

from src.domain.entities import Document

log = structlog.get_logger(__name__)

# Tipos de recurso que no son páginas de contenido.
_SKIP_EXT = re.compile(r"\.(pdf|jpg|jpeg|png|gif|svg|webp|css|js|ico|zip|mp4|woff2?)$", re.I)


def _slugify(url: str) -> str:
    """Nombre de archivo estable y legible para una URL (crudo ↔ limpio ↔ source_url)."""
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "index"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-")[:80]
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{slug}-{digest}"


class SeleniumBaseScraper:
    """Crawler acotado de un dominio. BBVA a toda costa (UC mode)."""

    def __init__(
        self,
        base_url: str,
        raw_dir: Path | str = "data/raw",
        max_pages: int = 25,
        headless: bool = True,
        reconnect_time: float = 4.0,
    ) -> None:
        self._base_url = base_url
        self._raw_dir = Path(raw_dir)
        self._max_pages = max_pages
        self._headless = headless
        self._reconnect_time = reconnect_time
        self._domain = urlparse(base_url).netloc

    def scrape(self) -> list[Document]:
        """BFS acotado desde `base_url`; guarda crudo y devuelve los Documents."""
        # Import diferido: SeleniumBase solo se necesita al scrapear (mantiene
        # liviano el resto de la app y los tests que no scrapean).
        from seleniumbase import SB

        self._raw_dir.mkdir(parents=True, exist_ok=True)
        documents: list[Document] = []
        seen: set[str] = set()
        queue: deque[str] = deque([self._base_url])

        with SB(uc=True, headless=self._headless) as sb:
            while queue and len(documents) < self._max_pages:
                url = urldefrag(queue.popleft()).url
                if url in seen:
                    continue
                seen.add(url)
                try:
                    sb.uc_open_with_reconnect(url, reconnect_time=self._reconnect_time)
                    try:
                        sb.uc_gui_click_captcha()  # best-effort si aparece challenge
                    except Exception:
                        pass
                    html = sb.get_page_source()
                except Exception as exc:  # noqa: BLE001 — un fallo de página no aborta el crawl
                    log.warning("scrape_page_failed", url=url, error=str(exc))
                    continue

                doc = Document(source_url=url, raw_html=html)
                self._save_raw(doc)
                documents.append(doc)
                log.info("scraped", url=url, n=len(documents), bytes=len(html))

                for link in self._extract_links(sb, url):
                    if link not in seen:
                        queue.append(link)

        log.info("scrape_done", pages=len(documents), raw_dir=str(self._raw_dir))
        return documents

    def _save_raw(self, doc: Document) -> Path:
        path = self._raw_dir / f"{_slugify(doc.source_url)}.html"
        path.write_text(doc.raw_html, encoding="utf-8")
        return path

    def _extract_links(self, sb, current_url: str) -> list[str]:
        """Enlaces internos (mismo dominio) que parezcan páginas de contenido."""
        links: list[str] = []
        try:
            hrefs = sb.execute_script(
                "return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"
            ) or []
        except Exception as exc:  # noqa: BLE001
            log.warning("extract_links_failed", url=current_url, error=str(exc))
            return links

        for href in hrefs:
            absolute = urljoin(current_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc != self._domain:
                continue
            if _SKIP_EXT.search(parsed.path):
                continue
            links.append(urldefrag(absolute).url)
        return links
