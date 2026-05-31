# Arquitectura

El sistema usa un monolito modular con Clean Architecture / Hexagonal. La decision evita
distribucion prematura y permite entregar un MVP demostrable con un solo comando Docker.

```text
            interface ─┐
                       ├─► application ─► domain
        infrastructure ┘
```

## Capas

| Capa | Responsabilidad |
|---|---|
| `domain` | Entidades puras: `Document`, `Chunk`, `ChatSession`, `ChatMessage`. |
| `application` | Casos de uso, ports y construccion del prompt. |
| `infrastructure` | Adaptadores para scraping, embeddings, persistencia, retrieval y LLMs. |
| `interface` | FastAPI, Streamlit, CLI, analitica y composition root. |

La regla de dependencia apunta hacia adentro. `domain` no importa frameworks. `application`
depende de ports, no de adaptadores. `interface/container.py` ensambla implementaciones y
las inyecta.

## Estructura principal

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
    streamlit_app/
    cli.py
    analytics.py
specs/
tests/
  verification/
  validation/
```

## Estilos elegidos

- **Monolito modular:** minimiza friccion operativa para una prueba de 2-3 dias.
- **Hexagonal:** proveedores externos quedan detras de ports.
- **Microkernel/plugin:** LLMs y estrategias de retrieval son intercambiables por entorno.
- **REST:** Streamlit consume FastAPI y no importa el motor directamente.
- **EDA-lite in-process:** la ingesta corre como pipeline secuencial local.

## Flujos principales

### CU-01: Ingesta

```text
bbva-ingest
  -> SeleniumBaseScraper
  -> TrafilaturaCleaner
  -> TextChunker
  -> SentenceTransformerEmbedder
  -> PgVectorKnowledgeRepository
```

### CU-02: Consulta RAG

```text
pregunta
  -> retrieval top-K
  -> rerank opcional
  -> PromptBuilder
  -> LLM con fallback
  -> respuesta con fuentes
```

### CU-03: Memoria

```text
session_id
  -> chat_sessions
  -> chat_messages
  -> ultimos N mensajes
  -> prompt del LLM
```

### CU-04: Analitica

```text
chat_sessions + chat_messages.sources
  -> AnalyticsUseCase
  -> GET /analytics
  -> Streamlit / bbva-analytics
```

## Decisiones de alcance

No se implementan microservicios, API Gateway, Service Registry, Service Discovery ni Load
Balancer. El sistema deja costuras limpias para escalar despues, pero el requerimiento
principal es demostrabilidad local y mantenibilidad del MVP.
