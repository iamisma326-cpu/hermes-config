# Operations — InnoDB, servidor, backups y DDL online (MySQL/MariaDB)

> Fuentes: planetscale/mysql (operations, transactions, connection, replication), mysql-expert §3/§6/§7, copilot. + experiencia tuning gestion_estudiantes (MariaDB 12 local).

## Perfil del servidor (ajustes por escala)

Ajustes aplicados en gestion_estudiantes (small-OLTP, app PHP mismo host) — calibrar según realidad:

| Variable | Valor small-OLTP | Razón |
|---|---|---|
| `innodb_buffer_pool_size` | 192M– (por defecto 128M) | Debe contener el working set; la BD entera ~3MB, margen para BDs vecinas |
| `max_connections` | 60 (defecto 151) | PHP por-petición en un host: 151 es desperdicio; pool/sockets reales < 60 |
| `wait_timeout` / `interactive_timeout` | 120s (defecto 28800) | Conexiones muertas de PHP no deben colgar 8h |
| `innodb_lock_wait_timeout` | 10s (defecto 50) | Fallar rápido y reintentar > colgar la app |
| `slow_query_log` | ON, `long_query_time=1`, `log_queries_not_using_indexes=ON` | El instrumento esencial: sin slow log no hay optimización con evidencia |
| `innodb_flush_log_at_trx_commit` | 1 | ACID completo; solo bajar a 2 con aceptación explícita de riesgo |

Aplicar en vivo (efímero hasta restart): `SET GLOBAL x = y;`
Persistente: archivo .cnf en `/etc/my.cnf.d/` (en gestion_estudiantes documentado en `api/docs/mariadb-gestion.cnf` — el sistema puede requerir sudo; instalarlo es decisión del usuario).

## Salud InnoDB — chequeo de rutina

```sql
-- Motor y formato (todo InnoDB + Dynamic):
SELECT TABLE_NAME, ENGINE, TABLE_ROWS, ROUND((DATA_LENGTH+INDEX_LENGTH)/1024,1) kb, ROW_FORMAT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA='DB' AND ENGINE IS NOT NULL
ORDER BY (DATA_LENGTH+INDEX_LENGTH) DESC;

-- Variables clave del servidor:
SHOW VARIABLES WHERE Variable_name IN ('innodb_buffer_pool_size','max_connections','wait_timeout',
  'innodb_flush_log_at_trx_commit','character_set_server','collation_server','slow_query_log',
  'innodb_file_per_table','max_allowed_packet');

-- Cuellos de botella vivos:
SHOW STATUS LIKE 'Threads_connected';
SHOW ENGINE INNODB STATUS\G    -- deadlocks recientes, waits
```

## Transacciones y locks

- Isolación por defecto **REPEATABLE READ** (gap locks en InnoDB). Contención alta (deadlocks en OLTP concurrido) → `READ COMMITTED`.
- **Orden de acceso consistente** entre transacciones previene deadlocks (si dos flujos tocan `vacantes` y `matriculas`, que ambas lo hagan en el mismo orden).
- Error 1213 (deadlock) → reintentar con backoff, es transitorio por diseño.
- `SELECT ... FOR UPDATE` con cuentagotas — solo en el punto de carrera real (en gestion_estudiantes: reserva de vacantes) y siempre dentro de transacción corta.
- I/O (llamadas API, archivos) FUERA de la transacción.

## DDL online (sin bloquear la app)

```sql
-- MySQL 8 / MariaDB modernos lo hacen solos en la mayoría de casos;
-- explicitarlo documenta la intención y falla temprano si no es posible:
ALTER TABLE tabla ADD INDEX idx_x (col), ALGORITHM=INPLACE, LOCK=NONE;
```
- INPLACE vale para: add index, add/drop column (con default en MySQL 8), drop index, rename column.
- NO online: cambiar tipo de columna, PK, charset de columna → ventana de mantenimiento o expand-contract.
- Testear el ALTER en staging/copia antes — el tiempo de un ALTER no se adivina, se mide.

## Backups

```bash
# Consistente sin bloquear writes (InnoDB):
mariadb-dump -u root gestion_estudiantes --single-transaction --routines --triggers > backup_$(date +%Y%m%d_%H%M).sql

# Restaurar (verificar):
mariadb -u root -e "CREATE DATABASE restaurar_test"
mariadb -u root restaurar_test < backup_XXXX.sql

# Verificación programada: restaurar el backup en BD efímera mensual y correr el E2E contra ella.
```
Reglas: backup antes de CADA migración; el pre-migración se conserva en disco (fuera de git) hasta confirmar estabilidad; probar la restauración, un backup no probado es una esperanza.

## Réplicas y monitoreo (cuando la escala lo pida)

- `SHOW REPLICA STATUS` → `Seconds_Behind_Source` (0 ideal); lecturas del app evitando réplica atrasada tras un write (read-your-writes).
- Slow log como fuente continua de optimización: revisar semanal, `pt-query-digest` si está disponible.
- Conexiones: la app usa pool o conexión por request corta; `max_connections` dimensionado al pool real, no al teórico.

## Checklist de despliegue a producción (cuando la app migra de host)

1. Exportar BD (`--single-transaction`) e importar en el destino ANTES de cambiar la app.
2. Credenciales del destino en config de producción (nunca en git): host, usuario con least privilege, BD.
3. Verificar versión del servidor destino (MySQL vs MariaDB divergen: CHECK enforcement, funciones JSON, generated columns).
4. Smoke de la app completa contra el destino nuevo (E2E si existe, si no curl de los endpoints críticos).
5. Cambiar el DNS/apuntar la app — y vigilar el slow log nuevo las primeras horas.
