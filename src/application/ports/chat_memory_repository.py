"""Port: persistencia de sesiones y mensajes de chat (memoria conversacional)."""
from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import ChatMessage, ChatSession


class ChatMemoryRepository(ABC):
    """Contrato para la memoria de chat: sesiones por ID y ventana de N mensajes.

    Implementación concreta (PostgreSQL) en infrastructure/persistence.
    """

    @abstractmethod
    def get_or_create_session(self, session_id: UUID | None = None) -> ChatSession:
        """Recuperar la sesión por ID o crear una nueva si no existe / es None."""
        ...

    @abstractmethod
    def add_message(self, message: ChatMessage) -> None:
        """Persistir un mensaje (user/assistant/system) en su sesión."""
        ...

    @abstractmethod
    def get_recent_messages(self, session_id: UUID, limit: int) -> list[ChatMessage]:
        """Últimos `limit` mensajes de la sesión, en orden cronológico.

        `limit` proviene de N_HISTORY_MESSAGES (config externalizada).
        """
        ...
