---
name: local-llm-gateway-debug
description: Debug a local LLM gateway with failing provider tests.
---

# Debug a local LLM gateway

When the user says "test failed" against a local LLM router (OmniRoute, LiteLLM, OneAPI, etc.) and the dashboard error is vague, your job is to find which side of the chain is broken: credential, URL, model ID, rate limit, or upstream outage. The dashboard test button is usually a thin wrapper around the same HTTP call you can make yourself — and making it yourself is faster than clicking through a UI and gives you the raw error.

## Workflow (evidence-first, never trust stored state alone)

1. **Locate the running process and its data dir.**
   - `ss -tlnp | grep <port>` or `lsof -i :<port>` to confirm the process and PID.
   - For OmniRoute: `~/.omniroute/` (storage.sqlite, logs/application/app.log, .env).
   - For LiteLLM: usually `~/.litellm/` or `/tmp/litellm-*`; check the running config.
   - For OneAPI: check `--data-dir` flag or `~/.oneapi/`.

2. **Read the live log FIRST, before the database.** The application log is authoritative for "what just happened." A SQL query gives you a snapshot; the log gives you the request that produced the current error.
   - OmniRoute: `~/.omniroute/logs/application/app.log` (JSON-lines, one event per line).
   - Grep for: the model ID the user is testing, the provider name, recent `[ERROR]`, `404`, `429`, `401`, `No credentials for`.
   - The last 5-10 minutes is usually enough; deeper if the user says "it's been broken for hours."

3. **Reproduce the test with curl against the gateway's own OpenAI-compatible endpoint.** This bypasses the dashboard UI and gives you the raw response. Most of these gateways expose `/v1/chat/completions` and `/v1/models`.
   ```
   curl -sS -X POST http://localhost:<port>/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer dummy" \
     -d '{"model":"<provider>/<model>","messages":[{"role":"user","content":"ping"}],"max_tokens":5,"stream":false}' \
     -w "\nHTTP %{http_code} | %{time_total}s\n"
   ```
   - `stream:false` is critical on first test — streaming failures mask themselves as partial success.
   - The gateway typically accepts any bearer for test traffic; it just needs to be present.

4. **Classify the failure by status code and error string.** This is the most important step. Before guessing causes, look at the actual response:
   - `200` → works, the user's complaint is something else (UI cache, stale cooldown, dashboard race).
   - `401` / `403` → credential problem (key missing, wrong format, expired, not authorized for that model).
   - `404` with "model does not exist" → model ID is wrong, deprecated, or not enabled upstream. NOT a credential issue.
   - `404` with "not found" on the path → URL/base_url is wrong.
   - `429` → rate limit (upstream or gateway-internal). Will resolve in minutes; don't keep retrying.
   - `500` / `502` / `503` → upstream outage. Check provider status page, not local config.
   - Connection refused / timeout → gateway is not running, or the outbound network is blocked.

5. **Only after you've reproduced and classified, look at the database** to understand the stored config. The DB is a *snapshot* and may be stale. Never diagnose from the DB alone.

## Common pitfalls

- **Don't diagnose from a stale log line.** OmniRoute has a 120s auto-lockout after a 404 — a model that "failed" in the log 30 seconds ago will still report 404 even if the user fixed the model name, until the cooldown expires. Either wait it out or test a different model to confirm the gateway is otherwise healthy.

- **The "model not in catalog" assumption is often wrong.** You see the model name in a stored JSON list and assume it's authoritative. It isn't. The catalog gets out of sync with the upstream provider. Always test the live endpoint before declaring a model dead.

- **Encrypted keys are not debuggable in place.** OmniRoute stores API keys as `enc:v1:<hex>`. You cannot decrypt them in SQLite to test "is the key valid." Instead, test through the gateway and let it use the key itself — the response tells you whether the key worked.

- **`provider_nodes` is not the source of truth in OmniRoute.** It's often empty. The catalog of models per connection lives in the `key_value` table under keys like `nara:<connection-uuid>` as a JSON array. Always check `key_value` for catalog data.

- **OpenAI-compatible != OpenAI.** Many gateways add a `Authorization: Bearer dummy` check but forward real auth headers to the upstream. A "401 from the gateway" might still be a "200 from upstream once the real key is used." Don't conflate the two.

- **Dashboard "Test" buttons often test the wrong thing.** Some test the credential, some test a specific model, some test the connection. Read the request the dashboard makes (browser dev tools, or the log line just after the click) to know what was actually tested.

- **Session-1 lesson: I made a confident wrong diagnosis from the DB snapshot** (claimed a model didn't exist because it wasn't in the stored catalog), and the user lost time on it. The fix was one curl call. Don't repeat this — the curl call is step 3, not step 7.

- **Your own re-test can trigger the cooldown you're trying to measure.** If a test returned 200, then 90 seconds later you re-test the same model and see 404, the cooldown is *yours*. The 120s lockout fires on the first 4xx, so by the time you re-test you've already eaten 30-60s of the window. Mitigation: when re-testing, use a model that you know is healthy (e.g. one that the log just showed `ok`), and test the suspect model after that one — if the suspect still 404s with `<500ms` response time and "reset after Xs" in the body, it's the cooldown, not the upstream. Real upstream 404s have no "reset after" hint. This is how I (re-)discovered that a model I had declared "doesn't exist" actually worked fine — the original test was inside a cooldown window from my own earlier probe.

- **Editing the `key_value` catalog is a temporary fix, not a permanent one.** This is the most important lesson from a session where the user restarted OmniRoute and all the broken-model removals came back. OmniRoute's startup / sync cycle re-populates `key_value` from the upstream provider's `/v1/models` endpoint. So:
  - If you remove a broken model from `key_value`, it works for the current session.
  - On next restart (or when the 24h ModelSync scheduler runs and the connection has `autoSync` enabled), the upstream list overwrites your edit.
  - Verify by running the same `SELECT value FROM key_value WHERE key=...` query *after* a restart. If the broken models are back, your edit was clobbered.
  - The fix that actually sticks: use the dashboard's per-model disable toggle, or set `is_active=0` on the broken row in a table the gateway respects for routing (not just display). For OmniRoute specifically, the model-level disable is in the dashboard under the provider's model list — not in the SQLite `key_value` blob.
  - The probe script's "broken models to remove from catalog" output is a hint, not a recipe. Read this pitfall before acting on it.

- **Don't propose "restart the gateway and edit the DB" as a fix when the catalog is upstream-controlled.** If `POST /api/providers/<id>/sync-models` returns `unchanged: N` (no changes added/removed/updated) but the user still sees old models in the dashboard, the catalog lives upstream, not in your local DB. Restarting won't help — the upstream list gets re-imported on startup. The real fix is the dashboard's per-model disable, not a DB edit.

- **The "first test, then re-test" loop is the single most common diagnostic trap on OmniRoute.** Plan: (a) one targeted curl for the reported failure → classify, (b) one curl for a known-healthy model on the same provider → confirm the provider is alive and not in cooldown, (c) only then re-test the suspect. If (a) and (b) both fail, the provider is the problem; if (b) works and (a) fails, the model is the problem.

- **410 Gone means end-of-life, not missing.** NVIDIA NIM returns 410 with `{"type":"about:blank","title":"Gone","status":410,"detail":"The model 'x' has reached its end of life on YYYY-MM-DD..."}` when a model is permanently retired. Distinguish from 404 "model does not exist" (transient/unknown). Both should be removed from catalogs, but 410 means the model is *never* coming back. Note: OmniRoute does not auto-purge 410 models from the dashboard catalog — they linger forever and will 410 on every test.

- **The `sync-models` endpoint is a no-op when the upstream list is unchanged.** `POST /api/providers/<id>/sync-models` returns 200 with `unchanged: N` and `importedCount: 0` when it sees no delta from the upstream. It does not force a re-import from the DB or wipe stale entries. Don't use it to "fix" a stale-looking catalog; it won't.

## Removing broken models

To remove a model that consistently 404s (so it stops showing in `/v1/models` and stops being picked by combos):

1. Find where the catalog is stored. For OmniRoute: `SELECT value FROM key_value WHERE key LIKE '<provider>:%';` — the value is a JSON array of `{id, name, source}`.
2. Edit the JSON array to drop the broken entries. Use Python with `json.loads` rather than `sqlite3` JSON functions — the latter often reject the `$[0]` path syntax silently and the UPDATE looks like it succeeded when it didn't.
3. Verify by calling `/v1/models` and counting the IDs that contain the provider prefix.

Example (OmniRoute):
```python
import sqlite3, json
con = sqlite3.connect('~/.omniroute/storage.sqlite')
cur = con.cursor()
key = 'nara:<connection-uuid>'
cur.execute("SELECT value FROM key_value WHERE key=?", (key,))
models = json.loads(cur.fetchone()[0])
broken = {'model-a', 'model-b'}
new = [m for m in models if m.get('id') not in broken]
cur.execute("UPDATE key_value SET value=? WHERE key=?", (json.dumps(new, ensure_ascii=False), key))
con.commit()
```

Then `curl http://localhost:<port>/v1/models | jq` to confirm.

## Reading OmniRoute logs efficiently

The log is JSON-lines with two slightly different shapes (look for `level` and `service` fields):
- `{"timestamp":..., "level":..., "component":..., "message":...}` — app-level
- `{"level":<number>, "time":..., "service":"omniroute", "module":..., "msg":...}` — pino logger

Useful grep patterns:
- `grep -iE "test|error|fail|<provider-name>" logs/application/app.log | tail -80`
- `grep "MODEL_TEST_ALL" logs/application/app.log` — batch model test events
- `grep "CredentialHealth" logs/application/app.log` — auto health-check cycles
- `grep -E "ROUTING|AUTH" logs/application/app.log` — per-request routing decisions

The `MODEL_TEST_ALL` events include `latencyMs` and a `tested:N/total:M` summary at the end of each batch. Use those to find *which* model in a batch failed.

## Verification

Before declaring "fixed":
1. Re-test the previously-failing model with curl. Expect HTTP 200.
2. Hit `/v1/models` and confirm the working model still appears.
3. Hit `/v1/models` and confirm the removed model no longer appears.
4. Tell the user about the 120s auto-lockout: even after removing a broken model, manually-requesting that model ID will still 404 until the cooldown expires. This is normal, not a regression.
5. Warn the user that a sync operation may re-import the broken models from upstream. If they want to keep them gone, the dashboard probably has a "disable per-model" toggle — recommend using that next time so it survives syncs.

## Reference

- [references/omniroute-data-layout.md](references/omniroute-data-layout.md) — empirical layout of `~/.omniroute/` (v3.8.x): table inventory, encrypted-key format, log event shapes, status-code map, NVIDIA NIM model roster.
- [scripts/probe_provider.py](scripts/probe_provider.py) — bulk-probe every chat model in a provider's catalog and classify each as ok / slow / cooldown / 410 / 404 / timeout. Re-runnable; takes (provider, gateway_url, max_latency_s).
