from src.infrastructure.scraping.scraper import SeleniumBaseScraper


class FakeBrowser:
    def __init__(self, hrefs: list[str]) -> None:
        self._hrefs = hrefs

    def execute_script(self, script: str) -> list[str]:
        return self._hrefs


def test_scraper_filters_and_prioritizes_business_pages():
    scraper = SeleniumBaseScraper(
        "https://www.bbva.com.co/",
        allowed_prefixes=["/personas", "/empresas"],
        exclude_patterns=["aviso-legal", "cookies"],
    )
    browser = FakeBrowser(
        [
            "/personas/aviso-legal.html",
            "/personas/productos/cuentas/ahorro.html?cid=tracking",
            "/empresas/productos/pymes.html",
            "https://www.bbva.com.co/personas/documento.pdf",
            "https://www.bbva.com.ar/personas/productos.html",
            "mailto:info@example.com",
        ]
    )

    links = scraper._extract_links(browser, "https://www.bbva.com.co/")

    assert links == [
        "https://www.bbva.com.co/empresas/productos/pymes.html",
        "https://www.bbva.com.co/personas/productos/cuentas/ahorro.html",
    ]
