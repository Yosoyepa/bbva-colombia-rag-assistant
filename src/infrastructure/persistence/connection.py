"""Pool de conexiones a PostgreSQL con pgvector registrado.

El pool es un singleton gestionado por el Composition Root y se inyecta en los
repositorios. Registrar el tipo `vector` permite pasar/leer list[float] directo.
"""

from __future__ import annotations

from psycopg_pool import ConnectionPool


def _register_vector(conn) -> None:
    from pgvector.psycopg import register_vector

    register_vector(conn)


def create_pool(dsn: str, min_size: int = 1, max_size: int = 4) -> ConnectionPool:
    """Crear y abrir un pool; cada conexión queda lista para usar vectores."""
    pool = ConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        configure=_register_vector,
        open=True,
    )
    return pool
