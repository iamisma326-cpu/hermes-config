# Migración MySQL/MariaDB -> PostgreSQL — Playbook completo

> Patrón probado en gestion_estudiantes (56 tablas, 99 FKs, 58 CHECKs, 4 vistas). Fase de migración ejecutada con verificación fila a fila.

## Principios

1. **La BD origen es la fuente de verdad y NO se toca** hasta que la PG destino pase todas las verificaciones (conteos + checksums + pruebas negativas + E2E).
2. **Cada fase es reversible**: el dump de origen queda en disco; la PG destino se puede recrear de cero con los scripts versionados.
3. **Verificación que ABORTA**: cualquier divergencia de conteos detiene la migración antes de declararla exitosa.

## Fase 0 — Preflight

```bash
# Backup de origen ANTES de todo (fuera del repo, conservar hasta confirmar estabilidad)
mysqldump --single-transaction -u root gestion_estudiantes > backup_pre_migracion_$(date +%F).sql

# Verificar binarios de destino (CachyOS/Arch: PG puede estar desincronizado con glibc)
/usr/bin/postgres -V        # debe responder con la versión, no con error GLIBC
ldd --version               # si postgres pide GLIBC mayor → pacman -Syu completo ANTES
```

Inicializar el clúster (solo la primera vez):
```bash
sudo su -l postgres -c "initdb --locale=C.UTF-8 --encoding=UTF8 -D '/var/lib/postgres/data'"
sudo systemctl enable --now postgresql
```

## Fase 1 — Traducción de DDL (estructura)

Reglas de traducción verificadas (tabla por tabla):

| MySQL/MariaDB | PostgreSQL |
|---|---|
| `id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` | `id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` |
| `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=...` | (se elimina; PG es UTF-8 nativo) |
| `` `tabla` `` (backticks) | sin comillas — nombres en minúsculas_snake |
| `VARCHAR(n)` | `VARCHAR(n)` o `TEXT` (TEXT es preferido salvo que se quiera limitar) |
| `DATETIME DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ DEFAULT now()` |
| `ON UPDATE CURRENT_TIMESTAMP` | trigger `BEFORE UPDATE` que setee `actualizado = now()` (o dejarlo a la app) |
| `TINYINT(1)` (booleano semántico) | `BOOLEAN` |
| `TINYINT(1) DEFAULT 0` (flag) | `BOOLEAN DEFAULT false` (importar 0/1 → false/true) |
| `DECIMAL(10,2)` | `NUMERIC(10,2)` (equivalente exacto) |
| `UNIQUE KEY uq_x (a, b)` | `CONSTRAINT uq_x UNIQUE (a, b)` dentro del CREATE TABLE |
| `KEY idx_x (a, b)` | `CREATE INDEX idx_x ON tabla (a, b);` FUERA del CREATE |
| `CONSTRAINT fk_x FOREIGN KEY ... REFERENCES ...` | igual (naming conservado) |
| `CONSTRAINT chk_x CHECK (...)` | igual (sintaxis compatible; verificada cláusula por cláusula) |
| `col TINYINT(4) GENERATED ALWAYS AS (IF(estado='X',1,NULL)) STORED` | `col INT GENERATED ALWAYS AS (CASE WHEN estado='X' THEN 1 ELSE NULL END) STORED` |
| `UNIQUE KEY (a, col_generada)` | igual — la unicidad condicional SOBREVIVE en PG (probado) |
| `MEDIUMBLOB/BLOB` | `BYTEA` |
| Comentario de tabla `COMMENT='...'` | `COMMENT ON TABLE tabla IS '...'` (separado) |

Estrategia de generación: escribir un `01_schema_pg.sql` NUEVO (no transformar el dump a ciegas) — el esquema PG es el artefacto versionado del repo, con el mismo orden de tablas y los mismos nombres de constraints que el origen (fk_tabla_col, chk_tabla_regla, uq_tabla_regla, idx_tabla_proposito). Los `CREATE INDEX` van al final (después de las FKs) para acelerar la carga.

## Fase 2 — Carga de datos

Opciones (en orden de preferencia):
1. **COPY desde TSV/CSV** — el más rápido: `mariadb -u root BD -e "SELECT * FROM tabla" --skip-column-names | psql -c "COPY tabla FROM STDIN"` (cuidado con tabuladores embebidos; para filas con BLOB/bytea usar CSV con `\copy`).
2. **INSERTs por tabla generados** — para volúmenes pequeños (demo/seeds): legibles y re-ejecutables.
3. `session_replication_role = replica` (superuser) para desactivar triggers/FKs durante la carga masiva — después reactivar y validar con queries de huérfanos.

Conversión de valores durante la carga:
- DECIMAL → NUMERIC directo (sin cast intermedio: nunca pasar por float).
- TINYINT 0/1 → false/true (castear explícito en el COPY: `COPY ... (col_bool)` con transform o importar a staging y `UPDATE ... SET col = col::int::boolean`).
- Fechas DATE/DATETIME idénticas; si el DATETIME origen era naive local, decidir zona (TIMESTAMPTZ asume la TZ del servidor: documentarla).
- Códigos de negocio ('E0001', 'MAT-2026I-001') son VARCHAR: copian tal cual.

## Fase 3 — Secuencias

- Cada `GENERATED ALWAYS AS IDENTITY` crea una secuencia interna: después de cargar datos con IDs explícitos, sincronizar:
  ```sql
  SELECT setval(pg_get_serial_sequence('personas','id'), (SELECT MAX(id) FROM personas));
  ```
- Si la app usa una tabla de códigos legibles (`secuencias_codigo` con prefijo+ancho+siguiente), se importa tal cual: la lógica de generación vive en la app, no en la BD.

## Fase 4 — Vistas

Reescribir `02_views_pg.sql`. Ojo:
- PG exige GROUP BY estricto (toda columna seleccionada no agregada debe estar en el GROUP BY) — el GROUP BY flexible de MySQL falla en PG.
- Alias y funciones agregadas son compatibles en general; verificar `COUNT(0)` → `COUNT(*)`.

## Fase 5 — Verificación (ABORTA si diverge)

```sql
-- 1. Conteos fila a fila (56 tablas, origen vs destino)
-- generados con un script que compara ambos catálogos y ABORTA ante cualquier !=

-- 2. Checksums de columnas críticas (identidad de datos, no solo cantidad)
SELECT md5(string_agg(p.id::text || p.numero_documento, ',' ORDER BY p.id)) FROM personas p;

-- 3. Pruebas NEGATIVAS: cada constraint DEBE rechazar (en PG el error es 23505 unique_violation / 23503 foreign_key_violation / 23514 check_violation)
INSERT INTO usuarios (codigo, persona_id, usuario, clave_hash, rol, nombre)
  VALUES ('TEST', 1, 'test', 'x', 'RolInexistente', 'Test');  -- debe fallar chk_usuarios_rol
-- doble matrícula vigente → debe fallar uq_mat_vigente
-- préstamo doble → debe fallar uq prestamos vigente
-- FK a persona inexistente → debe fallar

-- 4. Conteo de estructuras: tablas, FKs, CHECKs, índices, vistas (origen vs destino)

-- 5. E2E de la app apuntando a PG (la prueba definitiva del contrato)
```

## Errores típicos y su corrección

| Síntoma | Causa | Corrección |
|---|---|---|
| `relation "tabla" does not exist` en COPY | orden de creación por FKs | crear tablas en orden topológico o crear FKs al final |
| `GLIBC_2.xx not found` al ejecutar postgres | paquete PG desincronizado con glibc del sistema | `pacman -Syu` completo; NO inicializar clúster con binario roto |
| COPY falla en fila N con BLOB | tabulador/salto dentro del dato | CSV con delimitador seguro o staging + UPDATE |
| `ON CONFLICT` no aplica | falta constraint único objetivo | verificar que el índice único llegó en la fase DDL |
| Fechas corridas ±horas | DATETIME naive → TIMESTAMPTZ asume TZ servidor | documentar TZ del clúster y de la app; convertir explícito si hace falta |
| Autovacuum no corre tras carga masiva | tabla nueva sin stats | `VACUUM ANALYZE;` manual tras la carga completa |

## Entrega de la migración

Artefactos versionados en el repo: `01_schema_pg.sql` (estructura), `02_views_pg.sql`, seeds PG (`03_seed_pg.sql`...), script de verificación `verificar_migracion.sql` (conteos+checksums), y `docker-compose.yml`/docs con el comando de restauración. El informe técnico se actualiza con: motor de destino, verificación de conteos, pruebas negativas y diferencias de dialecto aplicadas.
