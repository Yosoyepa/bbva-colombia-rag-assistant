# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning for delivery milestones.

## [Unreleased]

## [1.1.0] - 2026-05-30

### Added

- Streamlit analytics tab for MVP observability, backed by `GET /analytics`.
- Visual metrics for total sessions, total messages and average messages per session.
- Top cited sources table and bar chart using the persisted conversation history.
- Minor-version release convention for post-MVP iterations after `v1.0.0`.

### Changed

- FastAPI application metadata version updated to `1.1.0`.
- Python package version updated to `1.1.0`.

## [1.0.0] - 2026-05-30

### Added

- End-to-end BBVA RAG MVP: scraping, cleaning, chunking, embeddings and pgvector indexing.
- FastAPI `/chat`, `/health`, `/sessions` and `/analytics` endpoints.
- Streamlit chat UI with persisted session browsing.
- Conversational memory by UUID with configurable `N_HISTORY_MESSAGES`.
- Multi-provider LLM support for Google, Anthropic, Bedrock and Ollama.
- Chain of Responsibility fallback with Circuit Breaker for LLM providers.
- CLI ingestion command `bbva-ingest`.
- CLI analytics command `bbva-analytics`.
- Cross-Encoder reranker strategy, disabled by default through `RERANK_ENABLED`.
- Docker one-command stack with PostgreSQL + pgvector, FastAPI and Streamlit.
- L1 pytest coverage and opt-in L2 Ragas smoke evaluation.

### Documented

- Architecture decisions, design patterns, known limitations and future improvements.
- GitFlow release baseline with tag `v1.0.0`.
