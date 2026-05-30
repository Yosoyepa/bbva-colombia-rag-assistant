"""LLMFactory (**Factory Method**) + ensamblado del fallback.

`create()` produce un proveedor concreto a partir de su nombre (Factory Method puro:
añadir proveedor = una clase + una rama). `create_with_fallback()` arma la **cadena
de responsabilidad**: coloca primero el proveedor activo, luego el resto de
`fallback_order` (deduplicado), envuelve cada uno en un **CircuitBreakerLLM**
(Decorator) y los compone en un `FallbackChainLLM`. Los proveedores sin credenciales
se omiten (se loguea) en vez de tumbar el arranque.
"""
from __future__ import annotations

import structlog

from src.application.ports import LargeLanguageModel
from src.infrastructure.llm.circuit_breaker import CircuitBreakerLLM
from src.infrastructure.llm.fallback_chain import FallbackChainLLM

log = structlog.get_logger(__name__)


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
        model: str,
        *,
        google_model: str = "",
        anthropic_model: str = "",
        ollama_model: str = "",
        google_api_key: str = "",
        anthropic_api_key: str = "",
        aws_access_key_id: str = "",
        aws_secret_access_key: str = "",
        aws_region: str = "us-east-1",
        bedrock_model_id: str = "",
        ollama_host: str = "",
    ) -> LargeLanguageModel:
        """Factory Method: instancia UN proveedor concreto por nombre."""
        provider = (provider or "").lower()
        if provider == "google":
            from src.infrastructure.llm.gemini_client import GeminiClient

            return GeminiClient(api_key=google_api_key, model=google_model or model)
        if provider == "anthropic":
            from src.infrastructure.llm.anthropic_client import AnthropicClient

            return AnthropicClient(api_key=anthropic_api_key, model=anthropic_model or model)
        if provider == "bedrock":
            from src.infrastructure.llm.bedrock_client import BedrockClient

            return BedrockClient(
                model_id=bedrock_model_id or model,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region=aws_region,
            )
        if provider == "ollama":
            from src.infrastructure.llm.ollama_client import OllamaClient

            return OllamaClient(host=ollama_host, model=ollama_model or model)
        raise ValueError(f"MODEL_PROVIDER desconocido: '{provider}'")

    @staticmethod
    def create_with_fallback(
        active_provider: str,
        fallback_order: list[str],
        model: str,
        *,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        **provider_kwargs,
    ) -> LargeLanguageModel:
        """Ensambla la cadena: [activo, *resto] → cada uno con Circuit Breaker."""
        # Orden: el proveedor activo primero, luego el resto del fallback (sin duplicar).
        order: list[str] = []
        for name in [active_provider, *fallback_order]:
            name = (name or "").lower()
            if name and name not in order:
                order.append(name)

        chain: list[LargeLanguageModel] = []
        for name in order:
            try:
                raw = LLMFactory.create(name, model, **provider_kwargs)
            except (ValueError, NotImplementedError, ImportError) as exc:
                # Sin credenciales / SDK ausente / nombre inválido → se omite del fallback.
                log.info("provider_skipped", provider=name, reason=str(exc))
                continue
            chain.append(
                CircuitBreakerLLM(
                    raw, name=name, failure_threshold=failure_threshold,
                    reset_timeout=reset_timeout,
                )
            )

        if not chain:
            raise ValueError(
                "ningún proveedor LLM disponible: configura credenciales para al menos uno "
                f"de {order}"
            )
        log.info("llm_chain_built", providers=[c.name for c in chain])  # type: ignore[attr-defined]
        return FallbackChainLLM(chain)
