# OmniRoute specifics

Captured from session 2026-08-27 against OmniRoute v3.8.49 (Node 16, npm package
installed at `/home/isma/.npm-global/lib/node_modules/omniroute`). Update this
file when the project changes.

## File layout

- Data dir: `~/.omniroute/`
- DB: `~/.omniroute/storage.sqlite` (sqlite3, WAL mode, ~2MB)
- Logs: `~/.omniroute/logs/application/app.log` (JSON lines, one event per line)
- Binary: `/home/isma/.npm-global/bin/omniroute` -> node wrapper
- Compiled bundle: `/home/isma/.npm-global/lib/node_modules/omniroute/dist/.build/next/server/chunks/ssr/_09b2p_u._.js` (~500KB, contains the hardcoded provider URL atlas)

## Default ports

- 20128: HTTP API and dashboard
- 20131, 20132: internal WebSocket / live WS (loopback by default)

## SQLite schema cheatsheet

- `provider_connections(id, provider, name, auth_type, is_active, api_key ENCRYPTED, test_status, last_error, last_tested, last_ping_at, ...)` — encrypted `api_key` values look like `enc:v1:<hex>:<hex>`. Don't try to decrypt; you don't need to.
- `combos(id, name UNIQUE, data JSON, sort_order, created_at, updated_at, system_message, tool_filter_regex, context_cache_protection)` — combo config lives entirely in the `data` JSON column.
- `key_value(key, value)` — the catalog per connection is stored here as `key = "<provider>:<connection-id>"`, value is a JSON array of `{id, name, source}` records.
- `provider_nodes` exists but is empty in real installs — do not rely on it. The catalog is in `key_value` and in the live API.

## API endpoints

- `GET /v1/models` — openai-compatible model list, includes combos as top-level entries.
- `GET /api/models` — Next.js dashboard model list, may include more entries than `/v1/models` (e.g. internal aliases).
- `GET /api/providers` — list connections.
- `POST /api/providers/<id>/sync-models` — force resync. Returns `{syncedModels, unchanged, modelChanges}`. If `unchanged == syncedModels` and `modelChanges.added == 0`, the sync ran but found no diff against the cached list — it is a no-op.
- `POST /api/combos` — create combo. Body shape: `{"name", "strategy": "priority", "models": [{"model": "provider/model-path", "providerId": "provider", "weight": 100}, ...]}`. If you send `models: ["provider/model"]` (strings), OmniRoute misparses the first path segment as `providerId`. Always send objects with explicit `providerId`.

## Error code -> meaning

Read the log first; the user-facing error message is often the gateway's local state, not the upstream.

- `404 "The requested model does not exist" (reset after 42s/2m)` — local cooldown, NOT necessarily a missing model. Wait or check the log for the upstream call.
- `410 "end of life"` — real upstream Gone. The model is deprecated by the provider and should be removed from the catalog.
- `502 "empty response"` — upstream returned 0 content tokens. Often "the model exists but is not generating". Increase `max_tokens` and retry.
- `503 "rate-limit queue budget maxWaitMs"` — local queue saturated, not upstream slow. Raise `Settings -> Resilience -> requestQueue.maxWaitMs` if this is recurring.
- `404 page not found` (no `reset after`) — model genuinely does not exist on the upstream.

## Catalog quirks

- The model catalog in `key_value` is *imported*, not authoritative. On every startup OmniRoute re-syncs from the upstream `/v1/models` (or the hardcoded bundle for known providers).
- Editing `key_value` directly will be overwritten on next sync cycle. The reliable workaround is to create a combo whitelist.
- The dashboard may show deprecated/410 models because the catalog is not auto-purged. This is a known OmniRoute bug.
- `modelsDevSync` is a feature flag for syncing from `models.dev` (third party). It is disabled by default.

## Cooldowns

- Per-model 404 lockout: 120s
- Per-connection 410/429 lockout: 3-15s
- After any 404 the next request to the same model returns 404 in <20ms with `reset after <N>s` — this is the local circuit breaker, not an upstream call. Wait it out before re-testing.

## Useful log greps

```bash
# Cooldown state
grep -E "lockout|cooldown|reset after" ~/.omniroute/logs/application/app.log | tail -50

# Sync activity
grep -E "ModelSync|ModelCatalog|provider_sync" ~/.omniroute/logs/application/app.log | tail -20

# Per-model test results
grep -E "Tested|MODEL_TEST_ALL" ~/.omniroute/logs/application/app.log | tail -30
```
