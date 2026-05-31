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
    max_pages: int = typer.Option(25, help="Máximo de páginas a scrapear."),
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
        PgCacheRepository,
        PgVectorKnowledgeRepository,
        create_pool,
    )
    from src.infrastructure.scraping import SeleniumBaseScraper, TextChunker, TrafilaturaCleaner

    s = get_settings()
    scraper = SeleniumBaseScraper(s.scrape_base_url, max_pages=max_pages, headless=headless)
    cleaner = TrafilaturaCleaner()
    chunker = TextChunker(chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)

    pool = create_pool(s.pg_dsn)
    cache_repo = PgCacheRepository(pool)
    repo = PgVectorKnowledgeRepository(pool)

    typer.echo(f"Scrapeando {s.scrape_base_url} (máx {max_pages} páginas)…")
    documents = scraper.scrape()

    all_chunks = []
    refresh_source_urls = []
    skipped = 0
    effective_freshness = freshness_hours or s.scrape_freshness_hours
    for doc in documents:
        text = cleaner.clean(doc)
        if text:
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            should_process = cache_repo.should_process_page(
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
            embedder = CachedEmbedder(embedder, cache_repo, model_name=s.embedding_model)
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


if __name__ == "__main__":
    app()
