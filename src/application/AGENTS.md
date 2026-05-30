# AGENTS.md — `src/application/`

Capa de orquestación. Ver [contexto global](../../AGENTS.md).

## Responsabilidad

Contener la **lógica de aplicación** (casos de uso) y los **contratos** (ports) que el
núcleo necesita del mundo exterior. Es el "qué hace el sistema", independiente de "con qué".

- `ports/` — interfaces abstractas (ABC): qué necesita la aplicación (persistir, generar, embeber, recuperar).
- `use_cases/` — flujos de negocio que coordinan dominio + ports: Ingest, Answer, Analytics.

## Regla de dependencia

- Importa **solo** de `domain` y de `application.ports`.
- **Nunca** importa `infrastructure` ni `interface`. No conoce psycopg, FastAPI, SeleniumBase
  ni ningún SDK. Recibe las implementaciones por **inyección de dependencias** (constructor).

## Patrones / decisiones

- **Dependency Inversion**: los use_cases dependen de abstracciones (ports), no de concretos.
- Un use_case recibe sus colaboradores ya construidos (los arma el Composition Root en `interface`).
- Los use_cases son donde vive la lógica anémica del dominio (orquestación, no las entidades).

## Para conservar

Si un caso de uso necesita una capacidad nueva del exterior, **primero define el port**
aquí, luego impleméntalo en `infrastructure`. Nunca al revés.
