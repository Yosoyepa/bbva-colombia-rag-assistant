# AGENTS.md — `src/` (raíz de capas)

Contexto global y convenciones en el [`AGENTS.md` raíz](../AGENTS.md). Aquí: cómo se
organizan las 4 capas y la única regla que las gobierna.

## Responsabilidad

Contener todo el código de producción, separado en 4 capas de Clean Architecture / Hexagonal:

- `domain/` — el corazón: entidades de negocio puras.
- `application/` — orquestación: casos de uso + ports (interfaces).
- `infrastructure/` — adaptadores: implementaciones concretas de los ports (DB, LLM, web).
- `interface/` — puntos de entrada: FastAPI, CLI, Streamlit, analytics (Composition Root).

## Regla de dependencia (innegociable)

Las flechas apuntan **hacia adentro**: `interface`/`infrastructure` → `application` → `domain`.

- `domain` no importa de ninguna otra capa ni de librerías externas.
- `application` solo conoce `domain` y sus propios `ports`.
- `infrastructure` implementa `application.ports` y puede usar `domain`.
- `interface` ensambla infraestructura e inyecta en los casos de uso.

Cualquier dependencia "hacia afuera" desde el núcleo se expresa como un **port** en
`application/ports/` que la infraestructura implementa (Dependency Inversion).

## Para conservar

- Una carpeta = una capa = una responsabilidad. No mezclar (p. ej. SQL en `domain`).
- Cada subcarpeta tiene su `AGENTS.md`: léelo antes de modificarla.
