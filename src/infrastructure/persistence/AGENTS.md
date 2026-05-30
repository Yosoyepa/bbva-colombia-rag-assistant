# AGENTS.md — `src/infrastructure/persistence/`

Adaptadores de persistencia. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Implementar los repositorios contra **PostgreSQL + pgvector**:

- `PgVectorKnowledgeRepository` — `VectorKnowledgeRepository`: insertar chunks con embedding,
  búsqueda top-K por similitud (índice **HNSW**).
- `PgChatMemoryRepository` — `ChatMemoryRepository`: sesiones, mensajes, ventana de últimos N.
- Esquema/migraciones de la DB (tablas + extensión `vector` + índice HNSW).

## Modelo de datos

- `document_chunks(id UUID, content_cleaned TEXT, vector_embedding VECTOR(N), source_url VARCHAR)` + índice HNSW.
- `chat_sessions(session_id UUID, created_at TIMESTAMP)`.
- `chat_messages(id, session_id FK, message_role, content, created_at)`.

## Regla de dependencia

- Implementa ports de `application`. Importa `domain`, `application.ports`, `psycopg`/`pgvector`.
- Convierte entre entidades del dominio y filas SQL aquí; el dominio no sabe de columnas.

## Patrones / decisiones

- **Repository** (no DAO): la API expone entidades, no filas.
- Conexión vía **pool** (`psycopg_pool`); el pool se inyecta (singleton gestionado en `interface`).
- La dimensión del vector (`VECTOR(N)`) debe coincidir con `EMBEDDING_MODEL`; es config, no hardcode.

## Para conservar

Todo el SQL vive aquí. Nada de strings SQL en use_cases o interface. Migraciones idempotentes
para que `docker compose up` levante el esquema sin pasos manuales.
