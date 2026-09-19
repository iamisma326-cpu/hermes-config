# Schema Design en PostgreSQL — Normalización y tipos

> Hereda la filosofía 3NF de mysql-architect/schema-design.md, aplicada a los tipos y features exclusivos de PG.

## Decisiones de normalización (THINK, no copiar)

```
NORMALIZAR cuando:
├── Datos repetidos entre filas / el mismo individuo en varias tablas
├── Actualizar requiere tocar varias tablas (anomalía de actualización)
└── Relaciones de negocio claras y estables
DESNORMALIZAR SOLO cuando:
├── Performance de lectura medida lo exige (EXPLAIN del hot path)
├── El dato rara vez cambia
└── ← documentar la decisión en comentario SQL o tabla meta (auditabilidad)
```

Caso real: `personas` raíz + tablas de rol (estudiantes, docentes, practicantes) con FK persona_id; `usuarios.nombre` denormalización de lectura documentada en `meta.denormalizaciones_aceptadas`.

## Primary keys

- `BIGINT GENERATED ALWAYS AS IDENTITY` para surrogates (preferido sobre SERIAL/BIGSERIAL: es SQL estándar y protege de INSERT accidentales del id).
- Claves naturales de negocio legibles ('E0001') válidas si estables — VARCHAR PK o UNIQUE + surrogate.
- UUID aleatorio como PK agrupada = page splits; si se necesita UUID, usar UUIDv7 (ordenable) o dejarlo como columna UNIQUE secundaria.
- PK compuesta para tablas de unión: `(matricula, unidad)`.

## Tipos — tabla de decisión rápida

| Necesito | Usar | No usar |
|---|---|---|
| Texto sin límite | TEXT | VARCHAR(255) por reflejo |
| Texto con límite real de negocio | VARCHAR(n) | TEXT + CHECK |
| Email case-insensitive | CITEXT (extensión contrib) + UNIQUE | LOWER() manual en cada query |
| Dinero / montos exactos | NUMERIC(10,2) | FLOAT/DOUBLE (nunca) |
| Booleano | BOOLEAN | TINYINT/CHAR(1) |
| Momento con zona | TIMESTAMPTZ | TIMESTAMP (solo con razón documentada) |
| Solo fecha | DATE | VARCHAR |
| Binario | BYTEA | TEXT con base64 (salvo que la app ya lo hace así) |
| Dominio cerrado ESTABLE | ENUM nativo o DOMAIN + CHECK | VARCHAR + CHECK repetido |
| Dominio que CRECE | tabla catálogo + FK | ENUM (ALTER por cada valor nuevo) |
| Estructura flexible consultable | JSONB + GIN | JSON (texto, sin índice) |
| Lista corta en fila | TEXT[] + GIN | tabla hija si no se consulta por elemento |
| Rango con exclusividad | tstzrange/daterange + EXCLUDE USING gist | dos columnas inicio/fin + trigger |

## Constraints — la BD es la última línea de defensa

```sql
-- Dominios reutilizables
CREATE DOMAIN email_valido AS TEXT CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
CREATE DOMAIN monto_positivo AS NUMERIC(10,2) CHECK (VALUE > 0);

-- CHECK de estado
CONSTRAINT chk_matriculas_estado CHECK (estado IN ('En trámite','Matriculado','Anulada'))

-- Unicidad condicional (idempotencia): parcial único hace el trabajo de la columna generada
CREATE UNIQUE INDEX uq_mat_vigente ON matriculas (estudiante, semestre)
  WHERE estado <> 'Anulada';   -- N anuladas, 1 vigente — sin columna extra

-- Exclusión de solapamiento (no existe en MySQL)
CREATE CONSTRAINT trg_no_solape ON reservas
  EXCLUDE USING gist (equipo WITH =, periodo WITH &&);
```

Nota de migración: la columna generada `estado_vigente + UNIQUE` de MySQL funciona igual en PG 12+, pero el **índice UNIQUE PARCIAL** es la forma idiomática PG (menos columnas). Elegir una y documentar.

## ON DELETE

| Acción | Cuándo |
|---|---|
| CASCADE | Hijo sin sentido sin padre (sesiones, avisos_destinatarios) |
| SET NULL | Referencia opcional |
| RESTRICT | Defecto — protege borrados con datos vivos |

## Naming y metadatos

- snake_case SIEMPRE (PG dobla a minúsculas los no citados: evitar CamelCase).
- FKs `fk_tabla_col`, CHECKs `chk_tabla_regla`, uniques `uq_tabla_regla`, índices `idx_tabla_proposito` — el nombre documenta la intención.
- `creado TIMESTAMPTZ DEFAULT now()`, `actualizado TIMESTAMPTZ DEFAULT now()` + trigger de update.
- `meta (clave, valor)` para versionar schema/seed y documentar denormalizaciones.
