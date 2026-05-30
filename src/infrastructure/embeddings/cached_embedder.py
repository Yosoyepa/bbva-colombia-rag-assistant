"""Decorator de cache para embeddings locales."""
from __future__ import annotations

import hashlib

from src.application.ports import Embedder


class CachedEmbedder(Embedder):
    def __init__(self, wrapped: Embedder, cache, model_name: str) -> None:
        self._wrapped = wrapped
        self._cache = cache
        self._model_name = model_name

    def _key(self, text: str) -> tuple[str, str]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self._model_name}:{text_hash}", text_hash

    def embed_text(self, text: str) -> list[float]:
        cache_key, text_hash = self._key(text)
        cached = self._cache.get_embedding(cache_key)
        if cached is not None:
            return cached
        embedding = self._wrapped.embed_text(text)
        self._cache.set_embedding(cache_key, self._model_name, text_hash, embedding)
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float] | None] = []
        missing: list[tuple[int, str, str, str]] = []
        for index, text in enumerate(texts):
            cache_key, text_hash = self._key(text)
            cached = self._cache.get_embedding(cache_key)
            results.append(cached)
            if cached is None:
                missing.append((index, text, cache_key, text_hash))

        if missing:
            vectors = self._wrapped.embed_batch([item[1] for item in missing])
            for (index, _text, cache_key, text_hash), vector in zip(missing, vectors, strict=True):
                self._cache.set_embedding(cache_key, self._model_name, text_hash, vector)
                results[index] = vector

        return [result or [] for result in results]

    @property
    def dimension(self) -> int:
        return self._wrapped.dimension
