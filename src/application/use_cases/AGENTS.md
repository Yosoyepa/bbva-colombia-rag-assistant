# AGENTS.md — `src/application/use_cases/`

Los flujos de negocio. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Orquestar dominio + ports para cumplir cada caso de uso de las `specs/`:

- `IngestDataUseCase` (CU-01) — scrape → clean → chunk → embed → persistir en el vector repo.
- `AnswerQueryUseCase` (CU-02) — embeber query → `RetrievalStrategy` top-K → construir prompt
  (con memoria) → `LargeLanguageModel` → respuesta **anclada** a fuentes (no alucinar).
- `AnalyticsUseCase` (CU-04) — recorrer el histórico → métricas de impacto.

## Regla de dependencia

- Importa `domain` y `application.ports`. **Nunca** infraestructura ni interface.
- Cada use_case recibe sus ports por constructor (DI). No instancia adaptadores concretos.

## Patrones / decisiones

- **Strategy** inyectada en `AnswerQueryUseCase` (`DenseRetrieval` vs `RerankRetrieval`).
- **Builder** (`PromptBuilder`) ensambla system defensivo + ventana de N mensajes + contexto
  recuperado + query del usuario.
- **Regla de negocio clave**: si el contexto recuperado no soporta la respuesta, el caso de
  uso debe producir un "no lo sé" en vez de inventar (anti-alucinación, verificable en specs).

## Para conservar

Toda la lógica de "cómo responde el asistente" vive aquí, no en la API ni en Streamlit.
La interface solo invoca el caso de uso y serializa el resultado.
