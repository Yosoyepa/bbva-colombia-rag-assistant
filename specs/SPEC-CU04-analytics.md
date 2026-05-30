# SPEC-CU04 — Analítica del histórico

**Traza a:** `prueba_tecnica_IAML.md` línea 27 (recorrer histórico para extraer métricas y valores de impacto).
**Capas:** `interface/analytics` (`bbva-analytics`) → `application/use_cases/AnalyticsUseCase` → `infrastructure/persistence`.

## Objetivo
Recorrer el histórico de conversaciones persistido y derivar métricas que demuestren el
impacto/uso del asistente.

## Actor
Operador/analista que ejecuta el CLI `bbva-analytics`.

## Precondiciones
- Hay sesiones y mensajes en la DB (CU-03 en uso).

## Flujo principal
1. `AnalyticsUseCase.execute()` recorre sesiones y mensajes.
2. Agrega métricas y produce `AnalyticsReport`.

## Criterios de aceptación
- [ ] Reporta `total_sessions` y `total_messages` consistentes con la DB.
- [ ] Reporta `avg_messages_per_session`.
- [ ] Reporta `top_sources`: fuentes (source_url) más citadas en las respuestas.
- [ ] El comando `bbva-analytics` imprime el reporte de forma legible.
- [ ] La métrica se deriva del **histórico real**, no de datos sintéticos.

## Casos borde
- Histórico vacío → reporte con ceros, sin error.

## Nota de diseño
Alimentado por **Log Aggregation** (logging estructurado por interacción) + el histórico
persistido. Métricas adicionales (latencias, frecuencia temporal) son extensión natural.
