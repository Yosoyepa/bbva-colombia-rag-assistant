# AGENTS.md — `src/infrastructure/`

Los **Adapters**. Ver [contexto global](../../AGENTS.md).

## Responsabilidad

Implementar los ports de `application` contra tecnologías concretas. Cada subcarpeta adapta
un mundo externo a una interfaz del núcleo:

- `persistence/` — PostgreSQL + pgvector (VectorKnowledgeRepository, ChatMemoryRepository).
- `llm/` — proveedores LLM + Factory + fallback (LargeLanguageModel).
- `embeddings/` — sentence-transformers en CPU (Embedder).
- `scraping/` — SeleniumBase UC + trafilatura (alimenta IngestDataUseCase).
- `retrieval/` — Dense / Rerank (RetrievalStrategy).

## Regla de dependencia

- Puede importar `domain` y `application.ports`. **Nunca** `interface`.
- Aquí —y solo aquí— viven los imports de librerías: psycopg, boto3, anthropic, seleniumbase,
  sentence_transformers, etc.

## Patrones / decisiones

- **Adapter** es el patrón rector de toda la capa.
- Cada adaptador implementa un port; si no implementa un port, probablemente no debería estar aquí.
- Config (claves, hosts, modelos) entra por inyección desde `interface`, leída de `.env`
  vía pydantic-settings. La infraestructura no lee el `.env` directamente.

## Para conservar

Cambiar de proveedor/DB/scraper debe afectar **solo** su subcarpeta, nunca `application` ni
`domain`. Si un cambio de tecnología obliga a tocar el núcleo, el port estaba mal diseñado.
