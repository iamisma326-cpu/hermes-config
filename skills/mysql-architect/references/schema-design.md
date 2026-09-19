# Schema Design — Normalización y estructura (MySQL/MariaDB)

> Fuentes: planetscale/mysql, sickn33/database-design, alirezarezvani/database-designer, aj-geddes/database-schema-design, moizibnyousaf/database-design + experiencia gestion_estudiantes.

## Decisiones de normalización (THINK, no copiar patrones)

```
NORMALIZAR (tablas separadas) cuando:
├── Datos repetidos entre filas (mismo valor copiado N veces)
├── Actualizar requiere tocar varias tablas/filas (anomalía de actualización)
├── El mismo individuo existe en varias tablas (persona = estudiante Y docente)
└── Las relaciones de negocio son claras y estables

DESNORMALIZAR (duplicar) SOLO cuando:
├── Performance de lectura medida lo exige (hot path con EXPLAIN)
├── El dato rara vez cambia (ciudad de nacimiento)
├── Siempre se consultan juntos y el JOIN cuesta más que el duplicado
└── ← documentar en comentario SQL por qué se aceptó la redundancia
```

**Caso real (gestion_estudiantes):** `usuarios.nombre` quedó duplicado de `personas` — denormalización de lectura aceptada y documentada (evita JOIN en cada request de auth). `estudiantes.dni` en cambio ELIMINADO: la unicidad del documento vive UNA vez en `personas.uq_personas_documento`.

## Formas normales — checklist práctico

| Forma | Regla | Detección rápida |
|---|---|---|
| **1NF** | Valores atómicos, sin grupos repetitivos | `VARCHAR` con "1,2,3" = lista de datos → tabla hija |
| **2NF** | Sin dependencias parciales de PK compuestas | Campo que depende de PARTE de la PK compuesta → tabla propia |
| **3NF** | Sin dependencias transitivas | Campo derivable vía otra tabla (`pagos.tipo ← conceptos.tipo`) → catálogo FK |
| **BCNF** | Todo determinante es clave candidata | Caso raro; revisar cuando haya >1 clave única por tabla |

Patrón típico 3NF que casi todos los sistemas necesitan tarde o temprano:

```sql
-- ANTES: dos entidades duplicando datos de la misma persona
CREATE TABLE estudiantes (codigo, apellidos, nombres, dni, telefono, ...);
CREATE TABLE docentes   (codigo, nombre, apellido, email, telefono, ...);

-- DESPUÉS (3NF): persona raíz + tablas de rol
CREATE TABLE personas (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo_documento VARCHAR(20) NOT NULL DEFAULT 'DNI',
  numero_documento VARCHAR(60) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  nombres VARCHAR(100) NOT NULL,
  sexo CHAR(1) NULL,                      -- nullable: no todos los roles lo tienen
  fecha_nac DATE NULL,
  ...
  UNIQUE KEY uq_personas_documento (tipo_documento, numero_documento)
);
CREATE TABLE estudiantes (codigo VARCHAR(20) PRIMARY KEY,
  persona_id BIGINT UNSIGNED NOT NULL,
  estado_civil VARCHAR(20) NULL, ocupacion VARCHAR(100) NULL,  -- SOLO datos del ROL
  CONSTRAINT fk_estudiantes_persona FOREIGN KEY (persona_id) REFERENCES personas(id));
```

## Primary keys (planetscale — la fuente más seria)

- `BIGINT UNSIGNED AUTO_INCREMENT` para OLTP write-heavy: estrecha, monótona, secuencial en el índice agrupado de InnoDB.
- **UUID random como PK agrupada = veneno** en InnoDB (page splits + cache misses); si necesitas ID externo, ponla en columna UNIQUE secundaria.
- ULID (ordenable por tiempo) como término medio en sistemas distribuidos.
- Claves naturales de negocio (`E0001`, `MAT-2026I-001`) son legibles y válidas si son estables — mantenerlas como PK VARCHAR corta o como UNIQUE + surrogate interno.
- PK compuesta útil para tablas de unión: `(matricula, unidad)`.

## Data types (MySQL específico)

- `utf8mb4` SIEMPRE (utf8 de 3 bytes no soporta emoji ni algunos caracteres).
- `DATETIME` sobre `TIMESTAMP` (rango 1970-2038 del TIMESTAMP; DATETIME llega a 9999) — ojo: la zona horaria se maneja en la app.
- `DECIMAL(10,2)` para dinero, NUNCA FLOAT/DOUBLE.
- `TINYINT(1)` para booleanos; `ENUM` evitar → tabla de catálogo (lookup table): el ENUM nuevo valor exige ALTER, el catálogo solo INSERT.
- BLOBs pesados (fotos, PDFs) fuera de la tabla caliente o en tabla `archivos` separada con `(entidad, registro, tipo_documento)` — el SELECT frecuente no arrastra MEDIUMBLOB.
- `JSON` válido para datos flexibles con índice parcial; NO como excusa para no diseñar (ver guardrails).

## Constraints — la BD es la última línea de defensa

Reglas de negocio en constraints, no solo en la app (la app cambia, la constraint no):

```sql
CHECK (monto >= 0.01), CHECK (estado IN ('Pendiente','Aprobado')),  -- MaríaDB 10.2+/MySQL 8
CHECK (fecha_inicio < fecha_fin),
UNIQUE (estudiante, semestre, estado_vigente),  -- máx 1 matrícula no-anulada por estudiante/semestre
```

Truco idempotencia/unicidad condicional con columna generada (MySQL 5.7+/MariaDB):
```sql
estado_vigente VARCHAR(20) GENERATED ALWAYS AS (IF(estado='Anulada', NULL, estado)) STORED
-- + UNIQUE(estudiante, semestre, estado_vigente): NULL no colisiona → permite N anuladas, 1 vigente
```

## ON DELETE por relación

| Acción | Cuándo |
|---|---|
| `CASCADE` | Hijo sin sentido sin padre (sesiones, requisitos de un trámite) |
| `SET NULL` | Referencia opcional (docente de un horario) |
| `RESTRICT` | Defecto — protege contra borrados accidentales con datos vivos |

## Naming y metadatos

- snake_case consistente; FKs `fk_tabla_col`, checks `chk_tabla_regla`, índices `idx_tabla_proposito` — el nombre documenta la intención.
- `creado DATETIME DEFAULT CURRENT_TIMESTAMP` + `actualizado ... ON UPDATE CURRENT_TIMESTAMP` en TODAS las tablas operativas.
- Tabla `meta (clave, valor)` para versionar schema/seed — y tabla `secuencias_codigo` si la app genera códigos legibles.
