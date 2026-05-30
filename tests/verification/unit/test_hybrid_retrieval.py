from src.domain.entities import Chunk
from src.infrastructure.retrieval.hybrid_retrieval import HybridRetrieval


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    @property
    def dimension(self) -> int:
        return 2


class FakeRepository:
    def __init__(self):
        self.args = None

    def add_chunks(self, chunks):
        pass

    def search(self, query_embedding, top_k):
        return []

    def search_hybrid(self, query_text, query_embedding, top_k, dense_weight, bm25_weight):
        self.args = (query_text, query_embedding, top_k, dense_weight, bm25_weight)
        return [Chunk(content="resultado", source_url="https://www.bbva.com.co/")]

    def count(self) -> int:
        return 1


def test_hybrid_retrieval_delegates_weighted_search_to_repository():
    repo = FakeRepository()
    retrieval = HybridRetrieval(FakeEmbedder(), repo, dense_weight=0.7, bm25_weight=0.3)

    chunks = retrieval.retrieve("empresas", top_k=4)

    assert chunks[0].content == "resultado"
    assert repo.args == ("empresas", [0.1, 0.2], 4, 0.7, 0.3)
