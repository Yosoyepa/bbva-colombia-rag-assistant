from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from src.domain.entities import ChatMessage, ChatSessionSummary
from src.interface.api.app import create_app


class FakeSettings:
    model_provider = "fake"


class FakeMemory:
    def __init__(self):
        self.session_id = uuid4()

    def list_sessions(self, limit: int = 20):
        return [
            ChatSessionSummary(
                id=self.session_id,
                created_at=datetime(2026, 5, 30, 10, 0, 0),
                updated_at=datetime(2026, 5, 30, 10, 1, 0),
                message_count=2,
                title="Que es BBVA?",
            )
        ]

    def get_recent_messages(self, session_id, limit: int):
        return [
            ChatMessage(
                session_id=session_id,
                role="user",
                content="Que es BBVA?",
                created_at=datetime(2026, 5, 30, 10, 0, 0),
            ),
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content="Respuesta anclada.",
                sources=["https://www.bbva.com.co/"],
                created_at=datetime(2026, 5, 30, 10, 1, 0),
            ),
        ]


class FakeContainer:
    def __init__(self):
        self.settings = FakeSettings()
        self.memory_repo = FakeMemory()

    def db_healthy(self) -> bool:
        return True

    def close(self) -> None:
        pass


class BrokenContainer(FakeContainer):
    def answer_use_case(self):
        raise ValueError("GOOGLE_API_KEY vacío")


def test_sessions_routes_expose_persisted_conversations():
    container = FakeContainer()
    app = create_app(lambda: container)

    with TestClient(app) as client:
        sessions = client.get("/sessions")
        assert sessions.status_code == 200
        assert sessions.json()[0]["title"] == "Que es BBVA?"

        session_id = sessions.json()[0]["session_id"]
        messages = client.get(f"/sessions/{session_id}/messages")
        assert messages.status_code == 200
        assert [item["role"] for item in messages.json()] == ["user", "assistant"]


def test_global_error_handler_maps_provider_configuration_errors():
    app = create_app(BrokenContainer)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/chat", json={"message": "Hola"})

    assert response.status_code == 503
    assert "GOOGLE_API_KEY" in response.json()["detail"]
