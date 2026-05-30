# AGENTS.md — `src/infrastructure/scraping/`

Scraping + limpieza. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Obtener contenido público de **bbva.com.co** y dejarlo listo para chunking:

- `SeleniumBaseScraper` (`uc=True`) — navega secciones públicas, sortea Cloudflare/WAF,
  guarda el **HTML crudo** en `data/raw/`.
- `cleaner` (trafilatura) — extrae texto principal del crudo y guarda el **limpio** en `data/clean/`.

## Regla de dependencia

- Alimenta `IngestDataUseCase` produciendo entidades `Document`/texto limpio. Importa
  seleniumbase y trafilatura. No conoce DB ni LLM.

## Patrones / decisiones

- **Store-and-Forward**: persistir crudo y limpio en disco permite **reprocesar sin
  re-scrapear** (resiliencia + frescura controlada). Es el "guardar crudo+limpio" exigido por la prueba.
- **BBVA a toda costa**: priorizar UC mode; si BBVA bloquea pese al esfuerzo, documentar el
  supuesto/atajo en el README (lo permite la prueba) — pero el objetivo es BBVA funcionando.
- **Manejo de errores** (bonus): timeouts, bloqueos y páginas vacías se registran y no tumban la ingesta.

## Para conservar

`data/raw/` y `data/clean/` son artefactos (gitignored). El scraper es respetuoso: solo
contenido público, sin auth, sin cargas agresivas.
