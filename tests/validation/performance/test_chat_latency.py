import time
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application.use_cases.answer_query import Answer
from src.interface.api.app import create_app


class FakeSettings:
    model_provider = "fake"


class FastContainer:
    settings = FakeSettings()

    def answer_use_case(self):
        session_id = uuid4()

        class UseCase:
            def execute(self, _session_id, _message):
                return Answer(session_id=session_id, content="ok")

        return UseCase()

    def db_healthy(self):
        return True

    def close(self):
        pass


def test_chat_endpoint_with_doubles_stays_fast():
    app = create_app(FastContainer)
    started = time.monotonic()

    with TestClient(app) as client:
        for _ in range(20):
            response = client.post("/chat", json={"message": "hola"})
            assert response.status_code == 200

    assert time.monotonic() - started < 1.0
