-- Esquema inicial (idempotente) — se ejecuta en el primer arranque de pgvector
-- vía /docker-entrypoint-initdb.d/. Ver SPEC-CU01 / SPEC-CU03 / SPEC-CU04.

CREATE EXTENSION IF NOT EXISTS vector;

-- Conocimiento vectorizado (CU-01). VECTOR(384) = dimensión del modelo de embedding
-- por defecto (multilingual MiniLM). Cambiar de modelo => actualizar esta dimensión
-- y re-indexar. EMBEDDING_MODEL es la única fuente de verdad (ver .env.example).
CREATE TABLE IF NOT EXISTS document_chunks (
    id               UUID PRIMARY KEY,
    content_cleaned  TEXT        NOT NULL,
    vector_embedding VECTOR(384) NOT NULL,
    source_url       VARCHAR     NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice HNSW para búsqueda aproximada por similitud coseno (rápido a escala).
CREATE INDEX IF NOT EXISTS idx_document_chunks_hnsw
    ON document_chunks USING hnsw (vector_embedding vector_cosine_ops);

-- Índice textual para retrieval híbrido BM25+denso (v1.3.0).
CREATE INDEX IF NOT EXISTS idx_document_chunks_fts
    ON document_chunks USING gin (to_tsvector('spanish', content_cleaned));

-- Cache persistente de embeddings. VECTOR(384) sigue la dimensión por defecto.
CREATE TABLE IF NOT EXISTS embedding_cache (
    cache_key        TEXT PRIMARY KEY,
    model_name       TEXT NOT NULL,
    text_hash        TEXT NOT NULL,
    vector_embedding VECTOR(384) NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cache opt-in de respuestas conversacionales.
CREATE TABLE IF NOT EXISTS answer_cache (
    cache_key       TEXT PRIMARY KEY,
    content         TEXT NOT NULL,
    sources         TEXT[] NOT NULL DEFAULT '{}',
    retrieval_trace JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Registro de frescura/cambios del scraping.
CREATE TABLE IF NOT EXISTS scraped_pages (
    source_url   TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    status       VARCHAR(24) NOT NULL DEFAULT 'new'
);

-- Sesiones de chat (CU-03).
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id  UUID PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mensajes de chat (CU-03 / CU-04). message_role: user | assistant | system.
-- `sources` registra las URLs citadas por las respuestas (Log Aggregation) → analítica CU-04.
CREATE TABLE IF NOT EXISTS chat_messages (
    id           UUID PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_role VARCHAR(16) NOT NULL,
    content      TEXT NOT NULL,
    sources      TEXT[] NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS sources TEXT[] NOT NULL DEFAULT '{}';

-- Ventana de últimos N mensajes por sesión (CU-03) y barridos de analítica (CU-04).
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
    ON chat_messages (session_id, created_at);
