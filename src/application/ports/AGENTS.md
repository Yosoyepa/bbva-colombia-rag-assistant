# AGENTS.md — `src/application/ports/`

Los **contratos** (Ports del patrón Ports & Adapters). Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Definir las interfaces abstractas que la aplicación necesita; la infraestructura las
implementa (Adapters). Ports previstos:

- `VectorKnowledgeRepository` — guardar chunks (con embedding) y buscar los top-K por similitud.
- `ChatMemoryRepository` — crear/leer sesiones y mensajes; ventana de últimos N.
- `LargeLanguageModel` — generar una respuesta dado prompt/mensajes (interfaz uniforme a todos los proveedores).
- `Embedder` — convertir texto(s) en vector(es).
- `RetrievalStrategy` — recuperar contexto para una query (Dense / Rerank).

## Regla de dependencia

- Solo `abc` + `typing` + tipos de `domain`. Sin librerías externas.
- Son **ABC** (o `Protocol`) con métodos sin implementar. Definen *qué*, no *cómo*.

## Patrones / decisiones

- **Repository** para persistencia (preferido sobre DAO): expone colecciones de entidades,
  oculta SQL/pgvector.
- **Strategy** para retrieval: misma interfaz, algoritmos intercambiables por env.
- **Factory** produce implementaciones de `LargeLanguageModel`; el port es agnóstico al proveedor.

## Para conservar

Un port describe una **necesidad del negocio**, no una tecnología. Nombres y firmas no deben
filtrar detalles de implementación (nada de `cursor`, `boto3`, `session_id` crudo de psycopg).
