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

## Patrones no incluidos

Prototype, Flyweight, Bridge, Composite, Interpreter, Visitor, Memento, Mediator, State,
Command, Template Method, Proxy, Iterator y Object Pool no se implementaron porque no
resolvían un problema concreto del alcance actual.
