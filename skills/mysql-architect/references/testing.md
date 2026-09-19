# Testing — Integridad, constraints y pruebas de migración (MySQL/MariaDB)

> Fuentes: petrkindlmann/database-testing (forward AND backward, constraint tests, drift), alirezarezvani (verification loop), copilot/sql-code-review (integrity checks) + experiencia gestion_estudiantes.

## Principios (de qa-skills, adaptados a MySQL)

1. **Probar la migración hacia ADELANTE y hacia ATRÁS.** Si el rollback falla, no puedes recuperarte de un deploy malo. La reversa se prueba con el mecanismo REAL (restaurar backup en copia, re-crear estado viejo), no "confiando".
2. **Los constraints son la primera línea de defensa** — pero solo si de verdad rechazan. Test de cada uno: NOT NULL, UNIQUE, FK, CHECK, ON DELETE CASCADE deben RECHAZAR el dato inválido con el error correcto.
3. **Seed determinístico** — IDs fijos, timestamps fijos. `NOW()`/`uuid()`/random en seed crean tests flaños (no reproducibles).
4. **Aislar estado por test** — transacción con ROLLBACK o BD efímera; tests que comparten estado son order-dependent.
5. **Una aserción de performance que no puede fallar no vale nada** — prueba que el test de EXPLAIN se pone rojo si quitas el índice, antes de confiar en su verde.
6. **Testear la migración real, no el sync del ORM** — `db push`/`synchronize` saltan el camino que producción correrá.

## Test de constraints (cada uno debe RECHAZAR)

```sql
-- La prueba es un intento de INSERT inválido que DEBE fallar:
INSERT INTO estudiantes (codigo, persona_id) VALUES ('E9999', 999999);
-- → ERROR 1452 (23000): Cannot add or update a child row: FK constraint fails  ✓ la FK vive

INSERT INTO personas (tipo_documento, numero_documento, apellidos, nombres)
VALUES ('DNI', '74296138', 'Dup', 'Dup');
-- → ERROR 1062: Duplicate entry ... uq_personas_documento  ✓ la unicidad vive

INSERT INTO notas (codigo, estudiante, unidad, semestre, nota, estado, veces)
VALUES ('N9999','E0001','MAT01','2026-I', 25, 'Aprobado', 1);
-- → CHECK chk_notas_rango violated (nota > 20)  ✓ la regla de negocio vive en la BD
```

En un script de test: capturar el error y ASERTAR el código esperado (1452 FK / 1062 dup / 4025 check en MariaDB), no solo "que falle".

## Auditoría de integridad referencial (anti-joins)

```sql
-- Huérfanos (debe devolver 0 filas):
SELECT h.* FROM tramite_requisitos h
LEFT JOIN tramites p ON p.codigo = h.tramite WHERE p.codigo IS NULL;

-- Brecha intención vs imposición (de qa-skills):
-- Columna que DEBERÍA ser única pero no tiene constraint:
SELECT COUNT(*) total, COUNT(DISTINCT dni) distintos FROM estudiantes;
-- total > distintos → falta UNIQUE (o hay datos sucios que arreglar ANTES del constraint)

-- Columna que debería ser NOT NULL pero admite:
SELECT COUNT(*) FROM tabla WHERE columna_importante IS NULL;
```

## Snapshot comparison (drift detection)

```bash
# Antes de la migración:
mariadb-dump -u root DB --no-data > /tmp/pre.sql
# ... aplicar migración ...
mariadb-dump -u root DB --no-data > /tmp/post.sql
diff /tmp/pre.sql /tmp/post.sql   # SOLO las tablas intencionales deben diferir
```

Y en CI (análogo al `prisma migrate diff` de qa-skills): recrear la BD desde el schema.sql del repo y comparar `information_schema` contra la BD migrada — si divergen, el repo quedó desincronizado (drift).

## El verification loop (de database-designer, ejecutado en las 3 fases)

```
1. Analizar el estado actual     → hallazgos (normalización faltante, índices, constraints)
2. Aplicar el cambio por fases   → cada fase con su E2E de regresión
3. RE-analizar el estado objetivo→ los hallazgos de la pasada 1 deben estar RESUELTOS
4. Smoke del contrato de la app  → los endpoints/responses que la UI consume, intactos
```

Caso real: tras la Fase 3, el smoke verificó 10 contratos (login 5 roles, estudiantes aplanados con DNI, pagos con tipo legible, CRUD estudiante→persona automático, DNI duplicado rechazado, dashboard resuelve vía persona). El E2E 32/32 solo cubre API; el smoke cubre lo que la UI realmente lee.

## Test de migración con datos reales (procedimiento)

```bash
# 1. Copia de la BD real en una BD de prueba:
mariadb -u root -e "CREATE DATABASE test_migracion"
mariadb-dump -u root gestion_estudiantes | mariadb -u root test_migracion

# 2. Correr la migración contra la COPIA (con sus SELECTs de conteo)

# 3. Verificar: conteos, huérfanos, duplicados, y la suite de la app apuntada a la copia

# 4. Solo entonces: backup de la real + migrar la real
```

## Seed determinístico (patrón del seed v2.1.0)

- IDs explícitos y estables (`INSERT INTO personas (id, ...) VALUES (1,...)`) para que los tests dependan de ellos.
- El seed es RE-EJECUTABLE: TRUNCATE de todo (FK-safe con `SET FOREIGN_KEY_CHECKS=0`) + INSERT con valores fijos.
- Timestamps de demo con fechas literales (`'2026-03-11'`), nunca `NOW()` — salvo lo deliberado (ventana de auto-asistencia "activa hoy" con `CURDATE()`, documentado).
- Perfiles por entorno (qa-skills): `test` mínimo 2-3 filas, `demo` curado — en gestion_estudiantes el seed único es `demo` y el E2E lo re-seedea.
