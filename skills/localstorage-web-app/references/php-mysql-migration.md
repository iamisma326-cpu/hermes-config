# PHP + MySQL Migration (from the localStorage simulation)

Trigger: the user asks to give the app a real backend — "instala una base de datos real", "para el backend usa PHP + una BD en MySQL", "haz un estudio completo del flujo". This is the anticipated end-state of this app class, so the migration must reuse every convention the simulation established.

## Study workflow (do this before writing any DDL)

1. **Index the project with codebase-memory-mcp first** (if installed): `index_repository` then `get_architecture(aspects=["overview","structure","entry_points","hotspots","clusters","file_tree"])`. It returns the layer map (datos = core with all fan-in, negocio/ui = entry), hotspots (the functions every module calls), and functional clusters — an instant map that replaces an hour of grep. ~500 tokens per structural query vs file-by-file reading.
2. **Read the source-of-truth files in this order**: `js/datos/esquema.js` (entity defs, enums, validation rules — this IS the schema), `js/datos/store.js` (CRUD semantics, code-generation, the `{ok, registro|errores}` contract), `js/datos/semillas.js` (exact code formats: `E0001`, `MAT-2026I-001`, `R0001`, seed credentials), then each `js/negocio/*.js` module (flows, state machines, side effects), then map vistas→negocio calls to derive the endpoint list.
3. **Verify the live stack before writing commands into the plan**: `php -v`, `php -m | grep -iE "pdo|mysql"` (need pdo_mysql), `mariadb --version`, `systemctl is-active mariadb`. On CachyOS/Arch: the client binary is `mariadb` — `mysql` is a deprecated alias that still works; server package is `mariadb` (check `pacman -Qs mariadb`). Never assume; a plan whose commands don't match the machine destroys trust on step 1.
4. Look for the **implicit identity mappings** the simulation fakes — e.g. usuario(Estudiante)→estudiante record is resolved by DNI match with a name-heuristic fallback (`_estudianteDelUsuario`). In the DB this becomes a real FK (usuarios.codigo ↔ estudiantes via DNI column or a dedicated link), and the heuristic dies.
5. If the user is in autonomous mode and a clarify question times out, proceed with the recommended options and label the assumptions in the plan ("Decisiones tomadas: ... si prefieres lo contrario se cambia antes de ejecutar").

## Expert schema patterns for this app class

- **Preserve visible codes as VARCHAR PKs** (`E0001`, `MAT-2026I-001`, `T0001`). Do NOT switch to bare AUTO_INCREMENT integers — the codes appear in printables, notifications, and the user's mental model. Replace `Store.siguienteId` with a `secuencias_codigo` table: `SELECT siguiente FROM secuencias_codigo WHERE entidad=? FOR UPDATE` + increment, inside the same transaction as the INSERT. Codes with composite formats (`MAT-<semestre>-NNN`) compose the prefix from the active semester at API level; the table only tracks the numeric suffix.
- **"Unique except soft-state" via generated column**: the business rule "max ONE non-anulada matrícula per estudiante+semestre" (states En trámite/Matriculado/Reservada mutually exclusive, multiple Anulada allowed) cannot be a plain UNIQUE(estudiante, semestre, estado). The clean MariaDB/MySQL solution:
  ```sql
  estado_vigente VARCHAR(20) GENERATED ALWAYS AS (IF(estado='Anulada', NULL, estado)) STORED,
  UNIQUE KEY uq_mat_vigente (estudiante, semestre, estado_vigente)
  ```
  NULLs escape the unique index, so anulada records duplicate freely while vigente states stay unique at the DB level.
- **Composite upserts → UNIQUE constraints**: every business-layer upsert found in the study becomes a UNIQUE key — notas (estudiante, unidad, semestre), evaluaciones (unidad, semestre, tipo), sílabos (curso, semestre), encuestas_respuestas (encuesta, estudiante), certificados_externos (estudiante, curso), asistencias (estudiante, unidad, fecha), carnes (tramite — idempotent emission), vacantes (semestre, carrera, turno). The API then does `INSERT ... ON DUPLICATE KEY UPDATE` or check-then-update inside the request.
- **Enums as VARCHAR + CHECK with the EXACT Spanish strings** from esquema.js (`'En trámite'`, `'Matriculado'`, `'Listo para recojo'`). Do not normalize to English or codes — the API responses feed the UI chips and error messages verbatim.
- **Centralize ALL blobs in one `archivos` table** (id, entidad, registro, tipo_documento, mime, tamano, datos MEDIUMBLOB) with one download endpoint `/api/archivos/{id}`, plus a dataURL-compat endpoint so `<img src=data:...>` UI keeps working unchanged. Size caps enforced at API level, mirroring the JS limits (voucher ≤2.5MB, foto ≤1.2MB).
- **JS-computed aggregates → SQL views**: promedio ponderado por créditos, % asistencia por curso, participación de encuestas, vacantes ocupadas (COUNT GROUP BY). Each replaces a `.filter().reduce()` loop; each view exists because a specific negocio function needs it.
- **Transactions for the oversell-sensitive spots**: vacancy consumption on conformidad (`SELECT ... FOR UPDATE` on the vacante row or the COUNT query, then UPDATE matrícula), cambio-de-turno application (validate destination vacancies + update matrícula + update trámite atomically), semester activation (deactivate previous + activate new in one transaction), code generation (always inside the INSERT transaction).
- **Password migration with rehash-on-login**: the simulation uses unsalted djb2 (`hashSimple` → `"h"+base36`). Port it exactly to PHP — `(($h << 5) + $h + ord($c)) & 0xFFFFFFFF` replicates JS `>>> 0` — then on login: if `clave_hash` starts with `'h'`, verify with hash_simple() and immediately UPDATE to `password_hash(...)`; else `password_verify()`. Seeds get bcrypt from day one (`php -r "echo password_hash('admin123', PASSWORD_DEFAULT);"` — never invent a hash string).
- **Least privilege**: dedicated app user with SELECT/INSERT/UPDATE/DELETE only; separate admin user for schema/seed scripts. utf8mb4 + utf8mb4_unicode_ci everywhere (roles carry accents: 'Secretaría', 'Tesorería').
- **Index justification discipline**: every index in the DDL must cite the negocio function it serves (idx_matriculas_filtro → `ocupadas()`, idx_pagos_voucher_pend → `vouchersPendientes()`, idx_horarios_docente → `cursosDelDocente()`). If you can't name the query, don't add the index.

## API design that makes the frontend migration mechanical

- Keep the **Store response contract identical**: `{ok: true, registro} | {ok: false, errores: [...]}` with the same Spanish error strings ("El DNI ya está registrado", "No hay vacantes disponibles en..."). Then the frontend adapter is a drop-in `Api` module with the same method names (leer/obtener/insertar/actualizar/eliminar/buscar) — the only mechanical change is async/await in views.
- Same-origin token auth: `Authorization: Bearer` + a `sesiones` table (replaces `ia_sesion` localStorage); token in `localStorage['ia_token']` following the same pattern the app already uses.
- Workflow endpoints wrap the negocio verbs (not raw CRUD): `/api/matriculas/{cod}/conformidad`, `/api/pagos/{cod}/validar-voucher`, `/api/tramites/{cod}/estado` — the state machines live server-side now; role checks replicate the `puede*()` matrix exactly.
- PDO settings that matter: `ATTR_EMULATE_PREPARES => false` + `ERRMODE_EXCEPTION`; never string-concatenate SQL even for ORDER BY clauses (whitelist column names).
- Dev serving: `php -S localhost:8870 router.php` where router.php serves the static app files AND maps `/api/*` to the front controller — one origin so the SPA needs zero CORS config.

## Data migration (don't lose the user's real records)

1. A standalone `export_localstorage.html` loads the existing js/datos layer, reads every `ia_*` key, and downloads one JSON dump.
2. A CLI importer inserts in FK order (catálogos → usuarios → estudiantes → matrículas → pagos → trámites/carnés → académico → recursos), decodes dataURLs into the archivos table, rehashes credentials, and syncs `secuencias_codigo.siguiente = max(n)+1` per entity so the next generated code doesn't collide.
3. Verify by count comparison (exported list lengths vs `SELECT COUNT(*)`) and by logging in with a migrated credential.

## Plan shape that worked

A plan document with: Parte A estudio (flows cited to file:line — the DDL must trace to real calls), Parte B full DDL inline (the implementer should never guess a column type), Parte C API contract, Parte D TDD tasks with exact curl commands and expected JSON, Parte E acceptance criteria as E2E role walkthroughs, Parte F risks. Save under `.hermes/plans/` per the `plan` skill. Each task = one commit; verify each against the live DB with `mariadb -u root <db> -e "..."` before moving on.
