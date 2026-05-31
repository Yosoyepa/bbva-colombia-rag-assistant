# Estrategia de pruebas V&V

La suite separa verificacion y validacion para que el evaluador vea dos preguntas
distintas:

- **Verificacion:** el software fue construido correctamente.
- **Validacion:** el chatbot satisface atributos relevantes de ejecucion.

```text
tests/
  verification/
    unit/
    integration/
    architecture/
  validation/
    system/
    rag_quality/
    performance/
    resilience/
    persistence/
```

## Comandos

Suite completa:

```bash
docker compose exec app pytest tests
```

Verificacion:

```bash
docker compose exec app pytest tests/verification
```

Validacion ligera:

```bash
docker compose exec app pytest tests/validation
```

Ragas real, opt-in:

```bash
docker compose exec -e RUN_RAGAS_L2=1 app pytest tests/validation/rag_quality
```

## Cobertura relevante

- Casos de uso y estrategias de retrieval con dobles.
- Contrato REST con TestClient.
- Regla de dependencias por capas.
- Fallback LLM y Circuit Breaker.
- Persistencia de memoria y fuentes.
- Performance ligera sin LLM real.
- Dataset RAG validado estructuralmente siempre; metrica Ragas solo con flag.

## CI

GitHub Actions ejecuta calidad en `main`: formato, lint, compilacion y suites de
verificacion/validacion ligera. La evaluacion RAG con credenciales queda opt-in.
