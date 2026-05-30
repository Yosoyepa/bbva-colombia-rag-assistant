# Sistema RAG BBVA Colombia

Asistente conversacional sobre informacion publica de `bbva.com.co`. El sistema cubre el
flujo pedido en la prueba tecnica: scraping, almacenamiento crudo y limpio, chunking,
embeddings locales, indexacion en pgvector, chat con memoria por sesion, multi-proveedor
LLM con fallback y analitica del historico.

La prioridad de diseno fue entregar un sistema demostrable con Docker en poco tiempo, sin
perder separacion de responsabilidades. Por eso se eligio un monolito modular con Clean
Architecture/Hexagonal: suficiente para mantener proveedores intercambiables y tests
claros, pero sin el costo operativo de microservicios para una prueba de 2-3 dias.

## Requisitos Previos

- Docker y Docker Compose.
- Una clave de LLM para respuestas reales. Camino recomendado: `GOOGLE_API_KEY` con
  `MODEL_PROVIDER=google`.
- Opcional: Ollama local si se quiere `MODEL_PROVIDER=ollama`. En Docker usar
  `OLLAMA_HOST=http://host.docker.internal:11434`.

## Arranque Desde Cero

1. Clonar el repositorio y entrar al proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd PruebaTecnica
```

2. Crear `.env` desde el ejemplo y configurar al menos un proveedor LLM:

```bash
cp .env.example .env
```

Para el camino recomendado:

```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=tu_clave
GOOGLE_MODEL=gemini-2.5-flash
PROVIDER_FALLBACK_ORDER=google,anthropic,ollama
```

3. Levantar base de datos, API y UI con un comando:

```bash
docker compose up --build
```

4. Abrir las interfaces:

- Streamlit: http://localhost:8501
- API FastAPI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

5. Ingestar contenido de BBVA:

```bash
docker compose exec app bbva-ingest --max-pages 25
```

Para una validacion rapida se puede usar `--max-pages 3`.

6. Consultar metricas del historico:

```bash
docker compose exec app bbva-analytics
```

## Uso

La forma principal de uso es Streamlit en http://localhost:8501. La UI consume la API
FastAPI; no llama directamente al motor RAG. Esto deja un contrato REST verificable y
permite probar el nucleo sin depender de la interfaz visual.

Ejemplo REST:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Que informacion general aparece sobre BBVA Colombia para empresas?"}'
```

La respuesta incluye:

- `session_id`: identificador de conversacion.
- `content`: respuesta generada.
- `sources`: URLs usadas como contexto.

Reusar el `session_id` mantiene memoria conversacional con los ultimos
`N_HISTORY_MESSAGES`.

## Que Se Implemento

| Requisito de la prueba | Estado | Implementacion |
|---|---:|---|
| Scraping de `bbva.com.co` | Incluido | `SeleniumBase` en modo UC y almacenamiento en `data/raw`. |
| Datos crudos y limpios | Incluido | Store-and-Forward en disco: raw HTML + texto limpio. |
| Vectorizacion e indice | Incluido | `sentence-transformers` CPU + PostgreSQL `pgvector` con HNSW. |
| Interfaz conversacional | Incluido | Streamlit consumiendo FastAPI. |
| Historial por ID y ventana N | Incluido | Persistencia en PostgreSQL y `N_HISTORY_MESSAGES` por env. |
| Docker con un comando | Incluido | `docker compose up --build` levanta DB + app. |
| >=3 patrones de diseno | Incluido | Factory, Strategy, Adapter, Repository, Builder, Decorator, CoR. |
| Analitica historica | Incluido | CLI `bbva-analytics` y `GET /analytics`. |
| Bonus reranker | Incluido | `RerankRetrieval` con Cross-Encoder, activable por env. |
| Bonus manejo de errores | Incluido | HTTP errors claros, fallback y circuit breaker. |
| Bonus config externa | Incluido | `.env` con proveedores, modelos, chunking, memoria y DB. |

## Enfoque Arquitectonico

El enfoque final sigue `PLAN_REAL.md`:

- **Monolito modular:** maximiza demostrabilidad y reduce friccion de despliegue.
- **Clean Architecture / Hexagonal:** `domain`, `application`, `infrastructure` e
  `interface` separan reglas de negocio de frameworks y SDKs.
- **Microkernel/plugin como lente:** LLMs, retrieval y scraping se seleccionan por
  configuracion y adaptadores, no por cambios al core.
- **REST:** FastAPI expone el motor RAG; Streamlit queda como cliente.
- **EDA-lite in-process:** la ingesta es un pipeline por etapas
  `scrape -> clean -> chunk -> embed -> index`, sin broker externo.
- **Cliente-servidor:** navegador/Streamlit/API/PostgreSQL, suficiente para el alcance.

Se descartaron microservicios y SOA para esta entrega porque anaden despliegue,
descubrimiento, balanceo, observabilidad distribuida y fallos de red que no mejoran la
evaluacion principal del RAG. La arquitectura deja puertos claros para evolucionar hacia
servicios separados si el volumen o el equipo lo justifican.

## Estructura

```text
src/
  domain/            # entidades puras: Document, Chunk, ChatSession, ChatMessage
  application/
    ports/           # contratos del nucleo
    use_cases/       # IngestDataUseCase, AnswerQueryUseCase, AnalyticsUseCase
    prompt_builder.py
  infrastructure/
    scraping/        # SeleniumBase + limpieza + chunking
    embeddings/      # sentence-transformers CPU
    persistence/     # PostgreSQL + pgvector + memoria
    retrieval/       # DenseRetrieval / RerankRetrieval
    llm/             # Google, Anthropic, Bedrock, Ollama, fallback, circuit breaker
  interface/
    api/             # FastAPI
    streamlit_app.py # UI
    cli.py           # bbva-ingest
    analytics.py     # bbva-analytics
specs/               # CU-01 a CU-04 con criterios de aceptacion
tests/l1             # tests unitarios
tests/l2             # Ragas ligero opt-in
```

## Decisiones Tecnicas Y Viabilidad

| Decision | Por que se eligio |
|---|---|
| PostgreSQL + pgvector | Unifica vectores, memoria conversacional y analitica en una sola DB self-hosted. Cumple Docker 1 comando y evita depender de un SaaS vectorial. |
| Embeddings locales CPU | Reducen costo y dependencia externa. El modelo multilingual MiniLM usa 384 dimensiones, suficiente para el corpus publico de la prueba. |
| Gemini como proveedor recomendado | Permite respuestas reales sin GPU local. Ollama queda soportado, pero no es el camino por defecto porque el entorno sin GPU puede ser lento. |
| Multi-proveedor real | El core no queda atado a un SDK. Se puede cambiar entre Google, Anthropic, Bedrock y Ollama por `.env`. |
| Fallback + Circuit Breaker | Si un proveedor falla o no tiene credenciales, el sistema intenta el siguiente y evita insistir sobre proveedores rotos. |
| Reranker opt-in | Mejora relevancia, pero consume CPU. Por eso `RERANK_ENABLED=false` por defecto y se activa cuando se quiera priorizar calidad sobre latencia. |
| FastAPI + Streamlit | Streamlit da UI rapida; FastAPI deja contrato REST validable y separa interfaz de motor. |
| Tests L1 + L2 ligero | Proporcional al tiempo. L1 cubre logica determinista; L2 con Ragas queda opt-in por costo/credenciales. |

## Patrones

### Patrones de diseno implementados

- **Factory Method:** `LLMFactory` crea `GeminiClient`, `AnthropicClient`,
  `BedrockClient` u `OllamaClient` segun `.env`.
- **Strategy:** `DenseRetrieval` y `RerankRetrieval` implementan la misma estrategia de
  recuperacion para el caso de uso de respuesta.
- **Adapter:** los SDKs externos, SeleniumBase, psycopg y pgvector viven en
  `infrastructure` y se adaptan a ports del nucleo.
- **Repository:** `PgVectorKnowledgeRepository` y `PgChatMemoryRepository` implementan
  persistencia sin filtrar SQL al caso de uso.
- **Builder:** `PromptBuilder` ensambla prompt defensivo, contexto, fuentes y ventana de
  memoria.
- **Decorator:** `CircuitBreakerLLM` envuelve proveedores LLM sin modificar clientes.
- **Chain of Responsibility:** `FallbackChainLLM` prueba proveedores en orden hasta
  obtener respuesta.

### Patrones arquitectonicos aplicados

- **DTO:** modelos Pydantic en la frontera REST.
- **Store-and-Forward:** raw + clean en disco antes de indexar.
- **Circuit Breaker:** resiliencia ante proveedores externos.
- **Log Aggregation:** logging estructurado y persistencia de fuentes para CU-04.

### Patrones evaluados y no incluidos

No se incluyeron API Gateway, Service Registry/Discovery, Load Balancer, SSO, Webhooks ni
microservicios porque no aportan al alcance evaluado y aumentan la complejidad operativa.
Prototype, Flyweight, Bridge, Composite, Interpreter, Visitor, Memento, Mediator, State,
Command, Template, Proxy, Iterator y Object Pool se descartaron por no resolver un
problema real del sistema en esta escala.

## Configuracion

Variables principales:

- `MODEL_PROVIDER`: `google`, `anthropic`, `bedrock` u `ollama`.
- `PROVIDER_FALLBACK_ORDER`: orden de fallback, por ejemplo `google,anthropic,ollama`.
- `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`, `OLLAMA_HOST`: credenciales/conexion.
- `GOOGLE_MODEL`, `ANTHROPIC_MODEL`, `BEDROCK_MODEL_ID`, `OLLAMA_MODEL`: modelo por
  proveedor.
- `EMBEDDING_MODEL` y `EMBEDDING_DIM`: por defecto MiniLM multilingual de 384 dimensiones.
- `TOP_K`, `RERANK_ENABLED`, `RERANK_MODEL`: recuperacion y reranking.
- `N_HISTORY_MESSAGES`: ventana de memoria por sesion.
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `SCRAPE_BASE_URL`: ingesta.
- `PG_*`: conexion PostgreSQL.

## API

- `GET /health`: estado de API, DB y proveedor configurado.
- `POST /chat`: pregunta/respuesta con memoria opcional por `session_id`.
- `GET /analytics`: metricas del historico.

Ejemplo con memoria:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "UUID_EXISTENTE", "message": "Y que mas dice sobre eso?"}'
```

## Analitica

`bbva-analytics` recorre el historico persistido y reporta:

- total de sesiones,
- total de mensajes,
- promedio de mensajes por sesion,
- fuentes mas citadas.

La misma informacion esta disponible en `GET /analytics`. El objetivo es demostrar el
requisito CU-04 sin introducir una plataforma externa de observabilidad.

## Pruebas Y Validacion

Tests unitarios:

```bash
docker compose exec app pytest tests/l1
```

Suite completa local:

```bash
docker compose exec app pytest tests
```

Evaluacion L2 ligera con Ragas:

```bash
docker compose exec -e RUN_RAGAS_L2=1 app pytest tests/l2
```

Durante el desarrollo se valido el flujo end-to-end con Docker:

- pgvector activo con extension, tabla `document_chunks`, HNSW y `VECTOR(384)`.
- ingesta real de paginas de BBVA con archivos crudos/limpios y chunks indexados.
- `/chat` respondiendo con Gemini y fuentes.
- `/analytics` reportando sesiones, mensajes y fuentes citadas.

## Limitaciones Y Supuestos

- El scraping de sitios bancarios puede ser bloqueado por WAF/Cloudflare. Se usa
  SeleniumBase UC, pero el bloqueo operativo sigue siendo un riesgo externo.
- Sin una clave valida de LLM, `/health` puede estar OK y `/chat` fallara con error claro
  de proveedor no disponible.
- `VECTOR(384)` esta acoplado al modelo de embeddings por defecto; cambiar dimensiones
  exige reindexar.
- El reranker esta incluido pero apagado por defecto para no penalizar latencia en CPU.
- No se implemento autenticacion de usuarios, SSO ni autorizacion por roles; quedan fuera
  del alcance de la prueba.
- La evaluacion L2 es opt-in para no exigir credenciales ni costo en cada ejecucion.
- No hay scheduler de re-scraping; la ingesta se ejecuta manualmente con `bbva-ingest`.

## Futuras Mejoras

- Re-scraping programado con frescura de documentos y deteccion de cambios.
- Autenticacion, autorizacion y separacion de sesiones por usuario real.
- Observabilidad centralizada con latencia por etapa, proveedor y query.
- Dataset de evaluacion mas grande con umbrales Ragas en CI.
- Retrieval hibrido BM25 + denso.
- Cache de respuestas y embeddings para reducir costo y latencia.
- API Gateway y despliegue por servicios solo si el volumen operacional lo justifica.

## Historial De Trabajo

El repositorio usa GitFlow: `develop` como rama de integracion, `feature/*` para cambios
importantes, merges `--no-ff` y release final en `main` con tag `v1.0.0`. Esto responde al
requisito de historial visible y progresion logica, no un unico commit final.
