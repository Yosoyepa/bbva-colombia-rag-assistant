# AGENTS.md — `src/infrastructure/embeddings/`

Adaptador de embeddings. Ver [contexto global](../../../AGENTS.md).

## Responsabilidad

Implementar `Embedder` con **sentence-transformers en CPU** (`SentenceTransformerEmbedder`):
texto → vector. Mismo modelo para indexar chunks (CU-01) y para embeber la query (CU-02).

## Regla de dependencia

- Implementa `application.ports.Embedder`. Importa `sentence_transformers`. Devuelve
  `list[float]` (o lote), no expone tensores/numpy al núcleo.

## Patrones / decisiones

- **Entorno sin GPU**: modelo ligero por defecto; CPU. La dimensión del vector la fija
  `EMBEDDING_MODEL` y **debe** coincidir con `VECTOR(N)` en `persistence`.
- **Singleton de facto**: el modelo se carga **una vez** (es caro) y se inyecta; no recargar por request.
- Soporta batch para acelerar la ingesta.

## Para conservar

Cambiar de modelo de embedding implica re-indexar (la dimensión cambia). Documentarlo y
mantener `EMBEDDING_MODEL` como única fuente de verdad.
