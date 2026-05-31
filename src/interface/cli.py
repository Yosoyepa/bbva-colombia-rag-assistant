"""CLI de ingesta (`bbva-ingest`) — orquesta el pipeline CU-01.

scrape (SeleniumBase UC) → clean (trafilatura) → chunk (LangChain) → embed → index.
Composition Root para la ingesta: arma la infraestructura y ejecuta el caso de uso.
"""

from __future__ import annotations

import hashlib

import structlog
import typer

from src.interface.config import get_settings

log = structlog.get_logger(__name__)
app = typer.Typer(help="Ingesta de información pública de BBVA al índice vectorial.")


@app.command()
def ingest(
    max_pages: int | None = typer.Option(None, help="Máximo de páginas a scrapear."),
    max_depth: int | None = typer.Option(None, help="Profundidad máxima del crawl BFS."),
    start_urls: str | None = typer.Option(
        None,
        help="URLs semilla separadas por coma. Si se omite, usa SCRAPE_START_URLS.",
    ),
    headless: bool = typer.Option(True, help="Navegador sin interfaz."),
    freshness_hours: int | None = typer.Option(
        None,
        help="Horas de frescura para saltar reindexado de páginas sin cambios.",
    ),
    force_refresh: bool = typer.Option(False, help="Reprocesar páginas aunque estén frescas."),
) -> None:
    """Ejecuta el pipeline completo de ingesta y reporta conteos verificables."""
    from src.application.use_cases import IngestDataUseCase, IngestResult
    from src.infrastructure.persistence import (
        PgEmbeddingCacheRepository,
        PgScrapedPageRepository,
        PgVectorKnowledgeRepository,
        create_pool,
    )
    from src.infrastructure.scraping import SeleniumBaseScraper, TextChunker, TrafilaturaCleaner

    s = get_settings()
    effective_max_pages = max_pages or s.scrape_max_pages
    effective_max_depth = max_depth if max_depth is not None else s.scrape_max_depth
    scraper = SeleniumBaseScraper(
        s.scrape_base_url,
        max_pages=effective_max_pages,
        max_depth=effective_max_depth,
        headless=headless,
        start_urls=_csv(start_urls) or s.scrape_start_url_list,
        allowed_prefixes=s.scrape_allowed_prefix_list,
        exclude_patterns=s.scrape_exclude_pattern_list,
    )
    cleaner = TrafilaturaCleaner()
    chunker = TextChunker(chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)

    pool = create_pool(s.pg_dsn)
    embedding_cache = PgEmbeddingCacheRepository(pool)
    scraped_pages = PgScrapedPageRepository(pool)
    repo = PgVectorKnowledgeRepository(pool)

    typer.echo(
        f"Scrapeando {s.scrape_base_url} "
        f"(máx {effective_max_pages} páginas, profundidad {effective_max_depth})…"
    )
    documents = scraper.scrape()

    all_chunks = []
    refresh_source_urls = []
    skipped = 0
    effective_freshness = freshness_hours or s.scrape_freshness_hours
    for doc in documents:
        text = cleaner.clean(doc)
        if text:
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            should_process = scraped_pages.should_process_page(
                source_url=doc.source_url,
                content_hash=content_hash,
                freshness_hours=effective_freshness,
                force_refresh=force_refresh,
                changed_only=s.rescrape_changed_only,
            )
            if not should_process:
                skipped += 1
                continue
            refresh_source_urls.append(doc.source_url)
            all_chunks.extend(chunker.chunk(text, doc.source_url))

    typer.echo(
        f"Documentos: {len(documents)} · omitidos_frescos={skipped} · "
        f"Chunks: {len(all_chunks)} · indexando…"
    )
    if all_chunks:
        from src.infrastructure.embeddings import CachedEmbedder, SentenceTransformerEmbedder

        embedder = SentenceTransformerEmbedder(s.embedding_model)
        if s.embedding_cache_enabled:
            embedder = CachedEmbedder(embedder, embedding_cache, model_name=s.embedding_model)
        use_case = IngestDataUseCase(embedder=embedder, knowledge_repo=repo)
        result = use_case.execute(
            all_chunks,
            documents_scraped=len(documents),
            replace_source_urls=refresh_source_urls,
        )
    else:
        result = IngestResult(documents_scraped=len(documents), chunks_indexed=0)
    total_indexed = repo.count()
    pool.close()

    typer.echo(
        f"✅ Ingesta completa — documentos={result.documents_scraped} "
        f"chunks_indexados={result.chunks_indexed} (total en índice={total_indexed})"
    )


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    app()
