# SPEC-CU01 — Ingesta de conocimiento

**Traza a:** `prueba_tecnica_IAML.md` líneas 15–17 (scraping, almacenar crudo+limpio, vectorizar e indexar).
**Capas:** `infrastructure/scraping` → `application/use_cases/IngestDataUseCase` → `infrastructure/embeddings` + `infrastructure/persistence`.

## Objetivo
Extraer contenido público de bbva.com.co, almacenarlo crudo y limpio en disco, y dejarlo
vectorizado e indexado en pgvector listo para recuperación.

## Actor
Operador que ejecuta el CLI `bbva-ingest`.

## Precondiciones
- Postgres + pgvector arriba (`docker compose up`).
- `.env` con `SCRAPE_BASE_URL`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `PG_*`.

## Flujo principal
1. El scraper (SeleniumBase `uc=True`) navega secciones públicas y guarda **HTML crudo** en `data/raw/`.
2. El cleaner (trafilatura) extrae texto principal → **texto limpio** en `data/clean/`.
3. Chunking (LangChain) parte el texto limpio en `Chunk` con `source_url`.
4. El `Embedder` calcula el vector de cada chunk.
5. `VectorKnowledgeRepository.add_chunks` persiste content + embedding + source_url (índice HNSW).

## Criterios de aceptación
- [ ] Tras la corrida existen archivos en `data/raw/` **y** `data/clean/` (crudo y limpio separados).
- [ ] `document_chunks` tiene ≥1 fila con `vector_embedding` no nulo y `source_url` trazable al archivo limpio.
- [ ] La dimensión del embedding insertado == dimensión declarada por `EMBEDDING_MODEL` (`VECTOR(N)`).
- [ ] `IngestResult` reporta `documents_scraped` y `chunks_indexed` > 0.
- [ ] Reprocesar desde `data/raw/`/`data/clean/` **no** requiere re-scrapear (Store-and-Forward).

## Casos borde
- BBVA bloquea pese a UC → registrar error, no abortar el resto; documentar el atajo en README.
- Página sin contenido principal → trafilatura devuelve vacío → el chunk no se indexa.
