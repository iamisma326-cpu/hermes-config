# Code Review — SQL seguro y de calidad (MySQL/MariaDB)

> Fuentes: copilot/sql-code-review (inyección, anti-patrones), copilot/database-data-management, mysql-expert pitfalls.

## Seguridad primero

### Inyección SQL — el chequeo #1 de cualquier review

```sql
-- ❌ CRÍTICO: concatenación de entrada de usuario
"SELECT * FROM usuarios WHERE usuario = '" + input + "'"
f"DELETE FROM ordenes WHERE id = {user_id}"          -- Python f-string
"SELECT ... WHERE codigo='$codigo'"                   -- interpolación PHP vieja

-- ✅ SEGURE: parameterized SIEMPRE (prepared statements)
$stmt = $pdo->prepare('SELECT * FROM usuarios WHERE usuario = ?');
$stmt->execute([$usuario]);
```

Reglas de review:
- Toda query con entrada externa → parámetro `?`, sin excepción.
- `ORDER BY`/limite dinámicos que no parametrizan → whitelist de valores permitidos en la app.
- `LIKE` con input de usuario → escapar `%` y `_` además de parametrizar.
- Verificar que la app usa el driver con prepareds nativos (PDO con emulate prepares OFF: `PDO::ATTR_EMULATE_PREPARES => false`).

### Permisos y exposición

- **Least privilege**: el usuario de la app SOLO `SELECT, INSERT, UPDATE, DELETE` en SU base — nunca root, nunca DROP/ALTER (`GRANT SELECT,INSERT,UPDATE,DELETE ON db.* TO 'app'@'localhost'`).
- Sin `SELECT *` en tablas con columnas sensibles (hashes de contraseña, documentos) — columnas explícitas; las respuestas de API excluyen `clave_hash` por diseño.
- Logs/bitácora de operaciones sensibles (quién validó qué, cuándo).
- Nunca credenciales en el código ni en git — config fuera del repo (config.local/produccion.php, .env, env vars).

## Anti-patrones de estructura (checklist de review)

| # | Patrón | Por qué malo | Corrección |
|---|---|---|---|
| 1 | `SELECT *` | Arrastra columnas nuevas/innecesarias, rompe contrato, BLOBs pesados | Columnas explícitas |
| 2 | JOIN implícito `,` (old style) | Facilita producto cartesiano accidental | `JOIN ... ON` explícito |
| 3 | `DISTINCT` que "arregla" duplicados | Síntoma de JOIN mal planteado | Repensar el JOIN/agregación |
| 4 | Función sobre columna indexada en WHERE | Mata el índice | Reescribir con rango/literal |
| 5 | Subquery correlacionada por fila | N ejecuciones | JOIN o window function |
| 6 | `OFFSET` profundo | Escanea y descarta | Keyset pagination (WHERE id > cursor) |
| 7 | INSERT fila a fila en loop | N round-trips | Multi-VALUES batch (500-5000) |
| 8 | OR complejo de rangos | El optimizador no usa índices bien | `UNION ALL` por rama |
| 9 | Transacción larga con I/O dentro | Locks sostenidos, deadlocks | I/O fuera; transacción corta |
| 10 | String multi-valuado `("A,B,C")` | Viola 1NF | Tabla hija |

## Formato y estilo

```sql
-- ✅ legible: keywords MAYÚSCULAS, alias claros, indentación consistente
SELECT e.codigo, p.apellidos, p.nombres, p.numero_documento AS dni
FROM estudiantes e
JOIN personas p ON p.id = e.persona_id
WHERE e.foto_estado = 'Pendiente'
ORDER BY p.apellidos, p.nombres;
```

- Naming consistente: snake_case SQL ↔ camelCase app con un solo punto de conversión (en gestion_estudiantes: `Tablas::campo/campoJs`).
- Constraints con nombre descriptivo (`fk_`, `chk_`, `uq_`, `idx_`) — un error `CONSTRAINT chk_notas_rango failed` se autodocumenta; `constraint failed` genérico no.
- Nada de palabras reservadas como identificadores (`order`, `group`, `key`).

## Review de schema (DDL)

Checklist al ver un CREATE TABLE / ALTER:
- [ ] Motor InnoDB + utf8mb4 + collation explícito
- [ ] PK adecuada (surrogate BIGINT o natural legible corta; sin UUID random agrupada)
- [ ] Toda FK con índice y con ON DELETE deliberado (RESTRICT por defecto)
- [ ] NOT NULL salvo justificación; DEFAULT donde tenga sentido
- [ ] CHECK de dominio de valores (estados, rangos numéricos, fechas)
- [ ] `creado`/`actualizado` en tablas operativas
- [ ] Comentario SQL en decisiones no obvias (denormalización aceptada, unicidad condicional)

## Reporte de review (formato de salida)

```markdown
## SQL Review — [archivo/query]

### CRÍTICO (bloquea)
1. [L42] Inyección: interpolación de $codigo en DELETE → prepared statement

### ALTO
2. [L67] SELECT * sobre tabla con hash de contraseñas → columnas explícitas

### MEDIO
3. [L88] OFFSET 5000 en paginación → keyset
4. [schema] FK sin índice en matricula_cursos.docente

### BAJO / estilo
5. [L12] JOIN implícito con coma → explícito
```
Cada hallazgo: ubicación + por qué + corrección concreta. CRÍTICO = seguridad o pérdida de datos.
