"""CLI de ingesta (`bbva-ingest`) — orquesta el pipeline CU-01.

scrape (SeleniumBase UC) → clean (trafilatura) → chunk (LangChain) → embed → index.
Composition Root para la ingesta: arma la infraestructura y ejecuta el caso de uso.
"""
from __future__ import annotations

import structlog
import typer

from src.interface.config import get_settings

log = structlog.get_logger(__name__)
app = typer.Typer(help="Ingesta de información pública de BBVA al índice vectorial.")


@app.command()
def ingest(
    max_pages: int = typer.Option(25, help="Máximo de páginas a scrapear."),
    headless: bool = typer.Option(True, help="Navegador sin interfaz."),
) -> None:
    """Ejecuta el pipeline completo de ingesta y reporta conteos verificables."""
    from src.infrastructure.embeddings import SentenceTransformerEmbedder
    from src.infrastructure.persistence import PgVectorKnowledgeRepository, create_pool
    from src.infrastructure.scraping import SeleniumBaseScraper, TextChunker, TrafilaturaCleaner
    from src.application.use_cases import IngestDataUseCase

    s = get_settings()
    scraper = SeleniumBaseScraper(s.scrape_base_url, max_pages=max_pages, headless=headless)
    cleaner = TrafilaturaCleaner()
    chunker = TextChunker(chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)

    pool = create_pool(s.pg_dsn)
    embedder = SentenceTransformerEmbedder(s.embedding_model)
    repo = PgVectorKnowledgeRepository(pool)
    use_case = IngestDataUseCase(embedder=embedder, knowledge_repo=repo)

    typer.echo(f"Scrapeando {s.scrape_base_url} (máx {max_pages} páginas)…")
    documents = scraper.scrape()

    all_chunks = []
    for doc in documents:
        text = cleaner.clean(doc)
        if text:
            all_chunks.extend(chunker.chunk(text, doc.source_url))

    typer.echo(f"Documentos: {len(documents)} · Chunks: {len(all_chunks)} · indexando…")
    result = use_case.execute(all_chunks, documents_scraped=len(documents))
    total_indexed = repo.count()
    pool.close()

    typer.echo(
        f"✅ Ingesta completa — documentos={result.documents_scraped} "
        f"chunks_indexados={result.chunks_indexed} (total en índice={total_indexed})"
    )


if __name__ == "__main__":
    app()
