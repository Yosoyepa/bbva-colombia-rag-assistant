from concurrent.futures import ThreadPoolExecutor

import pytest

from src.domain.entities import ChatMessage
from src.infrastructure.llm.circuit_breaker import CircuitBreakerLLM, CircuitOpenError
from src.infrastructure.llm.fallback_chain import FallbackChainLLM


class FailingLLM:
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        raise RuntimeError("boom")

    def stream(self, system_prompt: str, messages: list[ChatMessage]):
        raise RuntimeError("boom")
        yield ""


class WorkingLLM:
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        return "ok"

    def stream(self, system_prompt: str, messages: list[ChatMessage]):
        yield "ok"


class PromptSensitiveLLM:
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        if system_prompt == "fallback":
            raise RuntimeError("boom")
        return "primary"

    def stream(self, system_prompt: str, messages: list[ChatMessage]):
        yield self.generate(system_prompt, messages)


def test_fallback_chain_recovers_from_failed_provider():
    chain = FallbackChainLLM([FailingLLM(), WorkingLLM()])

    assert chain.generate("system", []) == "ok"
    assert chain.last_provider == "WorkingLLM"


def test_fallback_chain_tracks_provider_per_thread_context():
    chain = FallbackChainLLM([PromptSensitiveLLM(), WorkingLLM()])

    def call(prompt: str) -> tuple[str, str | None]:
        content = chain.generate(prompt, [])
        return content, chain.last_provider

    with ThreadPoolExecutor(max_workers=2) as pool:
        primary = pool.submit(call, "primary")
        fallback = pool.submit(call, "fallback")

    assert primary.result() == ("primary", "PromptSensitiveLLM")
    assert fallback.result() == ("ok", "WorkingLLM")


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreakerLLM(
        FailingLLM(),
        name="failing",
        failure_threshold=1,
        reset_timeout=60,
        max_retries=0,
    )

    with pytest.raises(RuntimeError):
        breaker.generate("system", [])
    with pytest.raises(CircuitOpenError):
        breaker.generate("system", [])
