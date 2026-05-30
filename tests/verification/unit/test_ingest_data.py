from src.application.use_cases.ingest_data import IngestDataUseCase
from src.domain.entities import Chunk


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [1.0, 0.0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), 0.0] for index, _ in enumerate(texts, start=1)]

    @property
    def dimension(self) -> int:
        return 2


class FakeRepository:
    def __init__(self):
        self.added = []
        self.replaced = None

    def add_chunks(self, chunks):
        self.added = chunks

    def replace_chunks(self, chunks, source_urls):
        self.replaced = (chunks, source_urls)

    def search(self, query_embedding, top_k):
        return []

    def count(self):
        return 0


def test_ingest_replaces_chunks_for_changed_sources_after_embedding():
    repo = FakeRepository()
    chunk = Chunk(content="nuevo contenido", source_url="https://www.bbva.com.co/a")
    use_case = IngestDataUseCase(embedder=FakeEmbedder(), knowledge_repo=repo)

    result = use_case.execute(
        [chunk],
        documents_scraped=1,
        replace_source_urls=[chunk.source_url],
    )

    assert result.chunks_indexed == 1
    assert chunk.embedding == [1.0, 0.0]
    assert repo.replaced == ([chunk], [chunk.source_url])
    assert repo.added == []
