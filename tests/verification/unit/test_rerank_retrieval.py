from src.domain.entities import Chunk
from src.infrastructure.retrieval.rerank_retrieval import RerankRetrieval


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    @property
    def dimension(self) -> int:
        return 3


class FakeRepository:
    def __init__(self):
        self.requested_top_k = None

    def add_chunks(self, chunks):
        pass

    def search(self, query_embedding, top_k):
        self.requested_top_k = top_k
        return [
            Chunk(content="tercero", source_url="https://bbva.com.co/3"),
            Chunk(content="primero", source_url="https://bbva.com.co/1"),
            Chunk(content="segundo", source_url="https://bbva.com.co/2"),
        ]

    def count(self) -> int:
        return 3


class FakeBaseRetrieval:
    def __init__(self):
        self.requested_top_k = None

    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        self.requested_top_k = top_k
        return [
            Chunk(
                content="hibrido tercero",
                source_url="https://bbva.com.co/3",
                dense_score=0.4,
                bm25_score=0.2,
                hybrid_score=0.33,
            ),
            Chunk(
                content="hibrido primero",
                source_url="https://bbva.com.co/1",
                dense_score=0.7,
                bm25_score=0.9,
                hybrid_score=0.77,
            ),
            Chunk(
                content="hibrido segundo",
                source_url="https://bbva.com.co/2",
                dense_score=0.6,
                bm25_score=0.5,
                hybrid_score=0.56,
            ),
        ]


class FakeCrossEncoder:
    def predict(self, pairs):
        return [0.1, 0.9, 0.4]


def test_rerank_retrieval_reorders_dense_candidates():
    repo = FakeRepository()
    retrieval = RerankRetrieval(
        FakeEmbedder(),
        repo,
        model_name="fake-cross-encoder",
        candidate_multiplier=3,
        cross_encoder=FakeCrossEncoder(),
    )

    chunks = retrieval.retrieve("consulta", top_k=2)

    assert repo.requested_top_k == 6
    assert [chunk.content for chunk in chunks] == ["primero", "segundo"]


def test_rerank_retrieval_can_wrap_hybrid_base_and_preserve_scores():
    base_retrieval = FakeBaseRetrieval()
    retrieval = RerankRetrieval(
        FakeEmbedder(),
        FakeRepository(),
        model_name="fake-cross-encoder",
        candidate_multiplier=2,
        cross_encoder=FakeCrossEncoder(),
        base_retrieval=base_retrieval,
    )

    chunks = retrieval.retrieve("consulta", top_k=2)

    assert base_retrieval.requested_top_k == 4
    assert [chunk.content for chunk in chunks] == ["hibrido primero", "hibrido segundo"]
    assert chunks[0].hybrid_score == 0.77
    assert chunks[0].dense_score == 0.7
    assert chunks[0].bm25_score == 0.9
    assert chunks[0].rerank_score == 0.9
