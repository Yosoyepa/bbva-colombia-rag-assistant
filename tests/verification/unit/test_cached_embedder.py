from src.infrastructure.embeddings.cached_embedder import CachedEmbedder


class FakeEmbedder:
    calls = 0

    def embed_text(self, text: str) -> list[float]:
        self.calls += 1
        return [1.0, 0.0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls += len(texts)
        return [[float(index), 0.0] for index, _ in enumerate(texts, start=1)]

    @property
    def dimension(self) -> int:
        return 2


class FakeCache:
    def __init__(self):
        self.values = {}

    def get_embedding(self, key):
        return self.values.get(key)

    def set_embedding(self, key, model, text_hash, embedding):
        self.values[key] = embedding


def test_cached_embedder_reuses_persisted_vector():
    wrapped = FakeEmbedder()
    cache = FakeCache()
    embedder = CachedEmbedder(wrapped, cache, model_name="test-model")

    first = embedder.embed_text("hola")
    second = embedder.embed_text("hola")

    assert first == second
    assert wrapped.calls == 1
