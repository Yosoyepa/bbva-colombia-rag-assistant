from uuid import uuid4

from src.application.use_cases.answer_query import AnswerQueryUseCase
from src.domain.entities import ChatMessage, ChatSession, Chunk


class FakeRetrieval:
    def retrieve(self, query, top_k):
        return [Chunk(content="BBVA empresas", source_url="https://www.bbva.com.co/empresas")]


class FakeLLM:
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        return "Respuesta persistible."

    def stream(self, system_prompt: str, messages: list[ChatMessage]):
        yield "Respuesta"


class FakeMemory:
    def __init__(self):
        self.session = ChatSession(id=uuid4())
        self.messages = []

    def get_or_create_session(self, session_id=None):
        return self.session

    def add_message(self, message):
        self.messages.append(message)

    def get_recent_messages(self, session_id, limit):
        return []


def test_chat_turn_persists_user_assistant_and_sources():
    memory = FakeMemory()
    use_case = AnswerQueryUseCase(
        retrieval=FakeRetrieval(),
        llm=FakeLLM(),
        memory=memory,
        top_k=5,
        n_history_messages=6,
    )

    answer = use_case.execute(None, "¿Qué ofrece BBVA empresas?")

    assert [message.role for message in memory.messages] == ["user", "assistant"]
    assert memory.messages[-1].sources == answer.sources
    assert answer.observability.persistence_latency_ms >= 0
