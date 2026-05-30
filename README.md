# Sistema RAG BBVA Colombia

Asistente conversacional sobre información pública de `bbva.com.co`. El flujo completo es:
scraping, almacenamiento crudo y limpio, chunking, embeddings locales, búsqueda en pgvector,
respuesta con LLM multi-proveedor, memoria por sesión y analítica del histórico.

## Requisitos

- Docker y Docker Compose.
- Una clave de LLM para respuestas reales. Para el camino recomendado:
  `GOOGLE_API_KEY` con `MODEL_PROVIDER=google`.
- Opcional: Ollama local si se quiere usar `MODEL_PROVIDER=ollama` (en Docker usar
  `OLLAMA_HOST=http://host.docker.internal:11434`).

## Arranque Rápido

1. Crear `.env` desde el ejemplo y llenar al menos la clave del proveedor elegido:

```bash
cp .env.example .env
```

2. Levantar todo con un comando:

```bash
docker compose up --build
```

3. Abrir la UI:

- Streamlit: http://localhost:8501
- API FastAPI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

4. Ingestar contenido de BBVA:

```bash
docker compose exec app bbva-ingest --max-pages 25
```

5. Consultar métricas del histórico:

```bash
docker compose exec app bbva-analytics
```

## Configuración

Variables principales en `.env`:

- `MODEL_PROVIDER`: `google`, `anthropic`, `bedrock` u `ollama`.
- `PROVIDER_FALLBACK_ORDER`: orden de fallback, por ejemplo `google,anthropic,ollama`.
- `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`, `OLLAMA_HOST`: credenciales/conexión.
- `EMBEDDING_MODEL` y `EMBEDDING_DIM`: por defecto MiniLM multilingual de 384 dimensiones.
- `TOP_K`, `RERANK_ENABLED`, `RERANK_MODEL`: recuperación y reranking.
- `N_HISTORY_MESSAGES`: ventana de memoria por sesión.
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `SCRAPE_BASE_URL`: ingesta.

## Uso De La API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué productos ofrece BBVA Colombia?"}'
```

La respuesta incluye `session_id`, `content` y `sources`. Reusar el `session_id` mantiene
memoria conversacional con los últimos `N_HISTORY_MESSAGES`.

## Arquitectura

El proyecto usa un monolito modular con Clean Architecture/Hexagonal:

- `domain`: entidades puras (`Document`, `Chunk`, `ChatSession`, `ChatMessage`).
- `application`: ports, casos de uso y `PromptBuilder`.
- `infrastructure`: adaptadores para scraping, embeddings, pgvector, retrieval y LLMs.
- `interface`: FastAPI, Streamlit, CLI y composition root.

pgvector se eligió porque resuelve búsqueda vectorial y persistencia conversacional en el
mismo PostgreSQL, es self-hosted, demostrable con Docker y evita depender de un servicio SaaS.

## Patrones De Diseño

- Factory Method: `LLMFactory` instancia Google, Anthropic, Bedrock u Ollama por env.
- Strategy: `DenseRetrieval` y `RerankRetrieval` se intercambian con `RERANK_ENABLED`.
- Adapter: infraestructura adapta SDKs/DB/SeleniumBase a ports del núcleo.
- Repository: `PgVectorKnowledgeRepository` y `PgChatMemoryRepository`.
- Builder: `PromptBuilder` arma prompt defensivo con contexto y fuentes.
- Decorator: `CircuitBreakerLLM` envuelve cualquier proveedor LLM.
- Chain of Responsibility: `FallbackChainLLM` intenta proveedores en orden hasta responder.

Descartados por proporción: Prototype, Flyweight, Bridge, Composite, Interpreter, Visitor,
Memento, Mediator, State, Command, Template, Proxy, Iterator y Object Pool.

## Analítica

`bbva-analytics` recorre el histórico real y reporta:

- total de sesiones,
- total de mensajes,
- promedio de mensajes por sesión,
- fuentes más citadas por respuestas del asistente.

También está disponible por REST en `GET /analytics`.

## Pruebas

```bash
python -m pytest tests/l1
```

L2 con Ragas queda como evaluación ligera opt-in:

```bash
RUN_RAGAS_L2=1 python -m pytest tests/l2
```

## Limitaciones Y Supuestos

- El scraping de sitios bancarios puede ser bloqueado por WAF/Cloudflare; se usa SeleniumBase
  UC y se documenta cualquier bloqueo operativo.
- Sin `GOOGLE_API_KEY` u otra credencial válida, `/health` puede responder pero `/chat`
  devolverá error claro de proveedor no disponible.
- El índice usa `VECTOR(384)` para el modelo por defecto; cambiar dimensión exige reindexar.
- La evaluación L2 está preparada, pero se deja opt-in para no requerir credenciales en cada run.

## Futuras Mejoras

- Re-scraping programado con frescura de documentos.
- Autenticación de usuarios y control de sesiones.
- Observabilidad centralizada y métricas de latencia por proveedor.
- Evaluación CI con umbrales Ragas y dataset más grande.
- Retrieval híbrido BM25+denso.
