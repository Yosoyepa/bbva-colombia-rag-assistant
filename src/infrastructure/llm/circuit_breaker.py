"""Circuit Breaker como **Decorator** sobre LargeLanguageModel.

Envuelve cualquier proveedor y mantiene su interfaz idéntica (Decorator). Cuenta
fallos consecutivos; al superar `failure_threshold` "abre" el circuito y falla
rápido durante `reset_timeout` segundos sin tocar al backend (evita martillar un
proveedor caído). Tras el timeout pasa a *half-open*: deja pasar una llamada de
prueba; si va bien cierra, si falla vuelve a abrir. Suma retry + logging.

Estados: CLOSED (normal) → OPEN (rechaza) → HALF_OPEN (prueba) → CLOSED/OPEN.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from threading import RLock

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class CircuitOpenError(RuntimeError):
    """El circuito está abierto: el proveedor se considera no disponible."""


class CircuitBreakerLLM(LargeLanguageModel):
    def __init__(
        self,
        wrapped: LargeLanguageModel,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        max_retries: int = 1,
    ) -> None:
        self._wrapped = wrapped
        self._name = name
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._max_retries = max_retries
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = RLock()

    @property
    def name(self) -> str:
        return self._name

    def _allow(self) -> bool:
        """¿Se permite intentar la llamada? (gestiona el paso OPEN→HALF_OPEN)."""
        with self._lock:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self._reset_timeout:
                log.info("circuit_half_open", provider=self._name)
                return True  # half-open: dejamos pasar una prueba
            return False

    def _on_success(self) -> None:
        with self._lock:
            if self._failures or self._opened_at is not None:
                log.info("circuit_closed", provider=self._name)
            self._failures = 0
            self._opened_at = None

    def _on_failure(self, error: Exception) -> None:
        with self._lock:
            self._failures += 1
            failures = self._failures
            should_open = failures >= self._failure_threshold
            if should_open:
                self._opened_at = time.monotonic()
        log.warning(
            "provider_call_failed",
            provider=self._name,
            failures=failures,
            error=str(error),
        )
        if should_open:
            log.error("circuit_opened", provider=self._name, reset_in_s=self._reset_timeout)

    def _guarded(self, fn):
        if not self._allow():
            raise CircuitOpenError(f"circuito abierto para proveedor '{self._name}'")
        last: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                result = fn()
                self._on_success()
                return result
            except Exception as exc:  # noqa: BLE001
                last = exc
                if attempt < self._max_retries:
                    log.info("provider_retry", provider=self._name, attempt=attempt + 1)
        self._on_failure(last)  # type: ignore[arg-type]
        raise last  # type: ignore[misc]

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        return self._guarded(lambda: self._wrapped.generate(system_prompt, messages))

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        # En streaming no reintentamos a medias: protegemos la apertura del stream.
        if not self._allow():
            raise CircuitOpenError(f"circuito abierto para proveedor '{self._name}'")
        try:
            yield from self._wrapped.stream(system_prompt, messages)
            self._on_success()
        except Exception as exc:  # noqa: BLE001
            self._on_failure(exc)
            raise
