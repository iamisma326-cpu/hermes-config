# Testing de BD PostgreSQL — Verificación de migraciones e integridad

## Invariante: toda afirmación "migró bien" necesita EVIDENCIA de 3 niveles

1. **Cantidad**: conteo fila a fila por tabla (origen vs destino).
2. **Identidad**: checksums de columnas críticas (mismo contenido, no solo misma cantidad).
3. **Comportamiento**: los constraints RECHAZAN lo que deben rechazar (pruebas negativas).

## 1. Conteos comparativos (ABORTAN ante divergencia)

```sql
-- En MySQL: SELECT TABLE_NAME, TABLE_ROWS (aprox) — NUNCA confiar en TABLE_ROWS para esto:
-- generar conteos exactos con COUNT(*) por tabla.

-- Script patrón: recorrer el catálogo de ambas BD y comparar
-- (python + psycopg + mariadb, o shells). ABORTA con lista de divergencias.
```

## 2. Checksums de identidad

```sql
-- Orden determinístico + agregación hash (ambos motores tienen md5/string_agg o equivalentes)
SELECT md5(string_agg(codigo || '|' || numero_documento, ',' ORDER BY id)) FROM personas;

-- Para tablas grandes: hashear por rango de PK y comparar por bloques.
```

Columnas críticas por dominio: identidad (documento), dinero (monto exacto — NUMERIC, nunca float), estados (dominio cerrado), fechas.

## 3. Pruebas negativas — cada constraint DEBE fallar

Códigos de error PG: `23505` unique_violation, `23503` foreign_key_violation, `23514` check_violation, `23502` not_null_violation, `P0002` (excepción de función).

```sql
BEGIN;
-- rol fuera de dominio → 23514
INSERT INTO usuarios (codigo, persona_id, usuario, clave_hash, rol, nombre)
  VALUES ('TST', 1, 'tst', 'x', 'Egresado', 'T');   -- si el CHECK lo excluye, DEBE fallar
ROLLBACK;

BEGIN;
-- FK a persona inexistente → 23503
ROLLBACK;

BEGIN;
-- Duplicado de documento → 23505
ROLLBACK;
```

Cubrir TODOS los CHECK/FK/UNIQUE del catálogo — generar la lista y un test por constraint:

```sql
SELECT conname, contype FROM pg_constraint WHERE conrelid = 'usuarios'::regclass;
```

## 4. Verificación estructural

```sql
-- Conteo de tablas/FKs/CHECKs/vistas/índices: origen vs destino
SELECT count(*) FROM information_schema.tables WHERE table_schema='public';
SELECT count(*) FROM pg_constraint WHERE contype='f';   -- FKs
SELECT count(*) FROM pg_constraint WHERE contype='c' AND connamespace='public'::regnamespace;  -- CHECKs
SELECT count(*) FROM pg_views WHERE schemaname='public';
```

OJO migración: PG no crea índice automático en FKs — comparar índices y CREAR los que faltan.

## 5. E2E de la app

La prueba definitiva: la suite E2E completa corriendo contra PG con los mismos seeds — el contrato de la app no debe notar el cambio de motor. Re-seedar ANTES (seed determinista), correr suite completa, 0 FAIL.

## 6. Órden de SQL en pruebas (dependencias)

Tablas raíz primero (personas → usuarios → estudiantes...), o desactivar triggers durante setup: `session_replication_role = replica` (solo superuser; reactivar y validar después).

## Anti-patrones de testing

- Confiar en TABLE_ROWS de MySQL (aproximado por InnoDB) — usar COUNT(*) exacto.
- "Migró bien porque no hubo errores" — sin conteos + checksums + negativas NO hay evidencia.
- Probar solo INSERT felices; el valor de una constraint está en el INSERT que rechaza.
- Migrar con la app viva escribiendo en origen: congelar escrituras o migrar en ventana de quietud.
