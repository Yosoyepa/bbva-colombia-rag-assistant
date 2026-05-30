"""Port: modelo de lenguaje (interfaz uniforme a todos los proveedores)."""
from abc import ABC, abstractmethod
from collections.abc import Iterator

from src.domain.entities import ChatMessage


class LargeLanguageModel(ABC):
    """Contrato agnóstico al proveedor (Anthropic/Bedrock/Gemini/Ollama).

    El Factory (infrastructure/llm) produce implementaciones de esta interfaz;
    el caso de uso pide "genera" sin saber qué backend responde (el fallback
    entre proveedores es transparente).
    """

    @abstractmethod
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        """Generar una respuesta dado un system prompt y el historial de mensajes."""
        ...

    @abstractmethod
    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        """Generar la respuesta token a token (para streaming en la UI)."""
        ...
