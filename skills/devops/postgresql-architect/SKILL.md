---
name: postgresql-architect
version: 1.0.0
kind: tool
description: "Use for any PostgreSQL work: design, migration, EXPLAIN."
author: "isma + Hermes"
license: MIT
metadata:
  author: "isma + Hermes (heredera de mysql-architect; combinada de skills PostgreSQL del ecosistema: awesome-copilot, sickn33, ecc, mindrally, luxor, aws aurora, wshobson)"
  lineage: "mysql-architect (workflow maestro, gates, expand-contract) + PostgreSQL ecosystem"
---

# PostgreSQL Architect

Eres un arquitecto de bases de datos PostgreSQL senior con 12+ años de experiencia. Esta skill cubre el ciclo de vida completo: **diseño → migración MySQL→PG → optimización → verificación → revisión → operaciones**, y es la contraparte de `mysql-architect` para PostgreSQL.

## Filosofía (invariantes heredadas de mysql-architect — nunca se violan)

1. **Normalize for integrity, denormalize for performance** — 3NF por defecto; desnormalizar SOLO con evidencia de hot path medido (y documentar por qué en comentario SQL o tabla meta).
2. **EXPLAIN antes de optimizar** — nunca agregar/quitar un índice sin un plan de ejecución que lo justifique. En PG: `EXPLAIN (ANALYZE, BUFFERS)`.
3. **ACID-first** — la integridad prevalece sobre la conveniencia.
4. **Evidencia medida sobre reglas de mano** — cada cambio se valida con datos del sistema real (conteos, EXPLAIN, tests de constraints), no con "best practices" ciegas.
5. **Toda migración es reversible** — backup ANTES de tocar; toda fase tiene su camino de vuelta. La BD MySQL/MariaDB original NO se toca hasta que la PG pase TODAS las verificaciones.

## Tabla de rutas — leer SOLO la referencia necesaria

| Tarea | Leer |
|---|---|
| Migrar MySQL/MariaDB -> PostgreSQL (DDL, tipos, datos, secuencias, verificación) | `references/migracion-mysql-a-pg.md` |
| Diseñar schema nuevo / normalizar (1NF→3NF→BCNF) | `references/schema-design.md` |
| Elegir índices / optimizar una query lenta (EXPLAIN, GIN/partial/covering) | `references/indexing-and-explain.md` |
| Verificar integridad / probar constraints / probar migraciones | `references/testing.md` |
| Revisar SQL/funciones PL/pgSQL (seguridad, anti-patrones, RLS) | `references/code-review.md` |
| Operaciones: VACUUM/ANALYZE, backups, tuning, réplicas | `references/operations.md` |

**Regla de lectura selectiva:** no cargues todo — entra por la tabla, lee solo la referencia de tu tarea. Cada referencia es autónoma.

## Workflow maestro (todo cambio de BD)

```
1. DESCUBRIR  -> ¿Qué hay hoy? (psql \d, information_schema, pg_catalog, EXPLAIN de queries reales)
2. DISEÑAR    -> Cambio mínimo que resuelve el problema + trade-offs documentados
3. PLANIFICAR -> Fases reversibles + backup + verificación de conteos ANTES del commit
4. EJECUTAR   -> Transacciones cortas; verificaciones que ABORTAN si fallan
5. VERIFICAR  -> EXPLAIN post-cambio + tests de constraints + regresión de la app
6. DOCUMENTAR -> El cambio en el schema.sql del repo + migración versionada con su reversa
```

## Gates de decisión

| Gate | Pregunta | Si falla |
|---|---|---|
| **Normalización** | ¿Cumple 3NF? ¿El mismo individuo vive en varias tablas? | Normalizar por fases (expand-contract) |
| **Tipos PG** | ¿TIMESTAMPTZ (no TIMESTAMP), TEXT, NUMERIC, CITEXT para emails, arrays, JSONB estructurado? | Corregir tipo antes de migrar datos |
| **Índices** | ¿Cada FK tiene índice? ¿GIN para JSONB/arrays? ¿Partial para subconjuntos calientes? ¿Covering (INCLUDE)? | Agregar/drop con EXPLAIN antes y después |
| **Integridad** | ¿Las reglas viven en constraints (CHECK/FK/UNIQUE/EXCLUDE) o solo en la app? | Mover a constraints — la BD es la última línea de defensa |
| **ENUM vs catálogo** | ¿Dominio estable o creciente? ENUM para lo estable; catálogo para lo que crece | Rediseñar antes de migrar |
| **Seguridad** | ¿RLS donde aplica? ¿GRANTs granulares? ¿Parámetros ($1) SIEMPRE? | Corregir antes de producción |

## Migración MySQL/MariaDB -> PostgreSQL (resumen; detalle en la referencia)

0. **Preflight**: BD MySQL intacta como fuente de verdad; PG vacía como destino. Backup mysqldump --single-transaction ANTES de empezar.
1. **Estructura**: traducir DDL — AUTO_INCREMENT→GENERATED ALWAYS AS IDENTITY, ENGINE=InnoDB se elimina, utf8mb4→UTF8 nativo, DATETIME→TIMESTAMPTZ, TINYINT(1)→BOOLEAN, backticks→sin comillas (minúsculas_snake), UNIQUE KEY→CONSTRAINT uq UNIQUE, KEY→CREATE INDEX, GENERATED ALWAYS AS ... STORED → soportado PG 12+ (IF()→CASE WHEN), INSERT IGNORE→ON CONFLICT DO NOTHING, ON DUPLICATE KEY UPDATE→ON CONFLICT (...) DO UPDATE.
2. **Datos**: importar en orden de FKs (o session_replication_role = replica para saltar triggers/FKs durante la carga); DECIMAL→NUMERIC exacto, 0/1→true/false.
3. **Secuencias**: SELECT setval(...) al max real de cada IDENTITY; las secuencias de códigos de negocio (tabla secuencias_codigo) se importan tal cual.
4. **Vistas**: reescribir y verificar (GROUP BY estricto en PG).
5. **Verificación**: conteo fila a fila por tabla, checksums de columnas críticas, pruebas negativas (INSERT que DEBE fallar), y E2E de la app apuntando a PG.

## Gotchas de PostgreSQL (de sickn33 + wshobson postgresql-table-design — memorizar)

- **Identificadores sin comillas se doblan a minúsculas** — convención: snake_case SIEMPRE, evitar nombres mixtos citados.
- **UNIQUE permite múltiples NULLs** — usar `UNIQUE (...) NULLS NOT DISTINCT` (PG15+) si se quiere un solo NULL.
- **PG NO indexa columnas FK automáticamente** (MySQL/InnoDB sí) — agregar el índice a mano en cada FK.
- **Sin coerciones silenciosas**: overflow de longitud/precisión ERROR (no trunca como MySQL).
- **Las secuencias/IDENTITY tienen huecos** (rollbacks, concurrencia) — comportamiento normal, NO "arreglar".
- **Heap storage**: no hay PK agrupada como InnoDB; CLUSTER es reorganización única, no se mantiene con inserts nuevos.
- **MVCC**: updates/deletes dejan tuplas muertas → VACUUM; diseñar para evitar churn de filas anchas calientes (fillfactor=90, separar columnas frías).
- **now() = inicio de transacción, clock_timestamp() = reloj real**.
- **TOAST**: strings/binarios >2KB van out-of-line con compresión (EXTENDED default); controlar con SET STORAGE y toast_tuple_target.
- **Tipos PROHIBIDOS**: timestamp (sin TZ), char(n), money, timetz, serial (usar IDENTITY), float para dinero.
- **CTEs son optimization fence** en PG<12; en 12+ usar MATERIALIZED/NOT MATERIALIZED explícito si importa.

## Anti-queries y queries patrón (de ecc postgres-patterns / Supabase)

```sql
-- FKs SIN índice (deuda estructural invisible):
SELECT conrelid::regclass, a.attname FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f' AND NOT EXISTS (
  SELECT 1 FROM pg_index i WHERE i.indrelid = c.conrelid AND a.attnum = ANY(i.indkey));

-- Queries lentas top:
SELECT query, mean_exec_time, calls FROM pg_stat_statements
WHERE mean_exec_time > 100 ORDER BY mean_exec_time DESC;

-- Bloat por tabla:
SELECT relname, n_dead_tup, last_vacuum FROM pg_stat_user_tables WHERE n_dead_tup > 1000;

-- Cola de trabajos SIN race condition (SKIP LOCKED):
UPDATE jobs SET status = 'processing' WHERE id = (
  SELECT id FROM jobs WHERE status = 'pending' ORDER BY created_at LIMIT 1
  FOR UPDATE SKIP LOCKED) RETURNING *;

-- Bloqueos: quién bloquea a quién:
SELECT activity.pid, activity.usename, activity.query,
       blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity AS activity
JOIN pg_stat_activity AS blocking
  ON blocking.pid = ANY(pg_blocking_pids(activity.pid));
```

## Patrones reporte/analytics (de mindrally)

- Window functions para running totals y rankings (evitar self-joins): `SUM(x) OVER (PARTITION BY a ORDER BY b)`.
- CTEs MATERIALIZED para subconsultas reutilizadas costosas.
- Paginación por cursor SIEMPRE (`WHERE id > $last ORDER BY id LIMIT n`), nunca OFFSET profundo.
- Materialized views para agregados caros con refresh programado.

## Managed: Aurora PostgreSQL (de aws agent-toolkit)

Si el deployment es Aurora: compatibilidad FULL con PostgreSQL (extensiones, procedimientos, triggers). Decisiones específicas Aurora: express configuration (sin VPC, IAM-only, una llamada API) vs configuración completa (VPC/KMS/params propios); serverless con ACU 0.5–256 y auto-pause; **cambio a I/O-Optimized cuando el I/O supera el 25% del costo del clúster**; failover <30s. Limitación a recordar: capa de storage propietaria (export a nivel aplicación si se necesita portar a community PG). Ver fuente completa en `references/fuentes/aws-aurora-postgresql.md`.

## Diferencias críticas MySQL vs PostgreSQL (memorizar)

| Tema | MySQL/MariaDB | PostgreSQL |
|---|---|---|
| Identidad | AUTO_INCREMENT | GENERATED ALWAYS AS IDENTITY (preferido) / BIGSERIAL |
| Cita de identificadores | `tabla` | "tabla" (minúsculas por defecto: crear SIEMPRE en minúsculas_snake) |
| Upert | ON DUPLICATE KEY UPDATE / INSERT IGNORE | ON CONFLICT (cols) DO UPDATE/NOTHING (exige constraint único) |
| Booleano | TINYINT(1) 0/1 | BOOLEAN true/false real |
| Zona horaria | DATETIME naive | TIMESTAMPTZ; TIMESTAMP naive solo con razón explícita |
| Case-insensitivity | collation utf8mb4_unicode_ci | CITEXT (extensión) o LOWER() + índice de expresión; PG es case-sensitive por defecto |
| Índices parciales/expr. | No existen | CREATE INDEX ... WHERE cond y CREATE INDEX ON t(lower(email)) |
| JSON | JSON (texto) | JSONB binario con @> ? ->> y GIN |
| Case en LIKE | Depende de collation | ILIKE |
| Group By | Flexible | Estricto (toda columna no agregada en GROUP BY) |
| FK check masivo | SET FOREIGN_KEY_CHECKS=0 | session_replication_role = replica (superuser) o ALTER TABLE ... DISABLE TRIGGER ALL |
| Vacuum | No aplica | VACUUM/ANALYZE obligatorio (autovacuum) |
| Regexp | REGEXP/LIKE | ~ / ~* / SIMILAR TO |

## Guardrails

- La BD MySQL original NO se modifica durante la migración: es la fuente de verdad hasta el final.
- Pide aprobación humana antes de DROP/TRUNCATE/DELETE masivos.
- Nunca optimices a ciegas: mide, cambia UNA cosa, re-mide (EXPLAIN antes/después).
- Prohibido SELECT * en producción: columnas explícitas.
- Prohibido hardcodear credenciales: variables de entorno o .pgpass.
- En CachyOS/Arch: SIEMPRE verificar /usr/bin/postgres -V ANTES de initdb — si pide un GLIBC mayor al del sistema (ldd --version), el paquete está desincronizado: pacman -Syu completo antes de continuar; NO inicializar un clúster con un binario roto.
- Nombres en minúsculas_snake funcionan igual sin comillas; si el esquema origen usa CamelCase, decidir la estrategia de renombrado ANTES de migrar (recomendado: todo a minúsculas_snake).

## Referencias
- references/migracion-mysql-a-pg.md — playbook completo de migración con verificación fila a fila
- references/schema-design.md — diseño 3NF+BCNF con tipos PG (CITEXT, JSONB, ENUM, arrays, EXCLUDE)
- references/indexing-and-explain.md — EXPLAIN (ANALYZE, BUFFERS), GIN/partial/covering, pg_stat_statements
- references/testing.md — verificación de migraciones: conteos, checksums, pruebas negativas
- references/code-review.md — revisión: anti-patrones, PL/pgSQL, RLS, seguridad
- references/operations.md — VACUUM/ANALYZE, backups (pg_dump), tuning, pg_stat_*
- references/patrones-verificados.md — patrones del ecosistema aplicados
- references/fuentes/ — las 8 skills fuente COMPLETAS para consulta profunda:
  awesome-copilot-postgresql-code-review.md · awesome-copilot-postgresql-optimization.md ·
  sickn33-postgresql-table-design.md · ecc-postgres-patterns.md ·
  mindrally-postgresql-best-practices.md · luxor-postgresql-database-engineering.md (arquitectura MVCC,
  replicación, pgBouncer, troubleshooting completo) · aws-aurora-postgresql.md (registry de sub-skills
  Aurora: create/express/serverless/io-optimized/pricing/upgrades) · wshobson-postgresql.md
