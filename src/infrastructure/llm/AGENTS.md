# AGENTS.md — `src/infrastructure/llm/`

Proveedores LLM, Factory y fallback. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Dar al núcleo un `LargeLanguageModel` uniforme, independiente del proveedor:

- `LLMFactory.create()` — Factory Method: instancia el cliente concreto por nombre.
- `LLMFactory.create_with_fallback()` — arma la cadena: activo + respaldos, cada uno con breaker.
- `AnthropicClient` / `BedrockClient` / `GeminiClient` / `OllamaClient` — adaptan cada SDK al port.
- `FallbackChainLLM` (Chain of Responsibility) + `CircuitBreakerLLM` (Decorator) ante fallos.

## Regla de dependencia

- Implementa `application.ports.LargeLanguageModel`. Importa los SDKs (anthropic, boto3,
  google-generativeai, ollama). No conoce FastAPI/Streamlit.

## Patrones / decisiones

- **Factory Method** — selección de proveedor por env; añadir un proveedor = nueva clase + alta en el Factory.
- **Chain of Responsibility** — `PROVIDER_FALLBACK_ORDER`: si el activo falla, pasa al siguiente.
- **Decorator** — `CircuitBreakerLLM` envuelve cualquier cliente con retry + logging estructurado +
  **Circuit Breaker** (CLOSED→OPEN tras N fallos, falla rápido, HALF_OPEN tras `reset_timeout`).
- **Regla de negocio**: el fallback es transparente para el caso de uso; este pide "genera" y
  recibe respuesta o un error claro, sin saber qué backend respondió.

## Para conservar

El port es agnóstico: nada específico de un proveedor debe filtrarse a `application`.
Claves y nombres de modelo llegan por inyección desde `interface` (nunca leer `.env` aquí).
