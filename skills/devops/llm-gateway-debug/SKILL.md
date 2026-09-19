---
name: llm-gateway-debug
description: Use when a local LLM gateway has broken providers.
metadata:
  origin: session-2026-08-27
  version: 1
  author: hermes-session-curator
  license: MIT
  hermes:
    tags:
      - llm
      - gateway
      - debugging
      - catalog
    related_skills:
      - terminal-ops
      - verification-loop
---

# LLM Gateway Debug

Use this when a local LLM gateway (OmniRoute, LiteLLM, OpenRouter, OneAPI, etc.) is running on the user's machine, the user reports test failures or wrong catalog, and the fix requires reading the live process state — not guessing from docs.

## Skill Stack

Pull these into the workflow when relevant:

- `terminal-ops` for evidence-first command execution
- `verification-loop` for "do not claim fixed until the test rerun proves it"
- `requesting-code-review` if the fix needs approval before merge
- `knowledge-ops` if the provider-specific quirks need to persist across sessions

## When to Use

- user says "el test falla", "veo modelos que no existen", "el provider da error", or names a specific gateway
- a service is already running on a known port (e.g. 20128, 4000, 8080)
- the fix needs to be made on the live system, not by reading source
- the provider has a catalog (model list) that may or may not match what the gateway shows

## Core Workflow

### 1. Locate the live process before assuming

Do not trust the user's summary of what's broken. Get ground truth:

- `pgrep -fa <name>` to find the real PID (gateways often have a node wrapper + esbuild helper + worker; user may report the wrong one)
- `ss -tlnp` to confirm the port and which PID owns it
- `curl -sI http://localhost:<port>/` to confirm the service is up and read the version banner
- The dashboard URL is rarely the same as the API base. The user's "dashboard at /dashboard/providers" is a UI route; the API is usually `/v1/...` or `/api/v1/...`

### 2. Find where the catalog actually lives

This is the single biggest trap. Gateways store model catalogs in multiple places and the live dashboard may not read from the one you expect.

Try in order:

1. **DB rows**: `sqlite3 <data_dir>/storage.sqlite ".tables"` then look for `provider_*`, `model_*`, `*_catalog*`. OmniRoute uses `key_value` with key `<provider>:<connection-id>`.
2. **Cached in process memory**: the bundle is loaded at startup. Editing the DB does NOT invalidate the cache until restart.
3. **Live upstream fetch**: some gateways call the provider's `/v1/models` on startup and cache. Editing the DB has zero effect.
4. **Hardcoded in the binary**: e.g. an npm bundle with a baked-in provider list. Editing the file may or may not survive the next package install.

Verify which one is in play: edit the DB, query the API, see if it changed. If no, the source is upstream or memory. If yes, you have the wrong source AND a cache invalidation problem.

### 3. Read the log before interpreting the test

Gateways have local rate-limiting, cooldowns, and circuit breakers that produce errors which look like provider errors but are actually local state. OmniRoute for example:

- 404 right after a 404 → "reset after 42s" in the error → this is a local 120s cooldown, not a real test
- 410 with "end of life" → real upstream Gone
- 502 with "empty response" → upstream returned 0 content (often a real "yes the model exists but failed")
- 503 with "rate-limit queue budget" → local queue saturated, not upstream slow

Always check `logs/application/*.log` and grep for `cooldown|rate|lockout|reset after` before concluding the provider is broken.

### 4. Distinguish 3 failure modes

- **Catalog issue**: the model is in the UI but doesn't exist upstream. Real, no workaround at gateway level. The fix is to filter the catalog (combo / disabled connection / dashboard filter).
- **Cooldown issue**: the gateway is throttling you locally. Wait or restart.
- **Real upstream 4xx/5xx**: the provider genuinely failed. Test again after a few minutes to rule out transient.

If your test result contradicts an earlier test, the most likely cause is cooldown, not the provider changing its mind.

### 5. The "filter the catalog" trap

When the user wants models that don't work removed from the dashboard, the obvious path (edit the DB) often fails because:

- The catalog is hardcoded in the bundle
- The catalog is re-fetched from upstream on startup
- The cache doesn't invalidate

The reliable alternatives, in order of invasiveness:

1. **Create a combo** that whitelists only the working models. The user picks the combo in their client. The broken models stay in the catalog but are never used.
2. **Disable the connection** entirely and add a manual one with only the working models. Most invasive — loses the original key.
3. **Patch the bundle file** that has the hardcoded list. Survives until next `npm install` or upgrade.

Always offer (1) first. Users almost never want (2) once they see (1) works.

## Output Format

When reporting back, include:

- the real PID and port (not just "OmniRoute is running")
- the source of truth you found for the catalog (DB key, bundle file, upstream URL)
- the specific error code you saw (with the cooldown/reset-after timestamp if present)
- what you actually changed and the API call that proves it

## Pitfalls

- do not conclude "model doesn't exist" from a 404 that happens during a cooldown window — read the log first
- do not edit `key_value` / DB catalogs and assume the dashboard updates — gateways cache in process memory
- do not assume the dashboard UI endpoint is the same as the API models endpoint — they often differ
- do not kill a manually-launched gateway process without confirming the user can re-launch it
- do not promote "edit the bundle" as a long-term fix — the next upgrade wipes it
- do not mix provider prefixes: when creating a combo, `providerId` must match the actual provider (e.g. "nvidia"), not the first segment of the model path
- when forcing a resync via the API, "syncedModels: N" with `unchanged: N` and `added: 0` means it's a no-op — the sync ran but found no diff against the cached list

## Verification

- the API call that proves the change actually applied (not "I updated the DB, should work now")
- the cooldown cleared or you're outside the cooldown window before declaring a test result valid
- for combos: a `POST /v1/chat/completions` against the combo name returns a valid response, not a routing error
