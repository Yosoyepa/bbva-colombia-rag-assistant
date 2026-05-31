# API, CLI y configuracion

## API

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/health` | Estado de API, DB y proveedor configurado. |
| `POST` | `/chat` | Pregunta/respuesta RAG con `session_id`, fuentes, trace y observabilidad. |
| `GET` | `/sessions` | Lista conversaciones persistidas. |
| `GET` | `/sessions/{session_id}/messages` | Carga mensajes de una conversacion. |
| `GET` | `/analytics` | Metricas historicas del chat. |

Ejemplo:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Que productos ofrece BBVA Colombia para empresas?"}'
```

Continuar conversacion:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "UUID_EXISTENTE", "message": "Y que mas dice sobre eso?"}'
```

## CLI

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
docker compose exec app bbva-ingest --max-pages 3 --freshness-hours 24
docker compose exec app bbva-ingest --max-pages 3 --force-refresh
docker compose exec app bbva-analytics
```

## Variables principales

| Variable | Uso |
|---|---|
| `MODEL_PROVIDER` | Proveedor activo: `google`, `anthropic`, `bedrock`, `ollama`. |
| `PROVIDER_FALLBACK_ORDER` | Orden de fallback. |
| `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`, `OLLAMA_HOST` | Credenciales/conexion por proveedor. |
| `GOOGLE_MODEL`, `ANTHROPIC_MODEL`, `BEDROCK_MODEL_ID`, `OLLAMA_MODEL` | Modelo especifico por proveedor. |
| `EMBEDDING_MODEL`, `EMBEDDING_DIM` | Modelo y dimension de embeddings. |
| `TOP_K` | Chunks recuperados. |
| `RETRIEVAL_MODE` | `dense` o `hybrid`. |
| `HYBRID_BM25_WEIGHT`, `HYBRID_DENSE_WEIGHT` | Pesos de fusion lexical/semantica. |
| `RERANK_ENABLED`, `RERANK_MODEL` | Activacion y modelo de reranking. |
| `EMBEDDING_CACHE_ENABLED` | Cache persistente de embeddings. |
| `ANSWER_CACHE_ENABLED`, `ANSWER_CACHE_TTL_SECONDS` | Cache opt-in de respuestas y TTL. |
| `N_HISTORY_MESSAGES` | Ventana de memoria conversacional. |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Parametros de chunking. |
| `SCRAPE_START_URLS` | Semillas iniciales. |
| `SCRAPE_MAX_PAGES`, `SCRAPE_MAX_DEPTH` | Limites del crawl. |
| `SCRAPE_ALLOWED_PREFIXES`, `SCRAPE_EXCLUDE_PATTERNS` | Politica de URLs. |
| `SCRAPE_FRESHNESS_HOURS`, `RESCRAPE_CHANGED_ONLY` | Frescura y deteccion de cambios. |
| `PG_*` | Conexion PostgreSQL. |
