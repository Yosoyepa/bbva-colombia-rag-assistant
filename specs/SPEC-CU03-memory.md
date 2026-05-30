# SPEC-CU03 — Memoria conversacional por sesión

**Traza a:** `prueba_tecnica_IAML.md` líneas 13, 22 (historial por ID, N mensajes configurable, persistencia).
**Capas:** `application/use_cases/AnswerQueryUseCase` → `infrastructure/persistence/PgChatMemoryRepository`.

## Objetivo
Recordar el contexto de mensajes previos dentro de una sesión identificada por ID,
inyectando los últimos N mensajes (N configurable) y **persistiendo** el historial.

## Actor
Usuario del chat (sesión identificada por `session_id`).

## Precondiciones
- Postgres arriba; `.env` con `N_HISTORY_MESSAGES`.

## Flujo principal
1. `get_or_create_session(session_id)` recupera o crea la sesión.
2. Antes de responder, `get_recent_messages(session_id, N_HISTORY_MESSAGES)` devuelve la ventana.
3. La ventana se inyecta en el prompt (CU-02), habilitando seguimiento anafórico.
4. Tras responder, `add_message` persiste el turno (user + assistant).

## Criterios de aceptación
- [ ] Pregunta de seguimiento ("¿y sus tasas?") se entiende usando el contexto previo.
- [ ] Reiniciar el cliente/pestaña y reusar el `session_id` recupera el historial (persistencia en DB).
- [ ] Cambiar `N_HISTORY_MESSAGES` cambia el tamaño de la ventana **sin redeploy** ni cambio de código.
- [ ] Mensajes persistidos con `role`, `content`, `created_at` y FK a la sesión.
- [ ] Dos `session_id` distintos no comparten historial (aislamiento).

## Casos borde
- `session_id` inexistente → se crea una sesión nueva, no error.
- Sesión con menos de N mensajes → se inyectan los que haya, sin relleno.
