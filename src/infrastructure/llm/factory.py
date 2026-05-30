"""LLMFactory (patrón Factory Method) — selecciona el proveedor por configuración.

Lee `provider` y produce una implementación de LargeLanguageModel. En Fase 1
solo Gemini está activo; el resto se añade en Fase 2 (junto al fallback). Añadir
un proveedor = una clase nueva + una rama aquí.
"""
from __future__ import annotations

from src.application.ports import LargeLanguageModel
from src.infrastructure.llm.gemini_client import GeminiClient


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
        model: str,
        *,
        google_api_key: str = "",
        anthropic_api_key: str = "",
        aws_access_key_id: str = "",
        aws_secret_access_key: str = "",
        aws_region: str = "us-east-1",
        bedrock_model_id: str = "",
        ollama_host: str = "",
    ) -> LargeLanguageModel:
        provider = (provider or "").lower()
        if provider == "google":
            return GeminiClient(api_key=google_api_key, model=model)
        if provider in ("anthropic", "bedrock", "ollama"):
            raise NotImplementedError(
                f"proveedor '{provider}' se habilita en Fase 2 (multi-proveedor + fallback)"
            )
        raise ValueError(f"MODEL_PROVIDER desconocido: '{provider}'")
