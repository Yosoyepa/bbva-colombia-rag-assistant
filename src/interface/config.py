"""Configuración externalizada (pydantic-settings) — leída en el Composition Root.

Única fuente de verdad de la config; la infraestructura recibe valores por
inyección, no lee el entorno. Mapea 1:1 con `.env.example`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # LLM (multi-proveedor)
    model_provider: str = "google"
    llm_model: str = "gemini-2.5-flash"
    provider_fallback_order: str = "google,anthropic,ollama"
    google_model: str = "gemini-2.5-flash"
    anthropic_model: str = "claude-3-5-haiku-latest"
    ollama_model: str = "llama3.1:8b"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ollama_host: str = "http://localhost:11434"

    # Embeddings
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # RAG
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Memoria
    n_history_messages: int = 6

    # Scraping
    scrape_base_url: str = "https://www.bbva.com.co/"

    # PostgreSQL + pgvector
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = "bbva"
    pg_password: str = "bbva"
    pg_database: str = "bbva_rag"

    @property
    def fallback_order(self) -> list[str]:
        return [p.strip() for p in self.provider_fallback_order.split(",") if p.strip()]

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado (singleton de facto) para el Composition Root."""
    return Settings()
