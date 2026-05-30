# AGENTS.md — `src/interface/api/`

Capa REST (FastAPI). Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Exponer el motor RAG por HTTP para que Streamlit (u otros clientes) lo consuman:

- `POST /chat` — recibe `{session_id, message}`, ejecuta `AnswerQueryUseCase`, responde
  texto anclado + fuentes (soporta streaming).
- `GET /health` — readiness/liveness (incluye DB y disponibilidad del proveedor LLM).
- `GET/POST /sessions` — gestión de sesiones de chat.
- `GET /analytics` — métricas del histórico (CU-04).

## Regla de dependencia

- Importa casos de uso de `application` y los recibe ya ensamblados (DI vía dependencias de
  FastAPI). No instancia adaptadores ni habla SQL.

## Patrones / decisiones

- **DTO**: modelos Pydantic de request/response; mapear a entidades, no exponer entidades crudas.
- **Contrato estable**: la API es la frontera pública; cambios rompen a Streamlit → versionar con cuidado.
- Manejo de errores HTTP coherente (502 si todos los proveedores caen tras el Circuit Breaker,
  503 si la DB no responde, 422 en payload inválido).

## Para conservar

`/health` debe reflejar dependencias reales para que `docker compose` y los checks
end-to-end sean fiables.
