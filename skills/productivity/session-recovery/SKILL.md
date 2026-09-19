---
name: session-recovery
description: "Use when a session seems deleted: find, rename, resume it."
version: 1.0.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Sessions, Recovery, Diagnostics, Hermes, Continuity]
    category: productivity
    related_skills: [session-librarian]
---

# Session Recovery

Handle two related situations: (1) the user reports a Hermes session as lost,
missing, or deleted ("creo que se eliminó una sesión", "my session is gone",
"we were working on X, where did it go?"); (2) a session must be resumed but
nobody is sure what state the work was left in. Sessions are almost never
actually deleted — the usual causes are a stale title, archive/hidden flags,
or simply not recognizing the entry in the `/sessions` listing. Companion to
`session-librarian` (which covers library organization: bulk find, archive,
prune); this skill covers the diagnose-and-resume flow.

## When to Use

- "Se me borró / eliminó una sesión", "my session is gone / was deleted"
- "We were working on X, I can't find it in /sessions"
- "Resume that session, but where exactly did we leave the work?"
- A prior session was interrupted mid-task and its outcome is uncertain.

## Diagnosis ladder (in order)

1. **Search by CONTENT, never by title.** `session_search(query=...,
   limit=5-10, sort="newest")` with topic keywords: project name, what was
   being done, error strings, table/API names. Titles reflect the session's
   FIRST prompt, not what it drifted into — a 271-message session titled
   "Install X" can be 90% database migration work.
2. **Verify in state.db.** The session store is SQLite at
   `~/.hermes/state.db` (or `$HERMES_HOME/profiles/<name>/state.db` when a
   profile is active). Timestamp columns are `started_at` / `last_activity_at`
   (NOT `created_at`/`updated_at` — those columns do not exist and sqlite
   errors out):

   ```bash
   sqlite3 -header -column ~/.hermes/state.db "SELECT id,
     datetime(started_at,'unixepoch','localtime') inicio,
     datetime(last_activity_at,'unixepoch','localtime') actualizado,
     message_count, archived, hidden, pinned, title
     FROM sessions WHERE source='cli'
     ORDER BY last_activity_at DESC LIMIT 15;"
   ```

   `archived=1` or `hidden=1` removes a session from the default listing while
   the session still exists. `pinned` sessions always surface.
3. **Confirm the match**: large `message_count` + `last_activity_at` matching
   when the user says they last worked + a content snippet from the
   `session_search` result describing the same work.
4. **Usual root cause: the title went stale.** The session drifted topics over
   days; the user scrolled `/sessions`, did not recognize the old title, and
   concluded "deleted". Rarely is deletion real — it requires an explicit act
   (`/quit --delete`, `hermes sessions delete`, `hermes sessions prune`).

## Fix and hand back

- **Rename so the user can find it.** Documented CLI:
  `hermes sessions rename <session_id> <new title>`. Verified sqlite fallback
  (works directly against the store; confirm with the trailing SELECT):

  ```bash
  sqlite3 ~/.hermes/state.db "UPDATE sessions SET title='<new title>'
    WHERE id='<session_id>';
    SELECT id, title FROM sessions WHERE id='<session_id>';"
  ```

  Titles are UNIQUE (partial index `idx_sessions_title_unique` on sessions with
  a non-NULL title) — pick a title no other session uses, or the UPDATE fails.
- **Hand back every resume handle**; the user only needs one:
  - in-session: `/sessions` (browse + select), `/resume <session_id>`
  - shell: `hermes --resume <session_id>`; `hermes --continue` (most recent)
- **Report where the work actually stands** (next section) so the user can
  decide: resume the old session, or continue in the current one using the
  recovered context (the transcript is readable via `session_search` either
  way — resuming is for continuing the conversation, not for reading it).

## Reconstruct work state — trust artifacts, not the transcript

The last messages of an interrupted session describe INTENT, not final state
("applying the seed...", then cutoff). Before telling the user where things
stand — or continuing the work — verify against live artifacts:

- `git log --oneline -10` + `git status` in the project: what actually got
  committed vs. what the transcript claims.
- Live counts/queries against the real system (DB tables, running services,
  test suites). Interrupted multi-step migrations (seeds, backfills) are
  usually HALF-APPLIED: some tables populated, others empty — one query
  counting across the affected tables exposes it immediately.
- Report BOTH: what the transcript says the plan was, and what the artifacts
  show actually landed. Offer to continue from the verified state.

## Reading a full session (large transcripts)

The user sometimes asks to "study all the context of that session" before
continuing (e.g. "estudia todo su contexto de aquella sesión"). 
`session_search(session_id=...)` caps around 100 KB of output — for big
sessions it returns a TRUNCATED window, and the spillover file holds only
that same truncated window (the "full result already on disk" hint is
misleading for session reads: a 416-message session can spill just ~30 of
them). The complete transcript lives in the local store:

```bash
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages
  WHERE session_id='<session_id>';"            # real size first
sqlite3 ~/.hermes/state.db "SELECT id, role, content, tool_calls, tool_name,
  timestamp FROM messages WHERE session_id='<session_id>'
  ORDER BY id;" > /tmp/session_dump.txt        # full transcript
```

Then build a readable digest with execute_code: user text verbatim
(trim ~800 ch), assistant text (~1500 ch) plus tool_calls as
`▶ name args` (json.loads, args trimmed ~250 ch), tool outputs trimmed to
~300 ch — write it to /tmp and page with read_file. This turns a 400+
message session into three readable chunks and is also the fastest route
when the user wants the whole context restudied before continuing. After
digesting, still verify the final state against live artifacts (git log,
git status, skill file state) rather than trusting the transcript's claims.

## Pitfalls

- Never conclude "the session was deleted" from the `/sessions` listing
  alone. Drift + stale title is far more likely; deletion is an explicit act.
- `session_search` indexes message CONTENT; state.db metadata (flags, counts,
  titles) is not searchable there. Combine both surfaces.
- The sessions table has `archived`, `hidden`, AND `pinned` flags — check all
  three before declaring a session missing.
- Gateway sessions (telegram, discord, ...) have `source != 'cli'` — filter
  accordingly when the user works across surfaces.
- Renaming via sqlite touches only the title; prefer `hermes sessions rename`
  when available, and always verify with a follow-up SELECT.
- Do not re-derive the whole prior conversation from the transcript before
  acting — the artifact check (git/DB/live system) usually tells you the real
  state faster than reading 200 messages. Exception: when the user EXPLICITLY
  asks to study all the context first, use the direct-DB digest method above.
- The spillover file from a truncated session read holds only the truncated
  window that was returned, NOT the whole session. Verify span before trusting
  it: compare the saved JSON's first/last message ids (or message_count) with
  the real `SELECT COUNT(*) FROM messages WHERE session_id=...`.
- In `state.db.messages`, assistant rows may have NULL `content` (tool-call-only
  turns); `tool_calls` is a JSON string that must be json.loads'd; `tool_name`
  names the tool that produced a 'tool' row.

## Verification

After a rename, re-run the state.db SELECT and confirm the new title appears.
Give the user the exact ID string to type after `/resume`. If they still cannot
find the session in `/sessions`, re-check `hidden`/`archived` — the listing
they see may be filtered.

## References

- `references/state-db-notes.md` — sessions-table schema notes, the validated
  diagnostic query set, and the 2026-09-10 case (stale-title root cause +
  half-applied seed detected by live counts).
