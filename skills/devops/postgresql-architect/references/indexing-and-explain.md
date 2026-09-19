# Indexing y EXPLAIN en PostgreSQL

## EXPLAIN antes de optimizar (invariante)

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
-- Banderas rojas: Seq Scan en tabla grande, sort costoso, nested loop con muchas iteraciones
```

## Tipos de índice — cuál para qué

| Tipo | Para | Ejemplo |
|---|---|---|
| B-tree (default) | igualdad y rango en escalares | FKs, códigos, fechas |
| GIN | JSONB, arrays, full-text (tsvector) | `USING gin(data)`, `USING gin(tags)` |
| GiST | rangos, geométricos, exclusión | `EXCLUDE USING gist` |
| BRIN | time-series enormes por bloques correlacionados | logs con timestamp monotónico |
| Hash | solo igualdad pura | raramente |

## Índices que MySQL no tiene (aprovecharlos)

```sql
-- PARCIAL: solo el subconjunto caliente — más pequeño, más rápido
CREATE INDEX idx_mat_activas ON matriculas (estudiante) WHERE estado = 'Matriculado';

-- De EXPRESIÓN: indexar la función
CREATE INDEX idx_usuarios_lower ON usuarios (lower(usuario));

-- COVERING (INCLUDE): evitar el heap fetch
CREATE INDEX idx_pagos_cubiertos ON pagos (estudiante) INCLUDE (monto, estado);

-- Multicolumna: orden por el patrón de query (igualdad primero, rango al final)
CREATE INDEX idx_mat_filtro ON matriculas (semestre, carrera, turno, estado);
```

## Reglas heredadas de mysql-architect (siguen valiendo)

1. Toda FK debe tener índice (PG NO crea índices en FKs automáticamente, a diferencia de MySQL ¡verificar en migración!).
2. Sin índices redundantes (prefijo izquierdo de otro).
3. DROP de índices sin uso SOLO con evidencia: `pg_stat_user_indexes.idx_scan = 0`.

## Diagnóstico con catálogos

```sql
-- Queries más costosas
SELECT query, calls, mean_exec_time, rows
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

-- Índices sin uso (candidatos a DROP)
SELECT relname, indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0;

-- Tamaños
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;
```

## JSONB bien indexado

```sql
-- Mal: no usa índice
SELECT * FROM eventos WHERE data->>'tipo' = 'login';
-- Bien: containment + GIN
CREATE INDEX idx_eventos_gin ON eventos USING gin(data);
SELECT * FROM eventos WHERE data @> '{"tipo":"login"}';
```

## Paginación (evitar OFFSET profundo)

```sql
-- Mal en datasets grandes: OFFSET 10000 escanea y descarta
SELECT * FROM productos ORDER BY id OFFSET 10000 LIMIT 20;
-- Bien: cursor (keyset)
SELECT * FROM productos WHERE id > $ultimo_id ORDER BY id LIMIT 20;
```

## VACUUM/ANALYZE

- Tras una carga masiva (migración): `VACUUM ANALYZE;` manual — el autovacuum tarda en llegar a tablas nuevas.
- Bloat visible en `pg_stat_user_tables.n_dead_tup`.
