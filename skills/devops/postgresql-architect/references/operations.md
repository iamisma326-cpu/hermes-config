# Operaciones PostgreSQL — backups, maintenance, tuning

## Backup / restore

```bash
# Dump lógico consistente (equivalente de mysqldump --single-transaction)
pg_dump -Fc -d gestion_estudiantes -f backup_$(date +%F).dump

# Restore
pg_restore -d gestion_estudiantes -j 4 backup.dump

# Dump solo esquema / solo datos
pg_dump -s -d gestion_estudiantes > esquema.sql
pg_dump -a -d gestion_estudiantes > datos.sql

# Backup físico (PITR): pg_basebackup + WAL archiving — para exigencias de RPO
```

Retención: diarios × 7, semanales × 4, mensuales × 6 (ajustar al negocio). Verificar restaurabilidad UNA VEZ al mes (un backup no probado no es backup).

## VACUUM / ANALYZE

- MVCC genera versiones muertas: VACUUM las reclama (autovacuum por defecto, verificar que corre).
- `VACUUM ANALYZE` manual tras cargas masivas / migraciones.
- Bloat: `pg_stat_user_tables.n_dead_tup` alto sostenido → revisar autovacuum thresholds o `VACUUM FULL` (bloquea — ventana de mantenimiento; alternativa: pg_repack).
- `VACUUM FREEZE` y wraparound: monitorear `datfrozenxid`.

## Tuning esencial de postgresql.conf

| Parámetro | Regla de arranque |
|---|---|
| shared_buffers | 25% RAM |
| effective_cache_size | 50-75% RAM (no asigna, informa al planner) |
| work_mem | 32-64MB (por sort/hash; cuidado con conexiones ×) |
| maintenance_work_mem | 512MB-1GB (VACUUM, index build) |
| max_connections | bajo (50-100) + pgBouncer si la app abre muchas |
| random_page_cost | 1.1 con SSD (default 4.0 pensado para spindle) |
| log_min_duration_statement | 500ms (slow log) |

## Monitoreo

```sql
-- Conexiones por estado
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Tablas más accedidas / índices sin uso
SELECT relname, seq_scan, idx_scan FROM pg_stat_user_tables ORDER BY seq_scan DESC LIMIT 10;
SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0;

-- Tamaño de BD y tablas
SELECT pg_size_pretty(pg_database_size(current_database()));
```

pg_stat_statements para el top de queries (activarlo en shared_preload_libraries + CREATE EXTENSION).

## Extensión pgBouncer / connection pooling

PHP por proceso + BD dedicada: transaccionar con `pdo_pgsql` abre conexiones por request. Con >50 conexiones concurrentes: pgBouncer en modo transaction.

## Versiones y upgrades

- Minor: `pacman -Syu postgresql` + restart (leer siempre el aviso de Arch: a veces exige pg_upgrade).
- Major: pg_upgrade --link (downtime corto) o réplica lógica (casi cero downtime).
- SIEMPRE: pg_dump completo ANTES de un upgrade major.

## Rituales

- Diario (automático): backup + envío de pg_stat_statements top-10 si hay lentitud reportada.
- Semanal: revisar índices sin uso, n_dead_tup, tamaño de BD.
- Mensual: restaurar un backup en BD scratch y correr tests.
