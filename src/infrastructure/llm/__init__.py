"""Proveedores LLM + Factory + fallback (Chain of Responsibility) + Circuit Breaker.

Ver AGENTS.md. Los clientes concretos se importan de forma diferida dentro del
Factory para no exigir todos los SDKs salvo que el proveedor se use.
"""
from src.infrastructure.llm.circuit_breaker import CircuitBreakerLLM, CircuitOpenError
from src.infrastructure.llm.fallback_chain import AllProvidersFailedError, FallbackChainLLM
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.llm.gemini_client import GeminiClient

__all__ = [
    "LLMFactory",
    "GeminiClient",
    "CircuitBreakerLLM",
    "CircuitOpenError",
    "FallbackChainLLM",
    "AllProvidersFailedError",
]
