"""Scraping + limpieza + chunking (alimenta IngestDataUseCase). Ver AGENTS.md."""

__all__ = ["SeleniumBaseScraper", "TrafilaturaCleaner", "TextChunker"]


def __getattr__(name: str):
    if name == "SeleniumBaseScraper":
        from src.infrastructure.scraping.scraper import SeleniumBaseScraper

        return SeleniumBaseScraper
    if name == "TrafilaturaCleaner":
        from src.infrastructure.scraping.cleaner import TrafilaturaCleaner

        return TrafilaturaCleaner
    if name == "TextChunker":
        from src.infrastructure.scraping.chunker import TextChunker

        return TextChunker
    raise AttributeError(name)
