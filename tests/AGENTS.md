# AGENTS.md — `tests/`

Estrategia de pruebas V&V para calidad de software. Ver [contexto global](../AGENTS.md).

## Responsabilidad

Separar verificación y validación para que el lector distinga pruebas de construcción
correcta frente a pruebas de comportamiento esperado del chatbot:

- `verification/unit/` — unidades deterministas: casos de uso, factories, estrategias y
  decorators sin red ni LLM real.
- `verification/integration/` — integración ligera entre API, DTOs y dependencias con dobles.
- `verification/architecture/` — regla de dependencias por capas.
- `validation/system/` — contrato observable del sistema desde el borde HTTP.
- `validation/performance/` — latencia ligera con dobles, sin proveedores reales.
- `validation/resilience/` — fallback, Circuit Breaker y errores controlados.
- `validation/persistence/` — memoria conversacional y fuentes persistidas.
- `validation/rag_quality/` — dataset ground-truth validado siempre y Ragas opt-in.

## Regla de dependencia

- Los tests pueden importar cualquier capa, pero no deben convertir infraestructura externa
  en requisito para la suite base.
- Las pruebas con LLM, Ragas real, scraping real o credenciales deben ser opt-in por variable
  de entorno.

## Patrones / decisiones

- **Verification** responde si el software fue construido correctamente: unidades,
  integración y arquitectura.
- **Validation** responde si el software satisface atributos de ejecución relevantes para
  un chatbot: sistema, performance, resiliencia, persistencia y calidad RAG.
- Ragas no bloquea el flujo local por defecto; el dataset sí se valida siempre para evitar
  que la evaluación se deteriore silenciosamente.

## Para conservar

```bash
rtk pytest tests/verification
rtk pytest tests/validation
RUN_RAGAS_L2=1 rtk pytest tests/validation/rag_quality
```

La suite base debe quedar verde antes de cada merge a `develop`.
