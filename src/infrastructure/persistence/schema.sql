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

-- Sesiones de chat (CU-03).
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id  UUID PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mensajes de chat (CU-03 / CU-04). message_role: user | assistant | system.
CREATE TABLE IF NOT EXISTS chat_messages (
    id           UUID PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_role VARCHAR(16) NOT NULL,
    content      TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ventana de últimos N mensajes por sesión (CU-03) y barridos de analítica (CU-04).
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
    ON chat_messages (session_id, created_at);
