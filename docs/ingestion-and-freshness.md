# Ingesta, scraping y frescura

La ingesta materializa el requisito de extraer informacion del sitio, conservar datos
crudos y limpios, vectorizar e indexar.

```text
bbva-ingest
  -> scrape
  -> clean
  -> chunk
  -> embed
  -> index
```

## Scraping

El scraper usa SeleniumBase UC para mejorar tolerancia a paginas modernas. No intenta
recorrer todo el sitio: parte de semillas de alto valor y aplica limites para mantener la
ejecucion reproducible.

Variables relevantes:

- `SCRAPE_BASE_URL`
- `SCRAPE_START_URLS`
- `SCRAPE_MAX_PAGES`
- `SCRAPE_MAX_DEPTH`
- `SCRAPE_ALLOWED_PREFIXES`
- `SCRAPE_EXCLUDE_PATTERNS`

Ejemplo:

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
```

## Datos crudos y limpios

- HTML crudo: `data/raw`.
- Texto limpio: `data/clean`.
- Chunks vectorizados: tabla `document_chunks`.

Este Store-and-Forward permite auditar que se extrajo y que se limpio antes de indexar.

## Frescura y deteccion de cambios

La tabla `scraped_pages` registra:

- `source_url`
- `content_hash`
- `fetched_at`
- `changed_at`
- `status`

Si una pagina esta fresca y su hash no cambio, la ingesta puede saltar reindexado. Esto
reduce trabajo repetido y evita que cada demo vuelva a procesar contenido identico.

Comandos utiles:

```bash
docker compose exec app bbva-ingest --max-pages 3 --freshness-hours 24
docker compose exec app bbva-ingest --max-pages 3 --force-refresh
```

No se incluye scheduler externo. En operacion continua, cron, GitHub Actions o un
orquestador pueden invocar el CLI con la politica de frescura deseada.
