# Migrations — Cambios de esquema seguros y reversibles (MySQL/MariaDB)

> Fuentes: alirezarezvani/database-designer (expand-contract, up/down), petrkindlmann/database-testing (forward+backward), sickn33/migrations, planetscale/online-ddl + experiencia real gestion_estudiantes (3 fases, 0 datos perdidos).

## Principios

1. **Nunca un cambio rompedor en un paso** — cada fase deja el sistema funcionando.
2. **Backup antes de tocar**: `mysqldump -u root DB --single-transaction --routines --triggers > backup_PRE_$(date +%Y%m%d).sql` — fuera del repo, en disco hasta confirmar estabilidad.
3. **Verificaciones de conteo que ABORTAN**: dentro de la transacción, `SELECT` de control (huérfanos=0, duplicados=0, total esperado) y revisar ANTES del COMMIT.
4. **Todo script de migración lleva su reversa** documentada (o la tabla de respaldo que permite reconstruir).
5. **Probar en copia primero** si hay datos reales en juego.

## Patrón expand-contract (zero-downtime) — versión MySQL

```
EXPAND    → estructura nueva al lado de la vieja (columnas NULL-able, tablas nuevas, sin FKs)
MIGRATE   → poblar datos en UNA transacción + verificaciones de conteo + congelar remitentes
TRANSITION→ la app escribe/lee la nueva (contrato externo intacto), conviven ambas estructuras
CONTRACT  → FKs + NOT NULL, DROP columnas viejas — SOLO cuando la nueva está verificada
```

En MySQL el ALTER de cada fase es transaccional por sentencia (DDL implícito-commit): ejecutar fase por fase como scripts separados, NO todo en un BEGIN...COMMIT gigante.

### Caso real ejecutado (3NF personas — gestion_estudiantes)

```
FASE 1 (estructura paralela — 0 riesgo):
  CREATE TABLE personas (...);                          -- nueva raíz
  ALTER TABLE estudiantes ADD COLUMN persona_id BIGINT UNSIGNED NULL, ADD KEY idx_...;
  -- usuarios, docentes igual; catálogos nuevos (tipos_pago, tipos_tramite...)
  → E2E de regresión VERDE (la app no se entera)

FASE 2 (datos — 1 transacción):
  START TRANSACTION;
  INSERT INTO personas SELECT ... FROM estudiantes WHERE NOT EXISTS (dup por documento);
  INSERT INTO personas SELECT ... FROM docentes (email como doc provisional);
  INSERT INTO datos_remitente ...;                      -- congela DNI/email original (auditoría)
  UPDATE estudiantes JOIN personas ON documento SET persona_id = personas.id;
  -- SELECTs de control: sin_mapear=0, duplicados=0, total=esperado
  COMMIT;

FASE 3 (contrato activo):
  ALTER TABLE estudiantes ADD CONSTRAINT fk_... FOREIGN KEY (persona_id) REFERENCES personas(id),
    MODIFY persona_id BIGINT UNSIGNED NOT NULL,
    DROP COLUMN apellidos, ...;                         -- columnas espejo eliminadas
  -- adaptar la app: mismas respuestas de API vía JOIN (contrato UI intacto)
  → E2E 32/32 + smoke de contrato 10/10
```

## Cambios comunes sin downtime

| Cambio | Procedimiento seguro |
|---|---|
| **Agregar columna** | `ADD COLUMN ... NULL` → backfill por batches → `MODIFY NOT NULL`. Con default constante MySQL 8 lo hace instantáneo (metadata-only) |
| **Agregar índice** | `ALGORITHM=INPLACE, LOCK=NONE` en MySQL 8/MariaDB (equivalente al CONCURRENTLY de Postgres) — testear en replica/staging primero |
| **Eliminar columna** | Dejar de usarla en la app → deploy → `DROP COLUMN` (el paso final de expand-contract) |
| **Renombrar columna** | Nueva columna → copiar datos → app lee la nueva → drop vieja (el RENAME directo rompe la app desplegada) |
| **Cambiar tipo** | Igual que renombrar; verificar truncamiento con SELECT de control antes |

## Backfill sin locks largos

```sql
-- batches de 5000 con auto-join hasta 0 filas:
UPDATE usuarios u
JOIN (SELECT id FROM usuarios WHERE col_nueva IS NULL LIMIT 5000) sub ON sub.id = u.id
SET u.col_nueva = LOWER(u.email);
-- repetir; monitorear locks con SHOW PROCESSLIST / performance_schema
```

## Versionado de migraciones (de database-designer)

```
api/sql/
├── 01_schema.sql            -- estado ACTUAL completo (instalación desde cero)
├── 02_views.sql
├── 03_seed.sql              -- datos demo re-ejecutable (TRUNCATE + INSERT)
└── migraciones/
    ├── 2026-09-10_fase1_3nf_personas.sql
    ├── 2026-09-10_fase2_3nf_migracion_datos.sql   -- con verificaciones de conteo inline
    └── 2026-09-10_fase3_3nf_contrato.sql
```

Regla crítica del repo: **el schema.sql siempre refleja el estado final** — quien instala desde cero obtiene lo mismo que quien migra. La tabla `meta` versiona (`schema_version`, `seed_version`).

## Verificación post-migración (checklist ejecutable)

```sql
-- 1. FKs vigentes y sin huérfanos:
SELECT COUNT(*) FROM hijos h LEFT JOIN padres p ON p.id=h.padre_id WHERE p.id IS NULL;  -- debe ser 0
-- 2. Estructura esperada:
SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='DB' AND TABLE_TYPE='BASE TABLE';
-- 3. Regresión de la app completa (E2E) — la prueba real
```

Migración que pasa `mariadb < script.sql` pero rompe la app NO pasó. Siempre correr la suite de la app después (en gestion_estudiantes: `python3 api/tests/e2e.py`).
