# AGENTS.md — `src/domain/`

Capa más interna. Ver [contexto global](../../AGENTS.md).

## Responsabilidad

Modelar los conceptos de negocio como **entidades puras**: `Document` (página cruda
scrapeada), `Chunk` (fragmento limpio listo para embedding/retrieval), `ChatSession`,
`ChatMessage`. Son `@dataclass` de stdlib.

## Regla de dependencia

- **Cero imports externos.** Solo `dataclasses`, `datetime`, `uuid`, `typing` de la stdlib.
- Prohibido: `pydantic`, `psycopg`, SDKs de LLM, `sqlalchemy`, frameworks. Si aparece un
  import de librería aquí, la arquitectura está rota.
- No conoce ports, use_cases, infraestructura ni interface.

## Patrones / decisiones

- **Entidades anémicas a propósito**: en este alcance son contenedores de datos; la lógica
  vive en los casos de uso. Mantenerlo así salvo que una invariante sea claramente del dominio.
- IDs como `UUID` generados por defecto (`field(default_factory=uuid4)`); timestamps en UTC.
- El `embedding` de `Chunk` es `list[float]` (no `numpy`): el dominio no depende de cómo se
  calcula. La conversión a/desde el vector de la DB es responsabilidad de `persistence`.

## Para conservar

Si un cambio te tienta a importar algo externo aquí, el lugar correcto es un **port**
(`application/ports/`) o un **adapter** (`infrastructure/`), no el dominio.
