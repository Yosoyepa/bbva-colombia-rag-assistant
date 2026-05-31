# AGENTS.md — Sistema RAG BBVA

> **`AGENTS.md` y `CLAUDE.md` son idénticos.** `CLAUDE.md` lo lee Claude Code; `AGENTS.md`
> es la convención abierta para cualquier otro agente/herramienta. Si editas uno, copia al otro
> (`cp AGENTS.md CLAUDE.md`). Este archivo es el **contexto global**; el detalle de cada capa
> vive en el `AGENTS.md` de su carpeta (ver §8).

---

## 1. Qué es este proyecto

Sistema **RAG (Retrieval-Augmented Generation)** que responde preguntas sobre información
**pública de BBVA Colombia** (bbva.com.co). Flujo: *scraping → almacenar crudo+limpio →
chunk → embed → indexar en pgvector → chat con memoria por sesión → analítica del histórico*.
Todo levantable con **un comando Docker**. Es una prueba técnica MLE/AI; los atributos de
calidad de primera clase incluyen **time-to-deliver y demostrabilidad**, no solo
mantenibilidad. La planeación viva (estrategia, descartes, fases) está en `PLAN_REAL.md`
(local, fuera de git) y los casos de uso formales en `specs/`.

## 2. Estilo arquitectónico

**Monolito modular + Hexagonal (Ports & Adapters) + lente Microkernel/plugin** para
proveedores (LLM/retriever/scraper como plugins seleccionables por env) + **pipeline de
ingesta EDA-lite in-process** + **REST (FastAPI)** entre la UI (Streamlit) y el motor.
Microservicios/SOA se **rechazan conscientemente** (premature distribution daña
deployability y time-to-deliver); quedan como evolución futura con las costuras ya limpias.

## 3. La regla de dependencia (innegociable)

```
            interface ─┐
                       ├─► application ─► domain
        infrastructure ┘
```

Las dependencias apuntan **hacia adentro**. Concretamente:

- `domain/` **no importa nada** fuera de la stdlib. Cero `pydantic`, `psycopg`, SDKs, etc.
- `application/` solo importa `domain` y sus propios **ports** (interfaces abstractas).
  Nunca importa `infrastructure` ni `interface`.
- `infrastructure/` implementa los ports de `application` (son **Adapters**). Puede importar
  `domain` y `application.ports`, nunca `interface`.
- `interface/` (API, CLI, Streamlit, analytics) orquesta: construye las implementaciones de
  infraestructura y las inyecta en los casos de uso (**Composition Root**).

Si una capa necesita algo de una capa externa, se define un **port** en `application` y la
capa externa lo implementa. Esto es lo que mantiene el dominio testeable y los proveedores
intercambiables.

## 4. Patrones de diseño curados (set, no pattern-stuffing)

Se implementan los que resuelven un problema real y se **documentan los descartados**.

| Patrón | Dónde vive | Para qué |
|---|---|---|
| **Factory Method** | `infrastructure/llm/` (`LLMFactory`) | instanciar proveedor LLM según `MODEL_PROVIDER` |
| **Strategy** | `infrastructure/retrieval/` | `DenseRetrieval` / `RerankRetrieval` intercambiables |
| **Adapter** | todo `infrastructure/` | adaptar SeleniumBase/psycopg/SDKs a los ports |
| **Repository** | `application/ports/` + `infrastructure/persistence/` | persistencia de chunks y memoria |
| **Builder** | `application` / `infrastructure/llm` (`PromptBuilder`) | ensamblar system + historial N + contexto + query |
| **Decorator** | `infrastructure/llm/` | envolver el LLM con retry/logging/**Circuit Breaker** |
| **Chain of Responsibility** | `infrastructure/llm/` | cadena de fallback entre proveedores |

**Descartados (documentar en README/docs):** Prototype, Flyweight, Bridge, Composite, Interpreter,
Visitor, Memento, Mediator, State, Command, Template, Proxy, Iterator, Object Pool.
**Patrones arquitectónicos aplicados:** Store-and-Forward (crudo+limpio en disco), DTO,
Circuit Breaker, Log Aggregation (logging estructurado → analítica CU-04).

## 5. Convenciones de trabajo

- **GitFlow**: `main` = base estable/releases · `develop` = integración · `feature/*` desde
  develop. Merges `--no-ff` a develop; al final `develop → main` + tag `v1.0.0`.
- **Commits semánticos** (Conventional Commits): `feat:`, `fix:`, `chore:`, `test:`, `docs:`,
  `refactor:`. Usar el comando **`/git-commit`** para cada cambio importante (trazabilidad).
- **Autor de los commits**: `Yosoyepa <jandradeu@unal.edu.co>`.
- **RTK obligatorio** para todo comando de CLI/git (`rtk git ...`, `rtk ls`, `rtk read`,
  `rtk proxy <cmd>` para lo no cubierto).
- **Spec-Driven**: antes de codificar una feature se escribe/lee su spec en `specs/` con
  criterios de aceptación verificables.

## 6. Stack

Python ≥3.11 · SeleniumBase UC (scraping) · trafilatura (limpieza) · sentence-transformers
(embeddings CPU) + Cross-Encoder (rerank) · PostgreSQL + pgvector (HNSW) · FastAPI + Streamlit
· Anthropic/Google/Bedrock/Ollama (multi-proveedor) · pydantic-settings · structlog · Docker.

## 7. Config externalizada (`.env`)

`MODEL_PROVIDER`, claves por proveedor (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `AWS_*`),
`LLM_MODEL`, `EMBEDDING_MODEL`, `N_HISTORY_MESSAGES`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`,
`RERANK_ENABLED`, `PROVIDER_FALLBACK_ORDER`, `PG_*`, `SCRAPE_BASE_URL`. Nada de secretos en código.

## 8. Mapa de `AGENTS.md` por carpeta (patrón spec-y-negocio por carpeta)

**Cada carpeta tiene su propio `AGENTS.md`** con la decisión y la lógica de negocio de esa
capa: responsabilidad, qué puede/no puede importar, patrones que aplica y reglas a conservar.
**Antes de tocar código en una carpeta, lee su `AGENTS.md`.** Este archivo raíz solo referencia;
el "cómo se adapta cada capa" vive ahí.

- [`src/AGENTS.md`](src/AGENTS.md) — visión de las 4 capas y la regla de dependencia.
- [`src/domain/AGENTS.md`](src/domain/AGENTS.md) — entidades puras, cero dependencias externas.
- [`src/application/AGENTS.md`](src/application/AGENTS.md) — orquestación, ports y casos de uso.
- [`src/application/ports/AGENTS.md`](src/application/ports/AGENTS.md) — contratos (interfaces) del núcleo.
- [`src/application/use_cases/AGENTS.md`](src/application/use_cases/AGENTS.md) — Ingest, Answer, Analytics.
- [`src/infrastructure/AGENTS.md`](src/infrastructure/AGENTS.md) — adaptadores; implementan los ports.
- [`src/infrastructure/persistence/AGENTS.md`](src/infrastructure/persistence/AGENTS.md) — pgvector + memoria.
- [`src/infrastructure/llm/AGENTS.md`](src/infrastructure/llm/AGENTS.md) — Factory + proveedores + fallback.
- [`src/infrastructure/embeddings/AGENTS.md`](src/infrastructure/embeddings/AGENTS.md) — embeddings CPU.
- [`src/infrastructure/scraping/AGENTS.md`](src/infrastructure/scraping/AGENTS.md) — SeleniumBase UC + cleaner.
- [`src/infrastructure/retrieval/AGENTS.md`](src/infrastructure/retrieval/AGENTS.md) — Dense/Rerank (Strategy).
- [`src/interface/AGENTS.md`](src/interface/AGENTS.md) — Composition Root: API, CLI, UI, analytics.
- [`src/interface/api/AGENTS.md`](src/interface/api/AGENTS.md) — FastAPI: contrato REST.
- [`specs/AGENTS.md`](specs/AGENTS.md) — specs por caso de uso (criterios de aceptación).
- [`tests/AGENTS.md`](tests/AGENTS.md) — niveles L1 (unit) y L2 (Ragas).
- [`data/AGENTS.md`](data/AGENTS.md) — Store-and-Forward: crudo y limpio en disco.
- [`docs/AGENTS.md`](docs/AGENTS.md) — documentación extendida y decisiones de entrega.

## 9. Comandos frecuentes

```bash
docker compose up                 # levanta pgvector + app (1 comando)
bbva-ingest                       # CLI: scrape → clean → chunk → embed → index
bbva-analytics                    # reporte de métricas del histórico (CU-04)
rtk pytest tests/l1               # tests unitarios
```
