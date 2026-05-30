from uuid import uuid4

from fastapi.testclient import TestClient

from src.application.use_cases.answer_query import Answer, AnswerObservability
from src.interface.api.app import create_app


class FakeSettings:
    model_provider = "fake"


class ContractContainer:
    settings = FakeSettings()

    def answer_use_case(self):
        class UseCase:
            def execute(self, _session_id, _message):
                return Answer(
                    session_id=uuid4(),
                    content="ok",
                    observability=AnswerObservability(total_latency_ms=1.0),
                )

        return UseCase()

    def db_healthy(self):
        return True

    def close(self):
        pass


def test_chat_contract_includes_observability_and_retrieval_trace():
    app = create_app(ContractContainer)

    with TestClient(app) as client:
        response = client.post("/chat", json={"message": "hola"})

    assert response.status_code == 200
    payload = response.json()
    assert "retrieval_trace" in payload
    assert payload["observability"]["total_latency_ms"] == 1.0
