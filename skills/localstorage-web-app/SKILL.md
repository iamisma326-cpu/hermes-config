---
name: localstorage-web-app
description: Use when building a vanilla-JS app with localStorage CRUD.
---

# Vanilla JS Web App with localStorage-Simulated CRUD

Class of project: single-page admin systems (student management, inventory, reservations...) where the user says "sin base de datos todavía", "simulate CRUD in JavaScript", "HTML5, CSS y JS por el momento". Usually adapted from a reference document (thesis, manual, official forms) and expected to migrate to PHP+MySQL later.

## Simulating an EXISTING real system (derive, don't invent)

When the "reference document" is a live system the user already built (their own PHP+MySQL app, with schema SQL, handlers, and official PDFs), the simulator must be **fidelity-first**: the user says "guíanos de la BD que creamos y de todo el proceso" — they will cross-check the mock against the real app. Workflow that worked (2026-09-15, planning a simulator for the user's gestionest1 system):

1. **Extract from the live sources, in this order**: `01_schema.sql` (entities, estados, CHECKs, uniques → the state machines), the handlers' route maps and transition tables (`TramitesHandler`, `MatriculasHandler`), demo seeds (real demo credentials, real record states), and the official PDFs (TUPA = procedures + montos + plazos + autoridad; RI = business rules by article number). Read them with pdftotext + grep for the process chapters — don't skim a 3000-line reglamento linearly.
2. **Write the plan with a per-entity table** (fields, states, FKs) that mirrors the real schema 1:1, and a **reglas de negocio** section citing the source (RQ article, TUPA code, handler route). Every rule in `negocio/` must trace to a real line in the DB or a real article.
3. **Seed = real demo data**: same demo users/credentials, same record states (a matrícula `En trámite` sin voucher, una `Reservada`, trámites en todos los estados) so the user recognizes their own data.
4. **Scope-cut explicitly in the plan** (YAGNI): model only the entities the requested roles/process touch; list what stays OUT (académico, soporte, egresados, expedientes detallados). For a subsystem that exists but won't be wired (e.g. WhatsApp/WAHA real), include it as a **visual placeholder panel** with an explicit "Simulación" note — the user asked "puedes crear visualmente su apartado".
5. **Decision default** (don't stop to ask): full catalog consultable + only the actionable subset wired for the chosen roles; note the lighter alternative in the plan's open questions.

Domain map for this ongoing case (Instituto Argentina + modulo04 simulator): `references/instituto-argentina-dominio.md`.

## Architecture that works (3 layers)

```
app/
├── index.html          # login view + app shell (SPA, hash router)
├── css/                # base.css (tokens) · layout.css · componentes.css · print.css
└── js/
    ├── datos/          # esquema.js (entity defs + validators) · store.js (localStorage CRUD) · semillas.js (seed data)
    ├── negocio/        # one file per domain: validation rules, state transitions, side effects
    └── ui/             # componentes.js (UI helpers) · documentos.js (printables) · router.js · vistas/*.js
```

- Name data-layer functions after classic DAL verbs — `listarTodos/listarPorCodigo/listarPorEstudiante/insertar/actualizar/eliminar` — so the future PHP+MySQL migration maps 1:1 to stored procedures/endpoints.
- Put ALL business rules (payment preconditions, vacancy counts, state machines) in `negocio/`, never in views or store.
- Version the seed: a `localStorage` version key checked at the top of `sembrarTodo()`. Bump it on **any** seed change — schema, yes, but also renamed users, changed demo credentials, new demo records. Forgetting the bump is invisible to you and painful for the user: they type the NEW correct credentials and get "usuario o contraseña incorrectos" because their browser still holds the old seeds (this exact incident happened: demo student renamed + credentials changed, version not bumped, user locked out until Ctrl+Shift+R + reseed).

## Store design lessons (each one was a real bug)

1. **Autogenerate the ID *before* validating**, not after — otherwise the first insert of an auto-id entity always fails validation with "campo obligatorio".
2. **Extract numeric suffix, not all digits**: for prefixed codes like `MAT-2026I-004`, `parseInt(str.replace(/\D/g,''))` gives garbage from the prefix. Use `str.split("-").pop()` then strip non-digits.
3. **Copy before insert** (`Object.assign({}, datos)`): protects against shorthand-property bugs (`{ semestre }` when the local var is `sem` → undefined field) and lets the caller reuse the object.
4. **Re-read after update**: when computing something right after `Store.actualizar(...)`, fetch the fresh record via `Store.obtener` — the local object is stale.
5. Entities should carry `creado/actualizado` timestamps and codes the user never edits; mark read-only fields in the schema so forms render them disabled.
6. **Constants referenced inside `ESQUEMA` must be declared ABOVE it** (top of esquema.js). Wiring a bottom-of-file `const ROLES` into a field (`{ n: "rol", opciones: ROLES }`) throws `ReferenceError: Cannot access 'ROLES' before initialization` — and it surfaced only when the Node test harness concatenated the sources, not in the browser.
7. Wire enum-ish fields to the shared constant anyway: the generic form renderer then offers only valid roles and `Store.validar` rejects anything else — one source of truth for UI and validation, and changing the role list automatically restricts the usuarios form.

## Composite-key upsert pattern

When an entity has a natural composite key (e.g. evaluations identified by `unidad + semestre + tipo`), implement upsert in the business layer rather than auto-generating IDs on every insert:

```js
guardarEvaluacion(datos) {
  const lista = Store.leer("evaluaciones");
  const existente = lista.find(e =>
    e.unidad === datos.unidad && e.semestre === datos.semestre && e.tipo === datos.tipo);
  if (existente) {
    Object.assign(existente, datos, { actualizado: ahoraISO() });
    Store.escribir("evaluaciones", lista);
    return { ok: true, registro: existente };
  }
  return Store.insertar("evaluaciones", { codigo: "EV" + paddedId, ...datos });
}
```

This prevents duplicates and makes "re-scheduling" idempotent. Validate required key fields before the lookup to give a clear error. The upsert key maps to a unique constraint in a future SQL migration.

## Design: never ship generic admin styling

The user rejected a default blue sidebar/tables look ("el diseño es muy genérico"). Load the design skills BEFORE writing CSS: `popular-web-designs` → the **Cal.com** template (monochrome `#242424`/white, Inter, ring-shadow cards `0 0 0 1px rgba(34,42,53,.08)` + diffused shadows, hairline tables, charcoal primary buttons) worked excellently for an institutional admin app. Pair with `make-interfaces-feel-better` for the polish pass (explicit transition properties, never `transition: all`; `:active` scale(.97); `tabular-nums` on tables/amounts; `text-wrap: balance`; antialiased smoothing). Tokens live in `:root` in base.css; print documents (print.css + a `#area-documento` visibility toggle) share the token system so fichas/nóminas/recibos look institutional on paper.

## Responsive checklist (do it in the first CSS pass, not as an afterthought)

- Tables: `.tabla-envuelta{overflow:auto}` + `table{min-width:640px}` inside the media query — columns never collapse.
- `input,select,textarea{font-size:16px}` under 800px → kills iOS focus zoom.
- Sidebar off-canvas ≤800px with overlay; close on outside click via `body:has(.sidebar.abierto) .menu-fondo{opacity:1;pointer-events:auto}` — the `:has()` approach works even though the overlay div is not a sibling of the sidebar.
- Dialogs full-screen ≤640px (`width:100vw;height:100dvh;border-radius:0`); print overlays full-width.
- Use `100dvh`/`100svh` (not `100vh`) for shells and login so mobile browser chrome doesn't clip.
- Hide desktop-only explainer text (`.solo-escritorio` utility) inside mobile forms.

## Testing workflow (verification is not optional)

1. After EVERY file write: `node --check <file>` — sweeping deletions routinely corrupt a neighbor line; catch it immediately. If lint output looks alien (weird tokens, wrong line), suspect the write landed at a corrupted path — check the resolved path, delete any spurious directory, and retry with a clean full `write_file`.
2. Business logic runs headless via the Node harness in `templates/logic-tests.template.js` (copy into `tests/`). It caught 5 real bugs that syntax checks missed. This is also the fallback when interactive browser automation is blocked pending user approval. **The harness only loads the files listed in its `archivos` array at the top** — every new `js/negocio/*.js` module MUST be registered there, or every test touching it dies with `X is not defined` (a cascade of ~14 failures that looks like an app-wide break but is just the loader; happened with RequisitoDocs.js AND recursos.js in one session — same mistake twice).
3. E2E: `python -m http.server 8899` in the app folder, then drive the browser. The route that WORKS on this machine (CachyOS/Hyprland, avoids the browser-use approval-popup dance entirely): launch a **dedicated Chrome** on the lightweight profile `~/.chrome-agent` with `--remote-debugging-port=9222 --remote-allow-origins=* --ozone-platform=wayland` (background=true), then drive it via the CDP helper from the `desktop:linux-desktop-automation` skill (`scripts/fcc_cdp.py`: `get_tab('localhost:8899')` → `Runtime.evaluate`). This is real-browser E2E: actual localStorage, actual hash router, actual DOM — far stronger than headless Function-constructor stubs. Write a one-off `tests/verifica-flujo.py` that logs in via the role card + form dispatch, clicks through the flow, and asserts on `document.body.innerHTML` / `getElementById` presence; delete it after the run (session-specific).
4. Re-run the full logic suite after every user-driven scope change — seed expectations (entity counts, turnos, roles) live in the tests and will catch drift.

For grep-style searches across project files use the `search_files` tool, not shell pipelines (complex `grep -rn ... | grep -v` one-liners can trip command-parser security blocks).

## Test isolation: within-test fresh state insertion

The Node test harness runs all tests in one shared scope — earlier tests mutate entities that later tests depend on. This is **different** from the `[0]`-indexing problem (which is about demo data ordering). Here, a test that changes E0001's matrícula from "Matriculado" to "En trámite" breaks a later test that checks `evaluacionesDelEstudiante("E0001")` because that method filters on `estado === "Matriculado"`.

**Pattern**: when a test needs a specific entity state, insert a fresh record within the test body rather than relying on semillas state:

```js
prueba("evaluacionesDelEstudiante: orden cronológico", () => {
  // Tests previos mutan E0001's matrícula → insertar limpia
  const mats = Store.leer("matriculas");
  if (!mats.find(m => m.codigo === "MAT-EVAL-TEST")) {
    mats.push({
      codigo: "MAT-EVAL-TEST", estudiante: "E0001", semestre: "2026-I",
      turno: "M", estado: "Matriculado",
      cursos: [{ unidad: "ADS01" }, { unidad: "COM01" }],
      creado: ahoraISO(), actualizado: ahoraISO()
    });
    Store.escribir("matriculas", mats);
  }
  // ... assertions ...
});
```

**Guardrail**: use a unique `codigo` prefix like `"MAT-EVAL-TEST"` to avoid colliding with real codes. The idempotent check (`if (!mats.find(...))`) prevents double-insertion if the test is somehow re-run.

This same pattern applies to any entity that earlier tests mutate: notas (a grading test changes a nota from Pendiente to Aprobado), trámites (the flow test creates and advances a trámite), pagos, etc. If your new test depends on a specific state of a shared entity, don't hope the semillas state survived — assert it by inserting fresh.

## Adding or removing a role: full sweep (a role touches 10+ places)

### Removing a role

Removing roles is NOT an `ROLES = [...]` one-liner. Every occurrence must go, or the app keeps dead branches and crashes on deleted helpers. Sweep checklist, in order:

1. `grep -rn "<role names>" js/ tests/ index.html README.md PLAN.md` — error messages in negocio ("solo Administrador y Secretaría"), permission helpers, dashboard access-maps, demo-account help text, doc signatures, comments.
2. `grep -rn "<helper names>" js/ tests/` for the helpers being deleted (e.g. `esJefeLectura`, `carreraJefe`, `filtrarPorCarrera*`) — removing a helper from autenticacion.js while a vista still calls it is a runtime crash the tests won't catch if that vista isn't exercised headless (this exact break happened: tramites.js called `Sesion.filtrarPorCarreraTramite` after the helper was removed).
3. Rewrite the permission helpers in autenticacion.js explicitly (`puedeEditarMatriculas() { return this.esRol("Secretaría"); }`) rather than keeping the merged `"Administrador", "Secretaría"` lists.
4. Update menus/dashboard maps for BOTH remaining roles — the surviving admin-ish role usually inherits the removed roles' exclusive views (Catálogos, Bitácora went to Secretaría).
5. Reword role-attributing copy: who registers payments, who signs printables (`Documentos.pie(["Tesorería", ...])` → Secretaría), demo-credentials block in index.html.
6. Reseed: bump the semillas version key and prune demo users/pay-concepts of removed roles — otherwise old accounts still log in.
7. Tests: add the negative assertions (`!Sesion.entrar("admin", ...).ok`), the new permission boundary (Estudiante can't edit but CAN request trámites), and rerun the whole suite (seed expectations live there).

### Adding a role (reverse sweep)

Adding a role (e.g. Docente as 5th role) is the inverse — you must **create** every touchpoint, not just add a string to `ROLES`. Checklist:

1. `esquema.js`: add to `ROLES` constant (top of file, above ESQUEMA). If the role needs its own entity (e.g. `docentes` with perfil fields), add it to ESQUEMA.
2. `autenticacion.js`: add the role to every relevant permission helper (`puedeEditarMatriculas`, `puedeGestionarTramites`, etc.) OR create new scoped helpers (e.g. `puedeCargarNotas() { return this.esRol("Docente"); }`). Add the role to the menu map — define what pages it sees.
3. `index.html` role selector: add a card with icon, name, and description. The card grid auto-adapts but verify responsive layout with5+ cards (may need `grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))` adjustment).
4. `semillas.js`: create demo user(s) for the new role, bump version. If the role has a profile entity, seed profiles linked to the user.
5. `dashboard.js`: add a branch for the new role in the dashboard switch (what cards/stats it sees).
6. Views: create the vistas the role needs (e.g. `js/ui/vistas/notas.js` for Docente). Register them in the router and in the menu map.
7. Business logic: create negocio modules for the role's domain (e.g. `js/negocio/notas.js`). Wire side-effects (notifications, state transitions) into the relevant events.
8. Tests: add positive assertions (`Sesion.entrar("docente", "doc123").ok`), permission boundaries (Docente can't edit matrículas), and seed expectations. Rerun full suite.
9. Grep for the new role name across ALL files after implementation — catch any place you forgot to wire it.

**Key difference from removing**: when removing, orphan references cause crashes (visible). When adding, missing references cause silent dead-ends (the role exists but can't do anything). Test every action the role should be able to perform.

## Demo data richness: seed across ALL sections

When the user asks for "datos de ejemplos en todos los apartados", they mean every role should log in and see populated data, not empty tables. Checklist per section:

- **Estudiante**: matrícula (at least one in a non-terminal estado so the portal shows the Cero Filas panel), pagos (at least one pending voucher), trámites (mix of estados: Pendiente, Aprobado, En proceso, Rechazado, Listo para recojo), notificaciones (2-3 unread), carné (one emitted), documents.
- **Secretaría**: bandeja vouchers (at least one pending with/without attached file), bandeja fotos (at least one pending, e.g. E0004 with `fotoEstado:"Pendiente"`), matrículas table (mix of estados), trámites mesa (all estados represented), pagos (several recibos), nóminas (rows in the main carrera/ciclo).
- **Tesorería**: bandeja vouchers (2+ pending — one with file, one without to test the "approve blocked without file" guard), pagos list.
- **Administrador**: dashboard stats (non-zero counts), catálogos populated, bitácora entries, usuarios for all roles.
- **Docente** (if exists): at least one assigned curso in `horarios`, one set of notas loaded, one auto-asistencia window (active/expired), one encuesta with results.

**Pitfall**: adding demo data after tests exist breaks index-based test assertions (`[0]`). Always use `.find(x => x.codigo === "E0005")` instead of `[0]` in tests, and re-run the full suite after every seed change.

**Version bump**: every seed change (new records, renamed users, changed credentials) MUST bump the `ia_version` key. The user's browser holds the old seeds and won't reseed without it. This bit THREE separate times in one session (credentials change, role-add seeds, external-courses seeds) — make the bump part of the same patch that changes seed content, never a follow-up.

**External links / platform directories**: when seeding a directory of external services (courses, portals), (a) verify each URL is alive and actually offers what its card claims via `web_search` first — Google Actívate no longer exists (migrated to Grow with Google), Fundación Telefónica's aula closed; dead/renamed links erode trust; (b) **one card per platform** — the user rejected representing one portal's internal courses as multiple cards pointing to the same URL ("no tiene sentido... si es parte del portal MTPE"); mention the portal's notable offerings inside the card name instead; (c) add a regression test `new Set(urls).size === urls.length` (no duplicate links) so the pattern can't creep back; (d) always bump the seed version in the same commit or users keep seeing the old directory.

## PDF reference document analysis workflow

When the user provides a PDF reference (thesis, manual, guide), analyze it visually, not just textually:

1. `pdfinfo <file>.pdf` — page count, dimensions, author.
2. `pdftoppm -png -r 60 <file>.pdf /tmp/<prefix>/pag` — render all pages as PNG (60 DPI is enough for layout/structure).
3. `montage pag-0{1,2,3,4,5,6}.png -tile 2x3 -geometry +4+4 -background gray m1.png` — create grids of 6 pages each for overview analysis with `vision_analyze`.
4. Use `vision_analyze` on montages (cost-efficient: one call per 6 pages) for layout, color, structure; then drill into individual pages for specific details (text in tables, button labels, form fields).
5. Combine with `read_file` text extraction (the anydoc converter handles PDFs) to get the full textual content.

This workflow caught visual details the text layer missed (color-coded course codes, button annotations, screenshot layouts, institutional branding) that were essential for replicating the system's UX.

## Batch-editing discipline (learned applying a 16-file scope cut)

- **Parallel patches to the same file are dangerous**: two edits to esquema.js ran concurrently and one DELETED the neighboring field ("nombre") instead of the intended one — the diff looked green. Prefer one patch per file per turn; after each batch, read the touched hunk back and check the neighborhood, not just the replaced string.
- When the final shape is small, `write_file` the whole file (autenticacion.js, dashboard.js) instead of stacking surgical patches.
- A failed/`no_change` patch usually means old/new got swapped — reread the file rather than re-sending.
- Beware residual lines after deleting a conditional branch (leftover `"</span></div>" +` produced malformed HTML string concatenation that still passes `node --check`).
- After a constant is moved/renamed, run the full Node suite — TDZ/ReferenceErrors hide until sources are concatenated.
- End-to-end smoke: `python -m http.server 8899` + curl every JS resource for 200 (the server log doubles as a load manifest).

## "El usuario no ve lo que yo verifico en el código" — check the SERVING ORIGIN first

Recurring multi-turn failure mode: the user reports a feature (upload buttons, new seed data) as missing; you grep the code, it's all there; you bump versions and re-push; the user STILL doesn't see it. The code was never the problem — **the browser was loading a different origin or a stale cache**. In this session: port 8899 was DOWN (nothing serving the project), `localhost:80` answered with an unrelated Apache LAMP install, and the user's tab held a stale copy from an earlier server. Three pushes of "fixes" did nothing because nothing reached the user.

Definitive debugging order (do this BEFORE touching code again):
1. `ss -tlnp | grep <port>` — is anything actually listening? (8899 was not.)
2. `curl -s http://localhost:<port>/js/datos/semillas.js | grep ia_version` — does the SERVED file match disk? A mismatch = wrong directory or stale reverse proxy.
3. `curl -s http://localhost:80/ | head` — check what else answers on default ports; user tabs pointed at the wrong origin show old code forever.
4. Start the server as a tracked background process (`terminal(background=true)`), re-verify with curl, then give the user the EXACT URL + Ctrl+Shift+R.
5. Prove it end-to-end on the served URL (see CDP route under Testing) — a real-browser run that logs in and finds the buttons is the only proof that survives the user's retry.

Never iterate on more code fixes while the serving-origin question is open.

## Login design: dedicated role-selection page BEFORE the login form

The user rejected both login layouts before converging: first credentials-only (got "el usuario y contraseña de estudiante es incorrecta" complaints), then a `<select>` of roles inside the login card ("me referia que antes de la pagina de login, haya una pagina con diseño profesional de seleccion de roles"). The accepted design is a **separate full-page role picker** that precedes the login:

- `#vista-roles` section: institution brand header (logo + name + subtitle), centered "¿Cómo deseas ingresar?", grid of role cards (`role name + one-line description + arrow`, inline SVG icon in a charcoal tile), hover lift (`translateY(-3px)` + deeper shadow), `:focus-visible` ring, auto-fit responsive grid, footer line. Same monochrome token system as the app.
- Clicking a card stores the chosen role on the view and shows the login form with a "Ingresando como: **X** · cambiar" band (the cambiar link returns to the picker).
- On submit, validate that the account's real rol matches the chosen one — mismatch yields "Esta cuenta corresponde al rol X, no a Y." This also replaces password-reminder hacks: demo credentials stay in a small help block.
- `VistaLogin.mostrar()` (no-session path) must show the ROLE PICKER, not the login form; `App.salir()` then naturally lands back on role selection.

Demo student accounts: user = their real DNI, password = same DNI (user explicitly set this: "el usuario con dni 74296138 debe llamarse Carlos Ismael, Espinoza" with usuario/clave = DNI). The user↔estudiante record mapping is by DNI match, done deterministically, not by name-splits. Also: seeding rich demo data across ALL sections (trámites in every estado, a pending foto for the approval inbox, extra pagos, 2 notifications) is expected — the user asked for it explicitly ("que haya datos de ejemplos en mesa de trámites y en todos los apartados").

## Verifying the whole flow: headless simulation beats test-by-test

Unit tests per function miss **composition bugs** — 31 passing tests and the flow was still broken. Before declaring a flow (e.g. matrícula: iniciar → subir voucher/foto → doble validación → conformidad) working, write a one-off Node script (tests/sim-flujo.js style) that replays the user story end-to-end with seeded data and prints the state after each step. It caught three real bugs in one run, none covered by the unit suite:

1. **"get most relevant record" helpers need state priority, not `.find()[0]`**: `deEstudiante()` returned the ANULADA matrícula when the student had anulada + a fresh "En trámite" one, so the portal showed the dead record. Fix: fetch all, sort by priority map (`{"En trámite":0, "Matriculado":1, "Reservada":1, "Anulada":2}`), return first.
2. **Every insert path must produce the entity's canonical code format**: a second insert path (portal trámite) forgot the `"MAT-" + semestre + "-" + padded` prefix and produced bare `0004`. When code format lives in one registrar, extract it or copy it to every path.
3. **Cross-entity state machines must actually fire**: the `etapa` field existed, notifications module existed, but NOTHING called them (0 notifications after a full flow). Grep for callers of each side-effect module before claiming it works; wire them into every business event (documento recibido/aprobado/rechazado, conformidad final).

**Scope-creep risk for shared state (`let` vs `const` across branches):** when a helper computed in one branch (e.g. `const codEst = this._estudianteDelUsuario()` inside the `rol === "Estudiante"` else-branch) is later referenced by NEW feature code at function level (estudiante-only panels below the shared `cont.innerHTML`), it throws `ReferenceError` and — because `render()` dies mid-way — the whole view renders BLANK ("el inicio está en blanco"). Declare `let codEst = null` at the top of `render()` and assign inside the branch. Verify a blank-view fix by actually invoking `VistaDashboard.render(fakeContainer)` headless (Function-constructor harness with localStorage/document stubs; note the bundle declares its own `UI`/`Documentos` so don't pass those as parameters) and asserting the panels appear in the produced HTML.

Two more flow guards that surfaced: validation inboxes must refuse approving a document with no attached file (voucher without `voucher` dataURL), and tests must not index demo-dependent collections with `[0]` — pick the specific record under test (`.find(x => x.codigo === "E0005")`) or seeding new demo data breaks them (it did, twice: an inbox ordering change and a pre-seeded carné flipped "Nueva" to "Renovación").

## Inline file uploads within forms (the "Adjuntar" pattern)

When a form requires document attachments as part of submission (not post-creation), render the file inputs **inline with the form fields** rather than in a separate upload panel. The user explicitly rejected the separate-panel approach: "la idea es que en el apartado trámites, al hacer nuevo trámite ahí mismo estén los botones para subir copia de dni, foto para el carné".

Implementation pattern:
1. Render each requirement as a row: label + optional chip (e.g. `<span class="chip chip-rojo">PDF obligatorio</span>`) + hidden `<input type="file">` + visible "Adjuntar" button + `<span>` for filename display.
2. Bind each "Adjuntar" button to trigger its hidden input: `input.onchange` reads the filename into the display span and stores `input.dataset.nombre`.
3. On form submit, collect all `input[type=file][data-req-idx]` with files selected. Validate formats **BEFORE creating the record** (e.g. DNI must be `application/pdf` — reject with toast if wrong). Only then call the registrar function.
4. After successful creation, inject attachments via `FileReader.readAsDataURL()` in a countdown pattern: each reader decrements a counter, the last one calls the success handler. This avoids race conditions with multiple async readers.
5. Display: show `📎 nombre.pdf` next to each requirement after file selection, changing from "Sin archivo".

Validation ordering matters: validate file types BEFORE creating the entity. If a DNI requirement comes as an image, block the entire submission with a toast — don't create a half-attached record.

## Config-style CRUD: inline table editing for structured data

When a feature requires configuring multiple related items with the same shape (e.g. 4 evaluation dates per course), use a **config-style table** where each row is an editable form:

1. Render a `<table>` with one row per slot (e.g. Parcial 1, Parcial 2, Examen Final, Proyecto Final). Each row has: fixed label (tipo) + `<input type="date">` + optional `<input type="time">` + `<input type="number">` + `<input type="text">` + status chip + Save/Delete button.
2. Pre-fill inputs from existing records (if the evaluation was already saved). Empty inputs = "Sin programar" chip.
3. Status chips: contextual color by date proximity — "HOY" (amber), "Próxima (3d)" (blue), "Programada" (green), "Realizada" (grey), "Sin programar" (grey).
4. Save button does the upsert (see composite-key pattern above). Delete confirms then removes.
5. After save/delete, call `Router.refrescar()` to re-render with updated state.

This pattern differs from the "Adjuntar" inline-upload pattern (which is about file selection during form creation) — this is about **editing existing structured data in-place**. The user's expectation: "el docente debe poner las evaluaciones en la fecha que indique" = the docente fills in dates per course, per evaluation type, in a single table view.

For the student's read-only view of the same data: render a single consolidated table sorted by date across ALL their courses, with the same status chips. Filter dropdown by course (optional).

## UX patterns for actor-scoped forms and always-available uploads

Two user corrections that converge on one principle — **the logged-in role determines the form, the state does not hide the capability**:

1. **Actor-scoped forms must not offer a selector of themselves.** The student's "+ Solicitar trámite" originally rendered a generic student `<select>` (copied from the staff view). User: "no tiene sentido tener la opción de elegir estudiante si se supone que es del que ingresó". Fix: when `Sesion.esRol("Estudiante")`, render a read-only "Solicitante" input with the resolved name+code and take the entity from the deterministic `_estudianteDelUsuario()` mapping in `guardarNuevo`; keep the `<select>` only for staff roles who legitimately file on behalf of others.
2. **Upload panels are standalone always-visible cards, not branches of the record state.** The voucher+photo upload cards were initially rendered only inside the "En trámite" / "Matriculado" branches, so users with a seeded terminal-state record never saw the buttons (reported repeatedly: "sigo sin ver el botón para subir pdf y foto"). Fix: extract `_panelDocumentos()` and render it as its own "Mis documentos" card for EVERY state, including no-record-yet (a photo for the future carné can legitimately be uploaded before any trámite exists). Rule of thumb: capabilities the user must exercise repeatedly or asynchronously belong in state-independent UI; only *workflow guidance text* belongs in state branches.

## Scope discipline: reference documents leak academic concepts

When the app is administrative but the reference is academic (a thesis about academic management), pedagogical remnants WILL creep in — plan-of-studies catalogs, per-course fields, admission "postulante" concepts, pedagogical conditions. The user will prune them one by one if you don't ("lo de apoderado es innecesario", "no hay turno tarde", "las notas las registra el docente en el sistema de MINEDU"). Run a proactive scope audit before they ask: search the codebase for each domain concept from the reference doc and classify it (administrative vs academic vs ghost), present a 🔴/🟡/🟢 report with a concrete removal plan, and let the user approve. When applying, update in the same pass: esquema → semillas (bump version) → negocio → vistas → documentos imprimibles → tests → README/PLAN.

Before keeping a concept as its own trámite/workflow, check whether it already exists as a type or estado of a core entity: Traslado/Reingreso are matrícula *types* and Reserva is a matrícula *estado*, so parallel trámites for them were redundant and got cut; constancias/certificados for the notes domain (MINEDU's) were cut too. Fewer parallel workflows = fewer roles needed — this reasoning is what let the app shrink from 5 roles to 2 (Secretaría + Estudiante). (Roles can come BACK with a new reference doc — a later borrador re-added Administrador and Tesorería; re-apply the role-sweep checklist in reverse, don't assume the old list.)

When the reference document specifies a DIFFERENT tech stack (a borrador demanding C#/ASP.NET MVC/SQL Server/SMTP/iText7), do not migrate. Write a plan doc (`PLAN_<feature>.md`) mapping each borrador requirement to the current stack with a per-section "Equivalente <tech>" note for the user's sustentación, and implement Fase A only: SMTP → notifications table + `emailSimulado` flag + inbox view; file uploads → compressed dataURLs with size caps (validate mime + size in negocio, compress images via canvas resize); PDF generation → printable view (+ jsPDF later). The user explicitly chose this: "procede con la implementación, pero solo de la FASE A y demás, no quiero migración a C#/ASP.NET".

## Publishing to GitHub (dual-account setup)

```bash
git init -b main
# .gitignore: exclude reference PDFs and OS junk FIRST
git add -A && git commit -m "..."
export GH_TOKEN=$(gh auth token --user <preferred-account>)   # don't switch the active account
gh repo create <repo-name> --private --description "..." --source . --push
# verify for real (a successful push message is not proof):
gh repo view <owner>/<repo> --json pushedAt,defaultBranchRef
gh api repos/<owner>/<repo>/contents --jq '.[].path'
```

## Support files

- `templates/logic-tests.template.js` — copy-and-adapt Node runner: localStorage Proxy shim, single-scope loader, mini test framework, sample tests.
- `references/patterns-and-pitfalls.md` — the debugging paths behind the lessons above (eval scope trap, marker self-split, stale-object bugs, write-corruption recovery, scope-audit checklist).
- `references/php-mysql-migration.md` — full workflow for migrating this app class to a real PHP+MySQL backend: study order (codebase-memory-mcp index first, then esquema/store/semillas/negocio), expert schema patterns (visible-code VARCHAR PKs + secuencias table, generated-column unique for "unique-except-anulada" states, upserts→UNIQUEs, djb2→bcrypt rehash-on-login, centralized blob table, SQL views for JS aggregates), API contract that keeps the frontend migration mechanical, and the localStorage→SQL data-migration path. Load it when the user asks for "base de datos real", PHP+MySQL backend, or the study/plan phase that precedes it.
