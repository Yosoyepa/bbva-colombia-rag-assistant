from uuid import uuid4

from src.application.use_cases.answer_query import AnswerQueryUseCase
from src.domain.entities import ChatMessage, ChatSession, Chunk


class FakeRetrieval:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve(self, query: str, top_k: int):
        return self._chunks


class FakeLLM:
    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        return "Respuesta anclada."

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


def test_answer_persists_assistant_sources_for_analytics():
    chunk = Chunk(content="Contenido BBVA", source_url="https://www.bbva.com.co/producto")
    memory = FakeMemory()
    use_case = AnswerQueryUseCase(
        retrieval=FakeRetrieval([chunk]),
        llm=FakeLLM(),
        memory=memory,
        top_k=5,
        n_history_messages=6,
    )

    answer = use_case.execute(None, "Que ofrece BBVA?")

    assert answer.sources == ["https://www.bbva.com.co/producto"]
    assert memory.messages[-1].role == "assistant"
    assert memory.messages[-1].sources == answer.sources


def test_answer_short_circuits_when_retrieval_is_empty():
    memory = FakeMemory()
    use_case = AnswerQueryUseCase(
        retrieval=FakeRetrieval([]),
        llm=FakeLLM(),
        memory=memory,
        top_k=5,
        n_history_messages=6,
    )

    answer = use_case.execute(None, "Pregunta fuera del corpus")

    assert "No encontré información" in answer.content
    assert answer.sources == []
    assert len(memory.messages) == 2
