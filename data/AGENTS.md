# AGENTS.md — `data/`

Artefactos de la ingesta (Store-and-Forward). Ver [contexto global](../AGENTS.md).

## Responsabilidad

Persistir en disco los productos intermedios del pipeline de ingesta:

- `raw/` — HTML crudo tal cual lo devuelve el scraper.
- `clean/` — texto limpio (post-trafilatura), listo para chunking.

## Patrón / decisión

- **Store-and-Forward**: guardar crudo y limpio permite **reprocesar sin re-scrapear**
  (cambiar chunking/embedding sin volver a golpear BBVA) y da resiliencia ante fallos aguas abajo.
  Es el "almacenar crudo + limpio" que exige la prueba.

## Regla de negocio

- Ambos subdirectorios son **artefactos generados** → `gitignored` (`data/raw/`, `data/clean/`).
  No se versionan; se regeneran con `bbva-ingest`.
- La carpeta `data/` (con este `AGENTS.md`) sí existe en el repo para documentar el contrato.

## Para conservar

El nombre de archivo debe permitir trazar crudo ↔ limpio ↔ `source_url` del chunk en la DB
(trazabilidad de la fuente para anclar respuestas).
