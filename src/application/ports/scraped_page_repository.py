"""Port: política de frescura de páginas scrapeadas."""

from abc import ABC, abstractmethod


class ScrapedPageRepository(ABC):
    @abstractmethod
    def should_process_page(
        self,
        source_url: str,
        content_hash: str,
        freshness_hours: int,
        force_refresh: bool,
        changed_only: bool,
    ) -> bool:
        """Decidir si una URL requiere reindexado según hash y frescura."""
        ...
