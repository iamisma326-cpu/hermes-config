# state.db Notes — Session Store Diagnostics

Reference for the `session-recovery` skill. Validated 2026-09-10 against a
live Hermes profile while recovering a "deleted" session that was not deleted.

## Store location

- Default profile: `~/.hermes/state.db` (SQLite + FTS5)
- Other profiles: `$HERMES_HOME/profiles/<name>/state.db` — resolve from
  `$HERMES_HOME`, never assume the default when a profile is active.

## sessions table — schema facts that matter

Relevant columns (from `.schema sessions`):

- `id` TEXT PK — the resume handle (e.g. `20260906_125922_788ec7`), passed to
  `/resume <id>` or `hermes --resume <id>`.
- `started_at` REAL, `last_activity_at` REAL — unixepoch seconds. There is NO
  `created_at` / `updated_at`; querying them fails with
  "no such column". Wrap with
  `datetime(col,'unixepoch','localtime')` for readable output.
- `title` + `title_source` — titles default to the session's FIRST prompt and
  only change via rename. `session-librarian` skill documents the
  `hermes sessions rename` CLI.
- `archived` / `hidden` / `pinned` INTEGER flags (default 0) — archived or
  hidden sessions drop out of the default listing while still existing.
- `message_count`, `tool_call_count`, `source` (`cli`, gateway platforms, ...),
  `model`, `cwd`, `git_branch`.
- `parent_session_id` — sessions branched via `/branch` point at their origin.

Indexes of note: `idx_sessions_started` (started_at DESC),
`idx_sessions_source`, and partial UNIQUE index
`idx_sessions_title_unique ON sessions(title) WHERE title IS NOT NULL` —
renames must avoid colliding with an existing non-NULL title, or the UPDATE
fails with a constraint error.

Related tables: `messages` (+ `messages_fts*` FTS5 shadow tables — what
`session_search` actually queries), `system_prompts`, `gateway_routing`,
`session_model_usage`, `compression_locks`.

## Validated diagnostic queries

Listing recent CLI sessions (the one that found the "lost" session):

```bash
sqlite3 -header -column ~/.hermes/state.db "SELECT id,
  datetime(started_at,'unixepoch','localtime') inicio,
  datetime(last_activity_at,'unixepoch','localtime') actualizado,
  message_count, archived, hidden, substr(title,1,42) titulo
  FROM sessions WHERE source='cli'
  ORDER BY last_activity_at DESC LIMIT 15;"
```

Rename + verify (fallback when the CLI is unavailable):

```bash
sqlite3 ~/.hermes/state.db "UPDATE sessions SET title='<new title>'
  WHERE id='<session_id>';
  SELECT id, title FROM sessions WHERE id='<session_id>';"
```

Check whether a specific ID still exists at all:

```bash
sqlite3 ~/.hermes/state.db "SELECT id,title,archived,hidden,message_count
  FROM sessions WHERE id='<session_id>';"
```

Full transcript extraction for a session (validated 2026-09-15):
`session_search` truncates around 100 KB of output; for large sessions the
spillover file contains only that truncated window, NOT the whole session.
The complete transcript, direct from the store:

```bash
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages
  WHERE session_id='<session_id>';"            # real size first
sqlite3 ~/.hermes/state.db "SELECT id, role, content, tool_calls, tool_name,
  timestamp FROM messages WHERE session_id='<session_id>' ORDER BY id;"
```

`content` may be NULL on assistant tool-call-only turns; `tool_calls` is JSON.
Summarize the dump with execute_code (user verbatim, assistant text +
`▶ tool args`, tool outputs trimmed) into a digest file and page with
read_file for the "study the whole session" request.

## Case 2026-09-10 — stale title misread as deletion

User: "creo que se eliminó una sesión, estaba cambiando mi BD en un proyecto".
`/sessions` did not show anything recognizable. Diagnosis:

1. `session_search` (content search: "cambiar base de datos BD proyecto" +
   "gestion_estudiantes MySQL esquema") found it immediately — 271 messages of
   3NF normalization work on MariaDB `gestion_estudiantes`.
2. state.db listing showed the session intact, `archived=0`, `hidden=0`, but
   titled "Instalar codebase-memory-mcp en Hermes agent" — the first prompt of
   the session, 4 days before the DB work it drifted into.
3. Root cause: topic drift + never renamed → user did not recognize the entry
   → assumed deletion.

Fix: renamed via the sqlite UPDATE above to
"BD gestionest1: 3NF personas (Fase 1-2 en curso)" and handed back
`/resume 20260906_125922_788ec7`.

Same case, second half — interrupted work-state reconstruction:

- Transcript's last messages said "applying seed v2" (intent).
- Live artifacts told the truth: git had only the Fase 1 commit (`7cc0ec7`);
  the seed had run HALF-WAY — `unidades_didacticas=4` (missing ING01/CFD01/
  CON01 from git HEAD's seed), `horarios=0`, `notas=0`, `asistencias=0`,
  `evaluaciones=0`, `seed_version=NULL`.
- Lesson: one cross-table COUNT query exposed the half-applied state faster
  than re-reading the transcript; the transcript's "done" claims were
  unverified intent.

## Case 2026-09-15 — "study all the context of that session"

User resumed gestionest1: "dime como se llama aquella sesión y en qué me
quedé", then "estudia todo su contexto de aquella sesión". The target
session (20260914_202442_30eda2) had 416 messages. `session_search(
session_id=...)` returned ~109 KB and truncated; the spillover file held
only 30 messages (window 20540–20955) — the "full result is already on
disk" hint did NOT mean the whole session was there.

Fix: `SELECT COUNT(*)` exposed the real size; the direct sqlite3 query on
`messages` returned all 416 rows; an execute_code pass structured them into
a 110 KB digest (user/assistant verbatim, tool calls as `▶ name args`,
tool outputs trimmed) written to /tmp and paged with read_file in three
chunks. Final state of the work was then confirmed with `git log` +
`git status` + skill_view of the project skill, and reported as verified:
frontend TUPA `356604e`, informe cliente `1fbcea3` (PDF 14 págs), BD
64/64 tablas PG↔MariaDB; know pendientes: capa PDO a PostgreSQL, WAHA
real, RouterIA.

## See also

- `session-librarian` skill — bulk library organization, `hermes sessions
  list/rename/archive/delete/prune/export` CLI, plan-before-mutate policy.
- `hermes-agent` skill — general Hermes internals (`state.db` in Key Paths).
