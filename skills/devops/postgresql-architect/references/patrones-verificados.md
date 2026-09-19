# Patrones PostgreSQL verificados (evidencia primero)

> Destilado del ecosistema: awesome-copilot postgresql-optimization y postgresql-code-review, sickn33/agentic-awesome-skills, affaan-m/ecc postgres-patterns, mindrally postgresql-best-practices, manutej/luxor postgresql-database-engineering, aws amazon-aurora-postgresql, wshobson postgresql-table-design.

## Diseño de tablas (wshobson postgresql-table-design)

Regla base: cada tabla = una entidad, tipos correctos, constraints declarativas, auditoría temporal.

```sql
CREATE TABLE pedidos (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cliente_id  BIGINT NOT NULL REFERENCES clientes(id),
  estado      pedido_estado NOT NULL DEFAULT 'pendiente',   -- tipo ENUM/DOMAIN
  total       monto_positivo NOT NULL,                     -- DOMAIN con CHECK
  creado      TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pedidos_cliente ON pedidos (cliente_id, creado DESC);
```

Anti-patrones de tabla: PK string aleatoria (UUIDv4 agrupado), columnas "god" JSONB cuando la estructura es fija (es schema evasion), tabla sin auditoría temporal, ENUM para dominios vivos.

## Optimización (awesome-copilot postgresql-optimization)

1. EXPLAIN (ANALYZE, BUFFERS) siempre antes de tocar un índice.
2. Índice parcial para el hot path (`WHERE estado='Matriculado'`).
3. Covering index (INCLUDE) para eliminación de heap fetch.
4. GIN para JSONB/arrays/tsvector — con operadores de containment (@>), no ->>.
5. Window functions para reportes (running totals, rankings) en vez de self-joins.
6. CTEs recursivos para jerarquías (carreras → ciclos → unidades).
7. pg_stat_statements como fuente de verdad de qué optimizar.

## Code review (awesome-copilot postgresql-code-review)

- JSONB estructurado + CHECK de shape (`CHECK (data->>'estado' IN (...))`).
- Trigger idiomático con `WHEN (OLD.* IS DISTINCT FROM NEW.*)`.
- RLS para multi-tenant; GRANTs granulares; nunca SELECT *.
- CITEXT para emails; TIMESTAMPTZ por defecto.
- Dominios (CREATE DOMAIN) para validaciones reutilizadas (email, monto).

## Aurora / managed (aws agent-toolkit)

- Cualquier recomendación de infra primero ver la capa: en Aurora el storage se autoescala y las réplicas se crean con un clic, pero el diseño de esquema/índices sigue SIENDO el 90% del problema.
- No aplicaré tuning de instancia (parámetros) sin antes arreglar queries e índices: la evidencia local manda.

## Patrones del proyecto gestion-estudiantes que SOBREVIVEN a PG

- personas raíz 3NF + tablas de rol.
- Unicidad condicional (índice único parcial — forma PG idiomática de la columna generada MySQL).
- Códigos de negocio legibles por tabla secuencias_codigo.
- Bitácora con FK fuerte + snapshots documentados en meta.
- ON CONFLICT para idempotencia de seeds (equivalente de ON DUPLICATE KEY UPDATE).
