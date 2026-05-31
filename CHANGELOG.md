# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning for delivery milestones.

## [Unreleased]

### Added

- Bounded deeper scraping configuration: start URLs, max depth, allowed prefixes and exclude
  patterns for `bbva-ingest`.
- Unit coverage for scraper URL filtering/prioritization and per-thread LLM provider tracking.

### Changed

- Reranker composition can now wrap dense or hybrid retrieval, preserving BM25/dense/hybrid
  trace fields while adding `rerank_score`.
- Split cache/freshness persistence into narrower repositories and ports for answers,
  embeddings and scraped pages.
- Made LLM fallback provider observability context-local and guarded Circuit Breaker state.
- README now explains how to increase scraping coverage without compromising runtime and
  reliability.

## [1.3.0] - 2026-05-30

### Added

- Verification/validation test taxonomy under `tests/verification` and `tests/validation`.
- Architecture, performance, resilience, persistence and system validation tests.
- Ragas ground-truth dataset with always-on structure validation and opt-in real Ragas run.
- Chat observability metrics in `POST /chat`: stage latencies, provider and cache hit state.
- Streamlit observability expander per assistant response.
- Persistent embedding cache and opt-in answer cache with TTL.
- Hybrid retrieval strategy combining pgvector dense search and PostgreSQL full-text search.
- Freshness/change detection table for scraping runs and `bbva-ingest` flags:
  `--freshness-hours` and `--force-refresh`.
- GitHub Actions quality workflow for verification, light validation and opt-in RAG quality.

### Changed

- FastAPI application metadata version updated to `1.3.0`.
- Python package version updated to `1.3.0`.
- README updated to describe software quality scope, V&V commands, retrieval/cache/freshness
  decisions and observability contract.

## [1.2.0] - 2026-05-30

### Added

- Retrieval trace in `POST /chat` responses, including rank, source URL, pgvector distance,
  similarity score, optional reranker score and content preview.
- Streamlit retrieval trace expander per assistant response.
- Recent conversations table in the Streamlit analytics tab.
- README section documenting local embedding/reranker choices and observability scope.

### Changed

- Refactored Streamlit from a single `streamlit_app.py` file into a modular
  `src/interface/streamlit_app/` package with API client, state and components.
- FastAPI application metadata version updated to `1.2.0`.
- Python package version updated to `1.2.0`.

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
