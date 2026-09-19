# Patterns & Pitfalls — vanilla JS + localStorage admin apps

Session-tested debugging paths behind the SKILL.md lessons. Each item: symptom → root cause → fix.

## 1. Seed version lockout (user-facing, invisible to you)

- **Symptom**: user types correct NEW credentials, gets "usuario o contraseña incorrectos". You re-check semillas.js and the credentials are right.
- **Cause**: `ia_version` localStorage key not bumped → browser keeps old seeds where the old user (`estudiante/est123`) still exists and the new one (`74296138`) doesn't.
- **Fix**: bump the version on ANY seed change (schema, users, credentials, demo data). Tell the user Ctrl+Shift+R. The seed check is `if (localStorage.getItem("ia_version") === "X.Y.Z") return;` — grep it every time you touch semillas.js.

## 2. Headless flow simulation (composition bugs)

Unit tests pass per-function; flows break in composition. Write `tests/sim-flujo.js`: load sources + localStorage Proxy shim in one `new Function`, replay the user story, `console.log` state after each step. One run caught:

- `deEstudiante()` returning the Anulada record instead of the fresh "En trámite" one → priority-sort helper (En trámite > Matriculado/Reservada > Anulada).
- A second insert path generating code `0004` instead of `MAT-2026I-004` (canonical code format must be applied on EVERY insert path of the entity).
- `Notificaciones` module with zero callers — existed, tested, never invoked by the flow. Grep for call sites of every side-effect module before declaring done.

## 3. Patch discipline (corruption class)

- Two parallel patches to the same file in one turn: one deleted an unrelated neighboring field ("nombre") while the diff looked green. One patch per file per turn; re-read the hunk neighborhood after each batch.
- Deleting a conditional branch can leave orphan string-concat fragments (`"</span></div>" +`) that still pass `node --check` but render broken HTML. After branch removals, read the surrounding `cont.innerHTML` block.
- An old/new swap in a patch returns `no_change` or inverts the edit — re-read the file, don't resend blind.
- Labeled-block leftover (`cont_bind: {` removed but its closing `}` kept) → `missing ) after argument list` three edits in a row. Give up on surgical patches at that point and `write_file` the whole view file.

## 4. TDZ in concatenated sources

`const ROLES` at the bottom of esquema.js, referenced inside ESQUEMA → `ReferenceError: Cannot access 'ROLES' before initialization`, only when the Node test harness concatenates files (browser load order masked it). Constants referenced by ESQUEMA live at the TOP of esquema.js.

## 5. Tests coupled to demo data

`fotosPendientes()[0]` broke when seeding added a pending demo photo (E0004) that sorted first; a pre-seeded carné flipped the "Nueva vs Renovación" assertion. Pick the record under test explicitly (`find(x => x.codigo === "E0005")`) and don't assert on collection indices that demo data can shift. When you add demo data, re-run the whole suite and fix couplings immediately.

## 6. Role-login contract

Dedicated role-picker page before login (user rejected in-form select twice). The account's real rol must equal the picked role or the session is rejected with an explicit message; `VistaLogin.mostrar()` lands on the picker. Demo student: usuario=clave=DNI, name mapped by DNI to the estudiantes record.

## 7. Fase-A mappings for backend-flavored requirements

SMTP → notificaciones table (`emailSimulado: true`) + inbox/bell; uploads → dataURL with mime+size validation in negocio (canvas resize to ~400px for photos, ≤2MB vouchers); PDF → printable view (jsPDF optional later); file storage by DNI folder → just the DNI field on the record. Document each mapping as "Equivalente <stack>" in the plan doc for the user's sustentación.

## 8. Adding a role: silent dead-ends vs visible crashes

When removing a role, orphan references cause crashes (visible). When adding a role, missing references cause **silent dead-ends** — the role exists but can't do anything because nobody wired its menu, permissions, or views. After adding Docente as 5th role, these specific gaps surfaced:

- `index.html` role selector card: added card but forgot to verify the CSS grid handled 5 cards (it did with `auto-fit`, but5 cards on mobile needed `minmax(180px, 1fr)` instead of `minmax(220px, 1fr)`).
- `autenticacion.js` menu map: the new role appeared in ROLES but had no menu entry → blank sidebar after login. Every role must have an explicit menu array.
- `dashboard.js`: no branch for the new role → empty dashboard. Add a branch even if it's just a welcome card.
- Tests: `Sesion.entrar("docente", "doc123")` worked but no test verified the menu was non-empty → add `afirmar(menu.length > 0, "docente tiene menú")`.

**Checklist for adding a role**: esquema.js ROLES → autenticacion.js menu+permissions → index.html role selector card → semillas.js demo user (bump version) → dashboard.js branch → vistas for the role → negocio modules → router registration → tests (positive + boundary) → grep for role name across all files.

## 9. Demo data richness: the "every section populated" pattern

The user said "que haya datos de ejemplos en mesa de trámites y en todos los apartados de los roles" — every role must log in and see populated data. Specific patterns that worked:

- **Trámites**: seed 5 trámites covering all estados (Pendiente, Aprobado, En proceso, Rechazado, Listo para recojo) across different estudiantes. This populates both the Secretaría mesa and the student's "Mis trámites".
- **Approval inboxes**: seed one student with `fotoEstado:"Pendiente"` (e.g. E0004) so the Secretaría bandeja de fotos has data. Seed one pago with `voucherEstado:"Pendiente"` and no voucher file for the Tesorería "approve blocked" demo.
- **Pagos**: seed a mix of matrícula payments + monthly payments + fee payments so the pagos table looks realistic.
- **Notifications**: seed 2-3 for the demo student (Bienvenida + event notifications).
- **Carnés/documents**: seed one emitted carné so the student's "Mis documentos" and carné re-download work.

**Critical pitfall**: adding demo data after tests exist breaks `[0]`-indexed assertions. Always use `.find(x => x.codigo === "E0005")` in tests, never collection indices. Re-run the full suite after every seed change.

## 10. PDF reference document analysis (visual + textual)

When the user provides a PDF (thesis, manual, guide), analyze it BOTH textually and visually:

```bash
pdfinfo file.pdf                          # page count, dimensions
pdftoppm -png -r 60 file.pdf /tmp/p/pag  # render pages as PNG
montage p/pag-0{1,2,3,4,5,6}.png -tile 2x3 -geometry +4+4 -background gray p/m1.png  # 6-page grids
```

Then `vision_analyze` on montages (one call per 6 pages for layout/structure overview) and drill into individual pages for specific details. Combine with `read_file` text extraction for full textual content.

This workflow caught visual details the text layer missed: color-coded course codes (red=failed, green=pass), button annotations ("SELECCIONAR" bubbles), screenshot overlaps with arrows, institutional branding, and table layouts with specific column structures — all essential for replicating the system's UX faithfully.

## 11. Test isolation: shared-state mutation across sequential tests

**Symptom**: a new test fails with "8 evaluaciones (ADS01+COM01): 0" even though the semillas clearly seed 8 evaluaciones and `evaluacionesDelEstudiante` is correct.

**Root cause**: the test harness runs ALL tests in one shared scope. Earlier tests mutate entities that later tests depend on. In this case, flow tests changed E0001's matrícula from "Matriculado" → "En trámite" → "Anulada" across different test functions. The new test expected E0001 to still be "Matriculado" (filter in `evaluacionesDelEstudiante`), but it wasn't.

**This is distinct from pitfall #5** (don't use `[0]` indexing on demo data). Pitfall #5 is about ORDER of demo records. Pitfall #11 is about STATE of shared entities being mutated by earlier tests.

**Three failed fix attempts before the real fix**:
1. Changed filter to include both "Matriculado" and "Reservada" → still 0 (E0001 was "Anulada" or "En trámite").
2. Used a different student E0009 for the test → E0009 doesn't exist in seeds (only E0001-E0005).
3. Inserted a clean matrícula for E0009 inside the test → still 0 because `e09` was null and fell back to E0001.

**The fix that worked**: insert a clean matrícula with a unique `codigo` (like `"MAT-EVAL-TEST"`) for an existing student (E0001) directly inside the test, with an idempotent guard:

```js
const mats = Store.leer("matriculas");
const limpia = mats.find(m => m.codigo === "MAT-EVAL-TEST");
if (!limpia) {
  mats.push({
    codigo: "MAT-EVAL-TEST", estudiante: "E0001", semestre: "2026-I",
    turno: "M", estado: "Matriculado",
    cursos: [{ unidad: "ADS01" }, { unidad: "COM01" }],
    creado: ahoraISO(), actualizado: ahoraISO()
  });
  Store.escribir("matriculas", mats);
}
```

**Lesson**: when a new test depends on a specific entity state, NEVER assume the semillas state survived earlier tests. Insert fresh state within the test itself. Use a unique prefix for test-created codes to avoid collisions with real data.
