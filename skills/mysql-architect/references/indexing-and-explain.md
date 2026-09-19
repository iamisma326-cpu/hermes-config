# Indexing & EXPLAIN — Optimización basada en evidencia (MySQL/MariaDB)

> Fuentes: planetscale/mysql (indexing + query-optimization), copilot/sql-optimization, sickn33/indexing, alirezarezvani index_optimizer + experiencia gestion_estudiantes.

## Metodología EXPLAIN → optimizar → re-verificar (NUNCA a ciegas)

```
1. Capturar la query REAL del sistema (slow log, handler de la app, o la que el usuario reporta)
2. EXPLAIN antes → guardar el plan (type, key, rows, Extra)
3. Cambiar UNA cosa (un índice, un rewrite)
4. EXPLAIN después → comparar. ¿Mejoró? ¿Sigue ALL/filesort?
5. Si no mejoró → revertir y repensar (no apilar índices "por si acaso")
```

## Lectura de EXPLAIN (banderas rojas)

| Campo | Malo | Bueno |
|---|---|---|
| `type` | `ALL` (full scan) | `const`, `ref`, `range`, `index` |
| `key` | NULL (no usó índice) | El índice esperado |
| `rows` | Millones estimados | Cercano al resultado real |
| `Extra` | `Using filesort`, `Using temporary` | `Using index` (covering) |

`EXPLAIN ANALYZE` (MySQL 8.0.18+/MariaDB 12) ejecuta de verdad y da tiempos reales — preferirlo sobre EXPLAIN estimado cuando esté disponible.

## Cuándo indexar (y cuándo NO)

```
INDEXAR:
├── Columnas de WHERE frecuentes
├── Columnas de JOIN (TODA FK debe tener índice — InnoDB no lo crea solo para FKs)
├── ORDER BY / GROUP BY
└── UNIQUE de negocio

NO indexar (over-indexing):
├── Tablas write-heavy con writes frecuentes y reads ocasionales
├── Cardinalidad baja (sexo, boolean) — el optimizador ignora el índice
├── Columnas rara vez consultadas
└── Índice que es prefijo izquierdo de otro (redundante → DROP con EXPLAIN de respaldo)
```

**Caso real:** `idx_matriculas_semestre(semestre)` dropeado — era prefijo izquierdo de `idx_matriculas_filtro(semestre, carrera, turno, estado)`; costaba escritura sin dar nada. Y `idx_notas_estudiante_sem(estudiante, semestre)` agregado porque la query más caliente del sistema (récord de notas) usaba una FK de cardinalidad 2.

## Índices compuestos — la regla que importa

**Orden: igualdad primero, rango/orden después** (leftmost prefix):

```sql
-- Query: WHERE semestre=? AND carrera=? AND estado=? ORDER BY turno
CREATE INDEX idx_bueno ON matriculas (semestre, carrera, estado, turno);
-- semestre/carrera/estado (igualdad) primero; turno (orden) al final

-- Un predicado de RANGO corta el índice: las columnas siguientes no se usan
WHERE fecha >= '2026-01-01' AND estado = 'A'   →  INDEX (estado, fecha)  ✓
                                                →  INDEX (fecha, estado)  ✗ (estado deja de usarse tras el rango)
```

- El índice secundario incluye la PK implícitamente (en InnoDB) → `(a, b)` sobre PK id ya cubre `SELECT a, b, id`.
- Prefix index para strings largos: `INDEX (nombre(20))` — menos espacio, misma utilidad práctica.
- Covering index (`Using index`): si el SELECT solo toca columnas del índice, InnoDB ni toca la tabla.

## Anti-patrones de query (de copilot/sql-optimization)

```sql
-- Función sobre columna indexada mata el índice:
WHERE YEAR(fecha) = 2026           ✗
WHERE fecha >= '2026-01-01' AND fecha < '2027-01-01'   ✓

-- SELECT * en producción:
SELECT * FROM estudiantes e JOIN personas p ...          ✗
SELECT e.codigo, p.apellidos, p.nombres FROM ...         ✓

-- OFFSET profundo (página 500):
LIMIT 20 OFFSET 10000            ✗ (escanea y descarta 10020)
WHERE id > :ultimo_id LIMIT 20   ✓ (cursor/keyset pagination)

-- Correlated subquery por fila → JOIN o window function:
SELECT p.*, (SELECT AVG(precio) FROM productos p2 WHERE p2.cat = p.cat) ✗
SELECT *, AVG(precio) OVER (PARTITION BY cat) ✓

-- INSERT fila a fila → batch:
INSERT INTO t VALUES (...),(...),(...)   -- 500-5000 por batch
```

## N+1 queries (el asesino silencioso de ORMs)

Síntoma: loop de la app que hace 1 query por fila (100 estudiantes = 101 queries).
Detección: `SELECT * FROM sys.statements_with_full_table_scans` o contar queries por request en el slow log.
Cura: JOIN único, `IN (...)` batch, o eager loading del ORM. En la API de gestion_estudiantes los trámites embeben sus requisitos en el mismo SELECT (evita N+1 desde la UI).

## Auditoría de índices existentes (comandos reales)

```sql
-- FKs sin índice explícito (deben ser 0):
SELECT k.TABLE_NAME, k.COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE k
LEFT JOIN information_schema.STATISTICS s
  ON s.TABLE_SCHEMA=k.TABLE_SCHEMA AND s.TABLE_NAME=k.TABLE_NAME AND s.COLUMN_NAME=k.COLUMN_NAME
WHERE k.TABLE_SCHEMA='DB' AND k.REFERENCED_TABLE_NAME IS NOT NULL AND s.INDEX_NAME IS NULL;

-- Índices redundantes (prefijo izquierdo de otro índice de la misma tabla):
SELECT t.TABLE_NAME, GROUP_CONCAT(INDEX_NAME) FROM information_schema.STATISTICS t
WHERE TABLE_SCHEMA='DB' GROUP BY TABLE_NAME, COLUMN_NAME HAVING COUNT(*) > 1;
-- (refinar: comparar secuencias de columnas de cada índice)

-- Índices sin uso desde el arranque (performance_schema, MySQL 8):
SELECT object_name, index_name, count_read
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE count_read = 0 AND object_schema NOT IN ('mysql','sys');
```

## Tablas grandes / particionado (umbral planetscale)

- Time-series >50M filas o tabla >100M filas → particionar por RANGE de fecha.
- Planificar ANTES: el retrofit es rebuild completo (MySQL/MariaDB no reparticiona online).
- La columna de partición debe estar en toda PK/UNIQUE; siempre `MAXVALUE` catch-all.
