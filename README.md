# Sistema RAG BBVA Colombia

Asistente conversacional para consultar información pública de
`https://www.bbva.com.co/` mediante RAG (Retrieval-Augmented Generation). El proyecto
cubre el ciclo completo solicitado en la prueba técnica: scraping web, almacenamiento de
datos crudos y limpios, vectorización, búsqueda semántica, respuesta con LLM, memoria por
sesión y analítica del histórico.

La solución prioriza tres atributos de calidad propios del contexto de entrega:
demostrabilidad, mantenibilidad y tiempo de implementación. Por eso se implementa como un
monolito modular con arquitectura hexagonal, levantable con Docker en un solo comando, y
con adaptadores intercambiables para proveedores LLM, retrieval y persistencia.

## Tabla de contenido

- [Alcance funcional](#alcance-funcional)
- [Inicio Rápido](#inicio-rápido)
- [Uso del sistema](#uso-del-sistema)
- [Arquitectura](#arquitectura)
- [Casos de Uso y Flujos](#casos-de-uso-y-flujos)
- [Decisiones Técnicas](#decisiones-técnicas)
- [Modelos locales y observabilidad](#modelos-locales-y-observabilidad)
- [Patrones aplicados](#patrones-aplicados)
- [Alternativas evaluadas](#alternativas-evaluadas)
- [Configuración](#configuración)
- [API y CLI](#api-y-cli)
- [Pruebas y Validación](#pruebas-y-validación)
- [Limitaciones y Evolución](#limitaciones-y-evolución)
- [Versionado](#versionado)

## Alcance funcional

| Requisito | Implementación |
|---|---|
| Scraping del sitio BBVA Colombia | `SeleniumBase` en modo UC sobre páginas públicas de `bbva.com.co`, con semillas, profundidad y filtros configurables. |
| Datos crudos y limpios | Store-and-Forward en `data/raw` y `data/clean`. |
| Vectorización e índice | Embeddings locales CPU con `sentence-transformers` y búsqueda en PostgreSQL + pgvector. |
| Interfaz conversacional | Streamlit como UI, consumiendo FastAPI por HTTP. |
| Memoria por ID | Sesiones UUID persistidas en PostgreSQL y ventana configurable `N_HISTORY_MESSAGES`. |
| Dockerización | `docker compose up --build` levanta PostgreSQL/pgvector, FastAPI y Streamlit. |
| Patrones de diseño | Factory, Strategy, Adapter, Repository, Builder, Decorator y Chain of Responsibility. |
| Analítica histórica | Pestaña visual en Streamlit, endpoint `GET /analytics` y CLI `bbva-analytics`. |
| Trazabilidad RAG | `/chat` expone ranking, distancia, similitud y preview de chunks recuperados. |
| Observabilidad de chat | `/chat` expone latencias por etapa, proveedor y estado de cache; Streamlit las muestra por respuesta. |
| Retrieval híbrido | Estrategia `dense` por defecto y `hybrid` opcional con BM25 PostgreSQL + pgvector. |
| Cache controlada | Cache persistente de embeddings y cache opt-in de respuestas con TTL. |
| Frescura de ingesta | Registro de páginas scrapeadas para saltar reindexado fresco/sin cambios. |
| Reranker bonus | `RerankRetrieval` con Cross-Encoder, activable por `RERANK_ENABLED`. |
| Manejo de errores bonus | Fallback multi-proveedor, Circuit Breaker y handlers globales HTTP. |
| Configuración externa bonus | `.env` para proveedores, modelos, chunking, memoria, DB y retrieval. |
| Calidad V&V | Pruebas separadas en verificación y validación: unit, integration, architecture, system, performance, resilience, persistence y RAG quality. |

## Inicio Rápido

### Requisitos previos

- Docker y Docker Compose.
- Una credencial de LLM para respuestas reales. Camino recomendado:
  `MODEL_PROVIDER=google` con `GOOGLE_API_KEY`.
- Opcional: servidor Ollama local si se quiere usar `MODEL_PROVIDER=ollama`.

### Ejecución desde cero

1. Clonar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd PruebaTecnica
```

2. Crear archivo de entorno:

```bash
cp .env.example .env
```

3. Configurar al menos un proveedor LLM. Ejemplo recomendado:

```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=tu_clave
GOOGLE_MODEL=gemini-2.5-flash
PROVIDER_FALLBACK_ORDER=google,anthropic,ollama
```

4. Levantar todo con Docker:

```bash
docker compose up --build
```

5. Abrir las interfaces:

- Streamlit: http://localhost:8501
- Swagger/OpenAPI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

6. Ingestar contenido del sitio:

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
```

Para una validación rápida:

```bash
docker compose exec app bbva-ingest --max-pages 3
```

Para una ingesta más representativa del sitio sin volverla agresiva:

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
```

## Uso del sistema

### Chat

La pestaña **Chat** permite hacer preguntas sobre la información indexada de BBVA
Colombia. Cada respuesta incluye fuentes cuando el contexto recuperado las soporta.
Además, cada respuesta nueva puede desplegar una traza de retrieval con ranking, URL,
distancia pgvector, similitud aproximada, score de reranker cuando aplica y preview del
chunk usado.

Cada respuesta también incluye un panel de observabilidad con latencia total, retrieval,
LLM, persistencia, proveedor usado y estado de cache. Estas métricas son locales al
request; no requieren Prometheus ni un servicio externo para ser útiles durante la prueba.

El sistema crea una sesión UUID en la primera pregunta. En preguntas posteriores,
Streamlit reutiliza ese `session_id`; el backend recupera los últimos
`N_HISTORY_MESSAGES` mensajes de la misma sesión y los envía al LLM junto con el contexto
RAG.

### Conversaciones

El panel lateral muestra conversaciones persistidas. Cada entrada incluye un título
derivado de la primera pregunta y el número de mensajes registrados. Al seleccionar una
conversación, Streamlit carga sus mensajes desde:

```text
GET /sessions/{session_id}/messages
```

### Analítica

La pestaña **Analítica** muestra observabilidad del MVP:

- total de sesiones,
- total de mensajes,
- promedio de mensajes por sesión,
- fuentes más citadas,
- gráfico de citas por fuente.
- conversaciones recientes.

Estas métricas se calculan desde el histórico persistido; no son contadores en memoria.
También están disponibles por CLI y API.

## Arquitectura

El proyecto usa un monolito modular con Clean Architecture / Hexagonal:

```text
            interface ─┐
                       ├─► application ─► domain
        infrastructure ┘
```

### Capas

- `domain`: entidades puras (`Document`, `Chunk`, `ChatSession`, `ChatMessage`).
- `application`: casos de uso, ports y `PromptBuilder`.
- `infrastructure`: adaptadores para scraping, embeddings, pgvector, retrieval y LLMs.
- `interface`: FastAPI, Streamlit, CLI, analítica y composition root.

### Estructura principal

```text
src/
  domain/
  application/
    ports/
    use_cases/
    prompt_builder.py
  infrastructure/
    scraping/
    embeddings/
    persistence/
    retrieval/
    llm/
  interface/
    api/
      routers/
      schemas.py
      errors.py
      dependencies.py
      app.py
    streamlit_app/
      app.py
      api_client.py
      components.py
      state.py
    cli.py
    analytics.py
specs/
tests/
  verification/
    unit/
    integration/
    architecture/
  validation/
    system/
    rag_quality/
    performance/
    resilience/
    persistence/
docker-compose.yml
Dockerfile
CHANGELOG.md
```

### Estilos arquitectónicos elegidos

- **Monolito modular:** reduce fricción operativa y permite entregar un MVP demostrable.
- **Arquitectura en capas / hexagonal:** protege el núcleo de frameworks y SDKs externos.
- **Microkernel/plugin como criterio de extensibilidad:** proveedores LLM y estrategias de
  retrieval son intercambiables por configuración.
- **REST:** FastAPI expone el motor y Streamlit actúa como cliente.
- **EDA-lite in-process:** la ingesta es un pipeline secuencial dentro del proceso:
  `scrape -> clean -> chunk -> embed -> index`.

## Casos de Uso y Flujos

### CU-01: Ingesta de Conocimiento

```text
bbva-ingest
  -> SeleniumBaseScraper
  -> TrafilaturaCleaner
  -> TextChunker
  -> SentenceTransformerEmbedder
  -> PgVectorKnowledgeRepository
```

Resultado:

- HTML crudo en `data/raw`.
- Texto limpio en `data/clean`.
- Chunks indexados en `document_chunks`.
- Índice HNSW sobre `VECTOR(384)`.
- Registro de frescura en `scraped_pages` para saltar páginas recientes sin cambios.
- Crawl acotado por `SCRAPE_MAX_PAGES`, `SCRAPE_MAX_DEPTH`, semillas iniciales, prefijos
  permitidos y patrones excluidos.

El scraper no intenta recorrer todo internet ni todo el sitio bancario. Parte de semillas
de alto valor (`home`, `personas`, `empresas`), prioriza páginas de productos/servicios,
filtra archivos y páginas legales repetitivas, y conserva límites explícitos para mantener
la prueba reproducible.

### CU-02: Consulta RAG

```text
pregunta
  -> embedding de la query
  -> retrieval top-K en pgvector (dense o hybrid)
  -> rerank opcional
  -> PromptBuilder
  -> LLM multi-proveedor
  -> respuesta con fuentes
```

Si no se recupera contexto suficiente, el caso de uso responde que no encontró
información confiable en el corpus, evitando inventar.

La cache de embeddings está activa por defecto para no recalcular vectores repetidos. La
cache de respuestas queda apagada por defecto porque durante evaluación conviene observar
cambios de corpus y de configuración; puede activarse con TTL cuando se prioriza latencia.

### CU-03: Memoria Conversacional

```text
session_id
  -> chat_sessions
  -> chat_messages
  -> últimos N mensajes
  -> prompt del LLM
```

La relación es lineal: una sesión contiene muchos mensajes. No se implementa árbol de
ramas conversacionales porque el requerimiento pide memoria por ID y ventana N, no
bifurcación de hilos.

### CU-04: Analítica Histórica

```text
chat_sessions + chat_messages.sources
  -> AnalyticsUseCase
  -> GET /analytics
  -> Streamlit Analítica / bbva-analytics
```

Las fuentes citadas por respuestas del asistente se persisten para alimentar métricas de
impacto y trazabilidad.

## Decisiones Técnicas

| Decisión | Razón |
|---|---|
| PostgreSQL + pgvector | Unifica vectores, memoria conversacional y analítica en una sola base self-hosted. Evita depender de un SaaS vectorial y simplifica Docker. |
| HNSW + similitud coseno | Buena relación entre velocidad y calidad para búsqueda semántica aproximada. |
| `sentence-transformers` local CPU | Reduce costo y dependencia externa para embeddings. El modelo multilingual MiniLM de 384 dimensiones es suficiente para el corpus de la prueba. |
| Retrieval híbrido opt-in | BM25 rescata coincidencias lexicales importantes y pgvector aporta similitud semántica; se activa con `RETRIEVAL_MODE=hybrid` para comparar sin romper el default. |
| Gemini como proveedor recomendado | Permite inferencia real sin GPU local. Ollama queda soportado para ejecución local, pero no es el camino por defecto en CPU. |
| Modelos locales para embedding y reranking | Se ejecutan en CPU para reducir costo y dependencia externa en recuperación. La generación queda en proveedores LLM configurables porque exige mayor calidad conversacional. |
| Multi-proveedor LLM | El core no queda atado a un SDK. Google, Anthropic, Bedrock y Ollama implementan el mismo port. |
| Fallback + Circuit Breaker | Aumenta resiliencia ante credenciales faltantes, timeouts o caídas de proveedor. |
| Estado compartido controlado | El LLM se instancia una vez en el Composition Root, pero la observabilidad de proveedor se mantiene por contexto de ejecución y el Circuit Breaker protege su estado interno. |
| Cache de embeddings activa | Reduce trabajo repetido en CPU y mantiene los resultados persistidos por modelo/texto. |
| Cache de respuestas opt-in | Mejora latencia cuando el corpus está estable, pero se desactiva por defecto para no ocultar cambios durante evaluación. |
| Scraping profundo acotado | Aumenta cobertura con semillas y profundidad, pero mantiene límites de páginas, dominio, prefijos y exclusiones para cuidar tiempo de ejecución y respeto al sitio. |
| Frescura de scraping | Evita reindexar páginas frescas e idénticas; conserva un CLI manual y deja scheduler externo como decisión operacional. |
| FastAPI + Streamlit | FastAPI deja contrato REST verificable; Streamlit ofrece UI funcional y rápida para la prueba. |
| Reranker opt-in | Mejora relevancia, pero consume CPU; por eso se activa con `RERANK_ENABLED=true`. Puede envolver retrieval denso o híbrido sin perder la trazabilidad previa. |
| Pruebas V&V | Verificación para construcción correcta y validación para atributos de ejecución: sistema, performance, resiliencia, persistencia y calidad RAG. |

## Modelos locales y observabilidad

### Modelos locales

La recuperación semántica se apoya en modelos locales ejecutados en CPU:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` para embeddings locales CPU.
- Dimensión `384`, alineada con `VECTOR(384)` en pgvector.
- Embeddings normalizados para búsqueda por distancia coseno.
- `cross-encoder/ms-marco-MiniLM-L-6-v2` como reranker opcional con `RERANK_ENABLED=true`.

La generación de respuesta queda en proveedores LLM configurables (`google`, `anthropic`,
`bedrock`, `ollama`) porque esa etapa exige mayor calidad conversacional y porque el
fallback multi-proveedor es parte del diseño. Un generador local queda como evolución
posible si el entorno objetivo dispone de GPU o de un modelo con latencia aceptable.

### Observabilidad de retrieval

Además de logs estructurados con `structlog`, el contrato `POST /chat` devuelve
`retrieval_trace`, una lista de chunks usados para construir la respuesta:

- `rank`: posición final del chunk.
- `source_url`: fuente pública recuperada.
- `distance`: distancia coseno reportada por pgvector.
- `similarity_score`: aproximación `1 - distance` para lectura humana.
- `rerank_score`: score del Cross-Encoder cuando el reranker está activo.
- `dense_score`, `bm25_score`, `hybrid_score`: scores opcionales cuando se usa
  `RETRIEVAL_MODE=hybrid`.
- `content_preview`: fragmento breve para auditoría visual.

Streamlit muestra esta traza en un panel desplegable por respuesta. Esto permite revisar
si el sistema respondió con evidencia real del índice y no solo con texto generado.
Si se configura `RETRIEVAL_MODE=hybrid` y `RERANK_ENABLED=true`, la traza muestra primero
los scores denso/BM25/híbrido y luego el `rerank_score` aplicado sobre esos candidatos.

### Observabilidad de latencias

`POST /chat` agrega el objeto opcional `observability` sin romper el contrato previo:

- `total_latency_ms`: duración total del request de chat.
- `retrieval_latency_ms`: tiempo de búsqueda de contexto.
- `prompt_latency_ms`: tiempo de armado del prompt.
- `llm_latency_ms`: tiempo de generación.
- `persistence_latency_ms`: tiempo de escritura de memoria/fuentes.
- `provider`: proveedor LLM efectivo o `answer_cache`.
- `cache_hit`: indica si la respuesta vino de cache.

Streamlit muestra estos datos en un expander por respuesta. Para esta versión se eligió
observabilidad embebida y logs estructurados porque es suficiente para demostrar el MVP
sin introducir Prometheus, OpenTelemetry o infraestructura adicional.

## Patrones aplicados

### Patrones de Diseño

| Patrón | Dónde | Propósito |
|---|---|---|
| Factory Method | `infrastructure/llm/factory.py` | Crear proveedor LLM según `MODEL_PROVIDER`. |
| Strategy | `infrastructure/retrieval/` | Intercambiar `DenseRetrieval`, `HybridRetrieval` y `RerankRetrieval`. |
| Adapter | `infrastructure/` | Adaptar SeleniumBase, SDKs LLM, psycopg y pgvector a ports del núcleo. |
| Repository | `application/ports` + `infrastructure/persistence` | Ocultar SQL y exponer persistencia como colecciones de dominio. |
| Builder | `application/prompt_builder.py` | Construir system prompt con contexto, fuentes y reglas anti-alucinación. |
| Decorator | `infrastructure/llm/circuit_breaker.py` | Envolver proveedores LLM con Circuit Breaker. |
| Chain of Responsibility | `infrastructure/llm/fallback_chain.py` | Intentar proveedores en orden hasta obtener respuesta. |

### Patrones arquitectónicos

- **DTO:** modelos Pydantic en `src/interface/api/schemas.py`.
- **Store-and-Forward:** datos crudos y limpios antes de indexar.
- **Circuit Breaker:** aislamiento de fallos en proveedores externos.
- **Log Aggregation:** persistencia de fuentes citadas para analítica.
- **Cache-aside:** cache persistente de embeddings y respuestas sin mezclarla con el caso de uso.
- **Composition Root:** `src/interface/container.py` ensambla dependencias.

### Patrones evaluados y no incluidos

No se implementaron API Gateway, Service Registry, Service Discovery, Load Balancer,
Webhooks, SSO ni microservicios porque pertenecen a escenarios de distribución y escala
que no aportan al MVP solicitado. También se descartaron Prototype, Flyweight, Bridge,
Composite, Interpreter, Visitor, Memento, Mediator, State, Command, Template Method,
Proxy, Iterator y Object Pool porque no resolvían un problema concreto del alcance actual.

## Alternativas evaluadas

| Alternativa | Decisión |
|---|---|
| Microservicios / SOA | Descartado para el MVP. Aumenta complejidad de despliegue, red, observabilidad distribuida y manejo de fallos. |
| LangChain / LangGraph como orquestador | No se usó como core para mantener visibles los patrones requeridos y conservar Clean Architecture. |
| `langchain-text-splitters` | Usado solo para chunking, una utilidad acotada que no captura la arquitectura. |
| LlamaIndex / Haystack | Descartados por la misma razón que LangChain como orquestador: acoplarían el núcleo al framework. |
| LiteLLM | Descartado porque el Factory + fallback propio son parte del entregable técnico y dan control fino del Circuit Breaker. |
| Pinecone / Qdrant / Weaviate / Chroma | Descartados para esta entrega porque pgvector cubre vectores, memoria y analítica con menos infraestructura. |
| requests + BeautifulSoup / Scrapy | Descartados por menor resiliencia frente al WAF de un sitio bancario moderno. |
| Embeddings por API | Descartados para la ruta base por costo y dependencia externa; embeddings locales cumplen el requerimiento. |

## Configuración

Variables principales en `.env`:

| Variable | Uso |
|---|---|
| `MODEL_PROVIDER` | Proveedor activo: `google`, `anthropic`, `bedrock`, `ollama`. |
| `PROVIDER_FALLBACK_ORDER` | Orden de fallback entre proveedores. |
| `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`, `OLLAMA_HOST` | Credenciales/conexión por proveedor. |
| `GOOGLE_MODEL`, `ANTHROPIC_MODEL`, `BEDROCK_MODEL_ID`, `OLLAMA_MODEL` | Modelo específico por proveedor. |
| `EMBEDDING_MODEL`, `EMBEDDING_DIM` | Modelo y dimensión de embeddings. |
| `TOP_K` | Número de chunks recuperados. |
| `RETRIEVAL_MODE` | Estrategia principal: `dense` o `hybrid`. |
| `HYBRID_BM25_WEIGHT`, `HYBRID_DENSE_WEIGHT` | Pesos para fusionar score lexical y semántico. |
| `RERANK_ENABLED`, `RERANK_MODEL` | Activación y modelo de reranking. |
| `EMBEDDING_CACHE_ENABLED` | Activa cache persistente de embeddings. |
| `ANSWER_CACHE_ENABLED`, `ANSWER_CACHE_TTL_SECONDS` | Cache opt-in de respuestas y TTL. |
| `N_HISTORY_MESSAGES` | Ventana de memoria conversacional. |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Parámetros de chunking. |
| `SCRAPE_BASE_URL` | URL base de scraping. |
| `SCRAPE_START_URLS` | Semillas iniciales separadas por coma para cubrir secciones relevantes temprano. |
| `SCRAPE_MAX_PAGES`, `SCRAPE_MAX_DEPTH` | Límites de cobertura del crawl. |
| `SCRAPE_ALLOWED_PREFIXES`, `SCRAPE_EXCLUDE_PATTERNS` | Política de URLs permitidas/excluidas. |
| `SCRAPE_FRESHNESS_HOURS`, `RESCRAPE_CHANGED_ONLY` | Política de frescura y detección de cambios. |
| `PG_*` | Conexión PostgreSQL. |

## API y CLI

### API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de API, DB y proveedor configurado. |
| `POST` | `/chat` | Pregunta/respuesta RAG con `session_id` opcional, fuentes, `retrieval_trace` y `observability`. |
| `GET` | `/sessions` | Lista conversaciones persistidas. |
| `GET` | `/sessions/{session_id}/messages` | Carga mensajes de una conversación. |
| `GET` | `/analytics` | Métricas históricas del chat. |

Ejemplo:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué información general aparece sobre BBVA Colombia para empresas?"}'
```

Para continuar una conversación:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "UUID_EXISTENTE", "message": "¿Y qué más dice sobre eso?"}'
```

### CLI

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
docker compose exec app bbva-ingest --max-pages 3 --freshness-hours 24
docker compose exec app bbva-ingest --max-pages 3 --force-refresh
docker compose exec app bbva-analytics
```

## Pruebas y Validación

Suite completa:

```bash
docker compose exec app pytest tests
```

Verificación: unitarios, integración y arquitectura.

```bash
docker compose exec app pytest tests/verification
```

Validación ligera: sistema, performance, resiliencia, persistencia y estructura del dataset
RAG.

```bash
docker compose exec app pytest tests/validation
```

Evaluación RAG con Ragas real, opt-in por credenciales:

```bash
docker compose exec -e RUN_RAGAS_L2=1 app pytest tests/validation/rag_quality
```

Validaciones realizadas durante el desarrollo:

- PostgreSQL + pgvector con extensión `vector`, tabla `document_chunks`, HNSW y
  `VECTOR(384)`.
- Ingesta real de páginas de BBVA con persistencia cruda/limpia y chunks indexados.
- Contrato REST validado con FastAPI/TestClient.
- Chat real con Gemini y fuentes.
- Memoria por `session_id` persistida y visible en Streamlit.
- Analítica visible por Streamlit, API y CLI.
- Trazabilidad de retrieval visible por respuesta en Streamlit.
- Observabilidad de latencias visible por respuesta en Streamlit y en el contrato REST.
- Cache de embeddings, cache opt-in de respuestas y freshness de ingesta cubiertos por tests.
- Retrieval híbrido BM25 + denso cubierto por strategy/unit y contrato extendido.
- Docker Compose levantando app + DB en un comando.

## Limitaciones y Evolución

### Limitaciones actuales

- El scraping de sitios bancarios puede verse afectado por WAF o cambios de estructura del
  sitio. SeleniumBase UC reduce el riesgo, pero no elimina la dependencia externa.
- La cobertura del scraping es intencionalmente acotada. Se priorizan páginas públicas de
  productos/servicios en `personas` y `empresas`; aumentar `SCRAPE_MAX_PAGES` y
  `SCRAPE_MAX_DEPTH` mejora cobertura a cambio de tiempo de ejecución y más exposición a WAF.
- La dimensión `VECTOR(384)` está ligada al modelo de embeddings configurado por defecto;
  cambiar de modelo requiere reindexar.
- Ollama está soportado, pero en entornos sin GPU puede tener latencia alta.
- El reranker está apagado por defecto para mantener buena latencia en CPU.
- No se implementan autenticación, autorización ni SSO; son extensiones naturales para un
  entorno corporativo real.
- La evaluación L2 es opt-in para no exigir credenciales ni costo en cada ejecución.
- La ingesta aplica frescura y detección de cambios, pero se ejecuta manualmente; no hay
  scheduler externo incluido.
- La cache de respuestas está apagada por defecto para evitar esconder cambios del corpus
  durante revisión técnica.

### Futuras mejoras

- Autenticación y autorización por usuario interno.
- Scheduler externo para invocar `bbva-ingest` por cron, GitHub Actions o un orquestador.
- Métricas productivas con Prometheus/OpenTelemetry si el sistema pasa a operación continua.
- Umbrales Ragas más estrictos en CI cuando existan credenciales y dataset curado por negocio.
- Despliegue distribuido solo si el volumen operativo lo justifica.

## Versionado

El proyecto usa versionado semántico para los hitos de entrega:

- `v1.0.0`: MVP RAG completo.
- `v1.1.0`: mejora menor con dashboard visual de analítica.
- `v1.2.0`: trazabilidad de retrieval y refactor modular de Streamlit.
- `v1.3.0`: calidad de software con V&V, observabilidad, cache, retrieval híbrido y frescura de ingesta.

Los cambios relevantes se documentan en [CHANGELOG.md](CHANGELOG.md).

## Historial de trabajo

El repositorio sigue GitFlow:

- `main`: rama estable de releases.
- `develop`: integración.
- `feature/*`: desarrollo incremental.

Los merges se hacen con `--no-ff` y commits semánticos para que el historial muestre una
progresión técnica revisable, alineada con el criterio de evaluación de la prueba.
