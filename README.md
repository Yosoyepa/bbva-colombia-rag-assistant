# Sistema RAG BBVA Colombia

Asistente conversacional para consultar informacion publica de
`https://www.bbva.com.co/` mediante RAG. La solucion cubre el ciclo pedido en la
prueba tecnica: scraping web, almacenamiento crudo y limpio, vectorizacion, indice
vectorial, chat con memoria por sesion y analitica del historico.

El proyecto prioriza demostrabilidad, mantenibilidad y despliegue simple: corre con
Docker, usa PostgreSQL + pgvector como base self-hosted, expone FastAPI como contrato
REST y ofrece una UI Streamlit limpia para evaluacion.

## Contenido

- [Cumplimiento](#cumplimiento)
- [Inicio rapido](#inicio-rapido)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Patrones de diseno](#patrones-de-diseno)
- [Stack y decisiones](#stack-y-decisiones)
- [Pruebas](#pruebas)
- [Limitaciones](#limitaciones)
- [Documentacion extendida](#documentacion-extendida)

## Cumplimiento

| Requisito de la prueba | Implementacion |
|---|---|
| Web scraping de BBVA Colombia | SeleniumBase UC sobre paginas publicas, con crawl acotado por semillas, profundidad y filtros. |
| Datos crudos y limpios | Store-and-Forward en `data/raw` y `data/clean`. |
| Vectorizacion e indice | `sentence-transformers` local CPU + PostgreSQL/pgvector `VECTOR(384)` con HNSW. |
| Interfaz conversacional | Streamlit consume FastAPI por HTTP. |
| Historial por ID | Sesiones UUID persistidas en PostgreSQL; ventana `N_HISTORY_MESSAGES` configurable. |
| Docker con un comando | `docker compose up --build` levanta DB, API y UI. |
| Patrones de diseno | Factory, Strategy, Adapter, Repository, Builder, Decorator y Chain of Responsibility. |
| Analisis historico | Pestaña Analitica en Streamlit, `GET /analytics` y CLI `bbva-analytics`. |
| Configuracion externa | `.env` para proveedores, modelos, chunking, memoria, retrieval, scraping y DB. |
| Bonus reranker | Cross-Encoder opt-in con `RERANK_ENABLED=true`. |
| Bonus manejo de errores | Handlers globales HTTP, fallback multi-proveedor y Circuit Breaker. |

## Inicio rapido

### Requisitos

- Docker y Docker Compose.
- Una clave de LLM para respuestas reales. Ruta recomendada:
  `MODEL_PROVIDER=google` con `GOOGLE_API_KEY`.

### Levantar desde cero

```bash
git clone https://github.com/Yosoyepa/bbva-colombia-rag-assistant.git
cd bbva-colombia-rag-assistant
cp .env.example .env
```

Edita `.env` y configura al menos:

```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=tu_clave
GOOGLE_MODEL=gemini-2.5-flash
PROVIDER_FALLBACK_ORDER=google,anthropic,ollama
```

Levanta todos los servicios:

```bash
docker compose up --build
```

Abre:

- Streamlit: http://localhost:8501
- Swagger/OpenAPI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

Indexa contenido antes de preguntar:

```bash
docker compose exec app bbva-ingest --max-pages 40 --max-depth 3
```

Para una prueba rapida:

```bash
docker compose exec app bbva-ingest --max-pages 3
```

## Uso

### Chat

En la pestaña **Chat** escribe preguntas sobre informacion publica de BBVA Colombia.
Cada respuesta incluye fuentes, trazabilidad de retrieval y metricas de latencia cuando
aplican. Streamlit conserva el `session_id`, por lo que las siguientes preguntas usan los
ultimos `N_HISTORY_MESSAGES` mensajes de esa misma conversacion.

### Conversaciones

El panel lateral muestra conversaciones persistidas. Al seleccionar una sesion, la UI
carga el historico desde `GET /sessions/{session_id}/messages`.

### Analitica

La pestaña **Analitica** resume sesiones, mensajes, promedio de mensajes por sesion,
fuentes mas citadas y conversaciones recientes. Las metricas salen de PostgreSQL, no de
contadores en memoria.

## Arquitectura

El sistema es un monolito modular con Clean Architecture / Hexagonal:

```text
            interface ─┐
                       ├─► application ─► domain
        infrastructure ┘
```

- `domain`: entidades puras.
- `application`: casos de uso, ports y `PromptBuilder`.
- `infrastructure`: adaptadores de scraping, embeddings, pgvector, retrieval y LLMs.
- `interface`: FastAPI, Streamlit, CLI, analitica y composition root.

FastAPI y Streamlit se separan por REST para mantener un contrato verificable sin
introducir microservicios prematuros. El pipeline de ingesta es secuencial:

```text
scrape -> clean -> chunk -> embed -> index
```

Mas detalle: [docs/architecture.md](docs/architecture.md).

## Patrones de diseno

| Patron | Donde | Por que se eligio |
|---|---|---|
| Factory Method | `src/infrastructure/llm/factory.py` | Crear proveedores LLM segun `MODEL_PROVIDER` sin acoplar el caso de uso. |
| Strategy | `src/infrastructure/retrieval/` | Cambiar entre retrieval denso, hibrido y rerank sin tocar `AnswerQueryUseCase`. |
| Adapter | `src/infrastructure/` | Encapsular SeleniumBase, SDKs LLM, psycopg y pgvector detras de ports. |
| Repository | `src/application/ports` + `src/infrastructure/persistence` | Separar SQL/persistencia del nucleo de aplicacion. |
| Builder | `src/application/prompt_builder.py` | Construir prompts con contexto, fuentes e instrucciones defensivas. |
| Decorator | `src/infrastructure/llm/circuit_breaker.py` | Envolver proveedores con Circuit Breaker. |
| Chain of Responsibility | `src/infrastructure/llm/fallback_chain.py` | Probar proveedores en orden hasta obtener respuesta. |

Patrones y alternativas descartadas:
[docs/design-decisions.md](docs/design-decisions.md).

## Stack y decisiones

| Area | Eleccion | Justificacion breve |
|---|---|---|
| Lenguaje | Python 3.11+ | Ecosistema ML/RAG maduro y compatible con FastAPI/Streamlit. |
| Scraping | SeleniumBase UC + trafilatura | Mejor tolerancia a sitios modernos y limpieza de HTML robusta. |
| Vector DB | PostgreSQL + pgvector | Una sola base para vectores, memoria y analitica; self-hosted y Docker-friendly. |
| Embeddings | `sentence-transformers` local CPU | Sin costo por embedding y reproducible en entorno local. |
| LLM | Google, Anthropic, Bedrock, Ollama | Multi-proveedor con fallback; Gemini queda como ruta recomendada para demo. |
| UI/API | Streamlit + FastAPI | UI simple para evaluacion y contrato REST verificable. |
| Calidad | pytest + V&V + CI | Verificacion de construccion y validacion de atributos de ejecucion. |

Decisiones completas:
[docs/design-decisions.md](docs/design-decisions.md).

## Configuracion esencial

Variables principales:

| Variable | Uso |
|---|---|
| `MODEL_PROVIDER` | `google`, `anthropic`, `bedrock` u `ollama`. |
| `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`, `OLLAMA_HOST` | Credenciales/conexion por proveedor. |
| `N_HISTORY_MESSAGES` | Numero de mensajes previos enviados como memoria. |
| `TOP_K` | Chunks recuperados para responder. |
| `RETRIEVAL_MODE` | `dense` o `hybrid`. |
| `RERANK_ENABLED` | Activa Cross-Encoder reranker. |
| `SCRAPE_MAX_PAGES`, `SCRAPE_MAX_DEPTH` | Cobertura del scraping. |
| `PG_*` | Conexion PostgreSQL. |

Tabla completa y comandos:
[docs/api-and-cli.md](docs/api-and-cli.md).

## Pruebas

Suite completa:

```bash
docker compose exec app pytest tests
```

Verificacion: unitarios, integracion y arquitectura.

```bash
docker compose exec app pytest tests/verification
```

Validacion ligera: sistema, performance, resiliencia, persistencia y dataset RAG.

```bash
docker compose exec app pytest tests/validation
```

Evaluacion RAG con Ragas real, opt-in:

```bash
docker compose exec -e RUN_RAGAS_L2=1 app pytest tests/validation/rag_quality
```

Estrategia V&V completa:
[docs/testing-strategy.md](docs/testing-strategy.md).

## Limitaciones

- El scraping de un sitio bancario puede verse afectado por WAF o cambios de estructura.
- La cobertura se mantiene acotada para cuidar tiempo de ejecucion y reproducibilidad.
- Cambiar el modelo de embeddings implica reindexar porque pgvector usa `VECTOR(384)`.
- Ollama esta soportado, pero puede tener latencia alta sin GPU.
- Reranker y cache de respuestas son opt-in para no ocultar costos ni cambios durante
  evaluacion.
- No se incluyen autenticacion, autorizacion ni scheduler externo; son extensiones naturales
  para un entorno corporativo.
- Capacidades enterprise como gobernanza formal de prompts, monitoreo Prometheus/OpenTelemetry,
  metricas de costo por token, A/B testing, data lineage, model registry y controles profundos
  de privacidad/PII se evaluaron como evolucion, pero quedan fuera del MVP para mantener la
  entrega ejecutable y alineada con el alcance de la prueba. Ver fundamento en
  [docs/design-decisions.md](docs/design-decisions.md#alcance-enterprise-evaluado-y-no-incluido).

## Documentacion extendida

- [Arquitectura](docs/architecture.md)
- [Decisiones, patrones y alternativas](docs/design-decisions.md)
- [Ingesta, scraping y frescura](docs/ingestion-and-freshness.md)
- [Retrieval, reranking y cache](docs/retrieval-and-reranking.md)
- [Observabilidad y analitica](docs/observability-and-analytics.md)
- [API, CLI y configuracion](docs/api-and-cli.md)
- [Estrategia de pruebas V&V](docs/testing-strategy.md)
- [Changelog](CHANGELOG.md)

## Versionado e historial

El repositorio sigue GitFlow: `main` para releases, `develop` para integracion y
`feature/*` para incrementos. Los merges se hacen con `--no-ff` y commits semanticos para
mostrar una progresion logica del trabajo.

Hitos:

- `v1.0.0`: MVP RAG completo.
- `v1.1.0`: dashboard visual de analitica.
- `v1.2.0`: trazabilidad de retrieval y Streamlit modular.
- `v1.3.0`: V&V, observabilidad, cache, retrieval hibrido y frescura de ingesta.
- `v1.4.0`: entrega final con scraping profundo acotado, refinamientos SOLID, rerank sobre
  retrieval hibrido y README ejecutivo con documentacion extendida.
