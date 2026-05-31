# Decisiones, patrones y alternativas

## Decisiones tecnicas

| Decision | Razon |
|---|---|
| PostgreSQL + pgvector | Unifica vectores, memoria y analitica en una sola base self-hosted. |
| HNSW + similitud coseno | Buen balance entre velocidad y calidad para busqueda semantica aproximada. |
| Embeddings locales CPU | Evitan costo por embedding y mantienen la ruta base reproducible. |
| Retrieval hibrido opt-in | BM25 rescata coincidencias lexicales y pgvector aporta similitud semantica. |
| Gemini recomendado | Permite inferencia real sin GPU local. |
| Multi-proveedor LLM | El core no queda atado a un SDK. |
| Fallback + Circuit Breaker | Mejora resiliencia frente a credenciales faltantes, timeouts o caidas. |
| Cache de embeddings activa | Reduce recalculo local de vectores. |
| Cache de respuestas opt-in | Mejora latencia con corpus estable, pero no oculta cambios durante evaluacion. |
| Scraping profundo acotado | Aumenta cobertura sin volver agresiva la ingesta contra el sitio. |
| FastAPI + Streamlit | Contrato REST verificable y UI funcional de baja friccion. |
| Pruebas V&V | Separa construccion correcta de atributos de ejecucion del chatbot. |

## Patrones de diseno

| Patron | Donde | Uso |
|---|---|---|
| Factory Method | `src/infrastructure/llm/factory.py` | Crear proveedores LLM segun configuracion. |
| Strategy | `src/infrastructure/retrieval/` | Intercambiar dense, hybrid y rerank. |
| Adapter | `src/infrastructure/` | Adaptar SeleniumBase, SDKs, psycopg y pgvector a ports. |
| Repository | `src/application/ports` + `src/infrastructure/persistence` | Encapsular persistencia. |
| Builder | `src/application/prompt_builder.py` | Construir system prompt con contexto y fuentes. |
| Decorator | `src/infrastructure/llm/circuit_breaker.py` | Envolver proveedores con Circuit Breaker. |
| Chain of Responsibility | `src/infrastructure/llm/fallback_chain.py` | Intentar proveedores en orden. |

## Patrones arquitectonicos

- **DTO:** Pydantic en `src/interface/api/schemas.py`.
- **Store-and-Forward:** persistencia de crudo y limpio antes de indexar.
- **Circuit Breaker:** aislamiento de fallos externos.
- **Log Aggregation:** fuentes citadas persistidas para analitica.
- **Cache-aside:** cache persistente sin mezclarla con casos de uso.
- **Composition Root:** `src/interface/container.py` ensambla dependencias.

## Alternativas evaluadas

| Alternativa | Decision |
|---|---|
| Microservicios / SOA | Descartado para no aumentar complejidad de despliegue y observabilidad distribuida. |
| LangChain / LangGraph como orquestador | No se uso como core para mantener visibles los patrones requeridos y el control de capas. |
| LlamaIndex / Haystack | Descartados por el acoplamiento de arquitectura para el alcance actual. |
| LiteLLM | Descartado porque Factory + fallback propio son parte del entregable tecnico. |
| Pinecone / Qdrant / Weaviate / Chroma | pgvector cubre vectores, memoria y analitica con menos infraestructura. |
| requests + BeautifulSoup / Scrapy | Menor resiliencia frente a un sitio bancario moderno. |
| Embeddings por API | Mayor costo y dependencia externa; embeddings locales son suficientes para esta prueba. |

## Alcance enterprise evaluado y no incluido

Estas capacidades son relevantes para una plataforma corporativa de GenAI/LLMOps, pero no
se implementaron en el MVP porque la prueba solicitaba un sistema RAG ejecutable en pocos
dias, con Docker, scraping, memoria, analitica y patrones de diseno. Se documentan porque
fueron consideradas durante el diseno y marcan una ruta razonable de evolucion.

| Capacidad | Decision y fundamento |
|---|---|
| Autenticacion, autorizacion y controles de acceso | No se incluyeron porque la prueba evalua ejecucion local y no define usuarios, roles ni integracion corporativa. La frontera REST queda lista para agregar OAuth2/OIDC, JWT, RBAC y politicas por endpoint en una version enterprise. |
| Gobernanza formal de prompts | El prompt vive en `PromptBuilder`, con reglas defensivas y versionable por Git. No se agrego registry ni historial de cambios en DB porque el MVP usa un prompt controlado. En produccion convendria un prompt registry con version, aprobador, fecha, metricas y rollback. |
| Monitoreo productivo Prometheus/OpenTelemetry | La version actual expone observabilidad embebida por respuesta y logs estructurados, suficiente para demo y diagnostico local. En operacion continua se agregarian trazas OpenTelemetry, metricas Prometheus, dashboards Grafana y alertas por latencia/error/provider. |
| Dataset Ragas amplio y umbrales estrictos | Ragas queda opt-in y el dataset es intencionalmente pequeno para no bloquear ejecucion local ni exigir credenciales. Para robustez real se requiere un dataset curado por negocio, 50-100+ preguntas, gold answers, umbrales en CI y revision periodica. |
| Metricas de costo por inferencia/token | No se normalizaron porque cada proveedor reporta usage/costos de forma diferente y algunos caminos locales no tienen costo por token. La evolucion seria capturar tokens por adapter, asociar tabla de precios por modelo y persistir costo estimado por request. |
| A/B testing real | No hay trafico multiusuario ni hipotesis de producto que justifique experimentacion. Una version productiva podria enrutar sesiones entre variantes de prompt/retrieval/modelo, persistir cohortes y medir calidad, latencia, costo y feedback. |
| Pipeline batch/streaming productivo | La ingesta es CLI manual con frescura y deteccion de cambios, suficiente para la prueba. En produccion se moveria a scheduler/orquestador, jobs batch, colas o streaming segun frecuencia de cambio y criticidad del corpus. |
| Data lineage formal y model registry | No se entrenan modelos propios; se usan modelos externos/locales configurados por entorno. Para gobierno ML se agregarian MLflow/model registry, model cards, version de embeddings, version de corpus, lineage de documentos y trazabilidad de datasets. |
| Privacidad/PII profunda | El corpus base es informacion publica de BBVA Colombia y no se procesa informacion bancaria privada. Aun asi, un entorno corporativo deberia agregar redaccion/deteccion de PII en preguntas, retencion configurable, cifrado, auditoria, DLP y politicas de no almacenamiento para datos sensibles. |

## Patrones no incluidos

Prototype, Flyweight, Bridge, Composite, Interpreter, Visitor, Memento, Mediator, State,
Command, Template Method, Proxy, Iterator y Object Pool no se implementaron porque no
resolvían un problema concreto del alcance actual.
