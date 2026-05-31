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
        max_depth: int = 3,
        headless: bool = True,
        reconnect_time: float = 4.0,
        start_urls: list[str] | None = None,
        allowed_prefixes: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> None:
        self._base_url = base_url
        self._raw_dir = Path(raw_dir)
        self._max_pages = max_pages
        self._max_depth = max_depth
        self._headless = headless
        self._reconnect_time = reconnect_time
        self._domain = urlparse(base_url).netloc
        self._start_urls = start_urls or [base_url]
        self._allowed_prefixes = tuple(
            prefix if prefix.startswith("/") else f"/{prefix}"
            for raw_prefix in (allowed_prefixes or [])
            if (prefix := raw_prefix.strip())
        )
        self._exclude_patterns = tuple(
            pattern.strip().lower() for pattern in (exclude_patterns or []) if pattern.strip()
        )

    def scrape(self) -> list[Document]:
        """BFS acotado desde `base_url`; guarda crudo y devuelve los Documents."""
        # Import diferido: SeleniumBase solo se necesita al scrapear (mantiene
        # liviano el resto de la app y los tests que no scrapean).
        from seleniumbase import SB

        self._raw_dir.mkdir(parents=True, exist_ok=True)
        documents: list[Document] = []
        seen: set[str] = set()
        queued: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        for url in self._start_urls:
            normalized = self._normalize_url(url)
            if normalized and self._is_allowed_url(normalized):
                queue.append((normalized, 0))
                queued.add(normalized)

        with SB(uc=True, headless=self._headless) as sb:
            while queue and len(documents) < self._max_pages:
                url, depth = queue.popleft()
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

                if depth >= self._max_depth:
                    continue
                for link in self._extract_links(sb, url):
                    if link not in seen and link not in queued:
                        queue.append((link, depth + 1))
                        queued.add(link)

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
            hrefs = (
                sb.execute_script(
                    "return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"
                )
                or []
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("extract_links_failed", url=current_url, error=str(exc))
            return links

        seen: set[str] = set()
        for href in hrefs:
            normalized = self._normalize_url(href, current_url=current_url)
            if not normalized or normalized in seen or not self._is_allowed_url(normalized):
                continue
            links.append(normalized)
            seen.add(normalized)
        return sorted(links, key=self._link_priority)

    def _normalize_url(self, url: str, current_url: str | None = None) -> str | None:
        absolute = urljoin(current_url or self._base_url, url)
        absolute = urldefrag(absolute).url
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return None
        return parsed._replace(query="").geturl()

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc != self._domain:
            return False
        if _SKIP_EXT.search(parsed.path):
            return False
        lowered = url.lower()
        if any(pattern in lowered for pattern in self._exclude_patterns):
            return False
        if not self._allowed_prefixes:
            return True
        path = parsed.path or "/"
        return path == "/" or any(path.startswith(prefix) for prefix in self._allowed_prefixes)

    @staticmethod
    def _link_priority(url: str) -> tuple[int, int, str]:
        path = urlparse(url).path.lower()
        score = 0
        if "/productos" in path:
            score -= 30
        if "/servicios" in path:
            score -= 20
        if path.startswith(("/personas", "/empresas")):
            score -= 10
        return (score, path.count("/"), url)
