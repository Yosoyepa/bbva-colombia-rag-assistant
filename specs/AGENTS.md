# AGENTS.md — `specs/`

Spec-Driven Development. Ver [contexto global](../AGENTS.md).

## Responsabilidad

Contener una **spec por caso de uso**, con criterios de aceptación verificables, escrita
**antes** de implementar la feature. La implementación se valida contra ellos.

- `SPEC-CU01-ingestion.md` — scraping → crudo → limpio → chunk → embed → pgvector.
- `SPEC-CU02-query.md` — embeber query → top-K → (rerank) → prompt → respuesta anclada (no alucina).
- `SPEC-CU03-memory.md` — sesión por ID, persistencia, ventana de N mensajes (N por env).
- `SPEC-CU04-analytics.md` — recorrer histórico → métricas de impacto.

## Convenciones

- Cada spec: objetivo, actores, precondiciones, flujo, **criterios de aceptación** (checklist
  verificable) y casos borde. Trazable al requisito original en `prueba_tecnica_IAML.md`.
- Una spec describe **comportamiento observable**, no implementación.

## Para conservar

Si el comportamiento cambia, primero se actualiza la spec, luego el código. Las specs son la
fuente de verdad de "qué debe hacer" y alimentan los tests L2.
