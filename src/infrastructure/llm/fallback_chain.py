"""Fallback entre proveedores como **Chain of Responsibility**.

Mantiene una lista ordenada de proveedores (cada uno normalmente envuelto en un
CircuitBreakerLLM). En `generate`/`stream` intenta el primero; si lanza, registra
y delega en el siguiente eslabón de la cadena. Si todos fallan, eleva un error
agregado. Es transparente para el caso de uso: sigue siendo un LargeLanguageModel.
"""
from __future__ import annotations

from collections.abc import Iterator

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class AllProvidersFailedError(RuntimeError):
    """Ningún proveedor de la cadena pudo responder."""


class FallbackChainLLM(LargeLanguageModel):
    def __init__(self, providers: list[LargeLanguageModel]) -> None:
        if not providers:
            raise ValueError("FallbackChainLLM requiere al menos un proveedor")
        self._providers = providers

    @staticmethod
    def _label(provider: LargeLanguageModel, idx: int) -> str:
        return getattr(provider, "name", provider.__class__.__name__) or f"#{idx}"

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        errors: list[str] = []
        for idx, provider in enumerate(self._providers):
            label = self._label(provider, idx)
            try:
                content = provider.generate(system_prompt, messages)
                if idx > 0:
                    log.info("fallback_succeeded", provider=label, position=idx)
                return content
            except Exception as exc:  # noqa: BLE001
                log.warning("provider_in_chain_failed", provider=label, error=str(exc))
                errors.append(f"{label}: {exc}")
        raise AllProvidersFailedError("todos los proveedores fallaron → " + " | ".join(errors))

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        errors: list[str] = []
        for idx, provider in enumerate(self._providers):
            label = self._label(provider, idx)
            try:
                # Materializamos el primer token para detectar fallo antes de ceder el stream.
                gen = provider.stream(system_prompt, messages)
                first = next(gen)
                if idx > 0:
                    log.info("fallback_succeeded", provider=label, position=idx)
                yield first
                yield from gen
                return
            except StopIteration:
                return  # stream vacío pero válido
            except Exception as exc:  # noqa: BLE001
                log.warning("provider_in_chain_failed", provider=label, error=str(exc))
                errors.append(f"{label}: {exc}")
        raise AllProvidersFailedError("todos los proveedores fallaron → " + " | ".join(errors))
