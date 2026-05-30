# AGENTS.md — `tests/`

Estrategia de pruebas pragmática (L1 + L2 ligero). Ver [contexto global](../AGENTS.md).

## Responsabilidad

Verificar el sistema en dos niveles proporcionales al alcance de la prueba:

- `l1/` — **unitarios** (pytest): chunking, cleaner, `LLMFactory` ante config malformada,
  repositorios (con DB de test). Rápidos, deterministas, sin red.
- `l2/` — **evaluación RAG ligera** (Ragas): `faithfulness` + `context_recall` sobre un set
  de 5–10 Q&A ground-truth. Verifica que el RAG responde anclado y no alucina.

## Regla de dependencia

- Los tests pueden importar cualquier capa. Los L1 mockean infraestructura externa (red/LLM);
  los repos se prueban contra una DB de test (pgvector en contenedor).

## Patrones / decisiones

- **No sobre-dimensionar**: se descartan L3 (ArchUnit, needle-in-haystack, OWASP exhaustivo)
  por proporción a 1.5 días; se documentan como futura mejora.
- L2 corre sobre el ground-truth definido en/junto a `specs/`; umbrales configurables.

## Para conservar

`rtk pytest tests/l1` debe quedar verde antes de cada merge a `develop`. L2 valida calidad de
respuesta, no solo que el código corra.
