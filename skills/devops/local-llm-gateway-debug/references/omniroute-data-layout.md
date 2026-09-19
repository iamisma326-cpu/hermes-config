# OmniRoute — runtime data layout (v3.8.x)

Captured 2026-08-27 from a live install at `~/.omniroute/`. This is the empirical shape of an OmniRoute data directory, useful when you need to find config or models without going through the dashboard.

## Directory

```
~/.omniroute/
├── .env                          # only STORAGE_ENCRYPTION_KEY + PORT in the captured instance
├── storage.sqlite                # main DB (also has -shm, -wal)
├── call_logs/                    # JSON request logs per call
├── db_backups/                   # automatic SQLite backups
├── logs/
│   └── application/app.log       # JSON-lines app + pino logs (one file, appended)
└── server/                       # empty in the captured instance
```

## Database tables you actually need

There are ~90 tables. Most are auxiliary. The ones that matter for provider debugging:

| Table | Purpose | Notes |
|---|---|---|
| `provider_connections` | Per-connection config: API key, OAuth, priority, last test result | `api_key` column is **encrypted** as `enc:v1:<hex>:<hex>` — cannot be decrypted in place. `provider` is the short name (`nara`, `opencode`, `nvidia`). |
| `provider_nodes` | (Empty in the captured instance.) Probably only used for certain provider types; the per-provider routing config lives elsewhere. Don't waste time querying it. |
| `key_value` | Generic JSON blob store. **This is where the per-connection model catalog lives** under keys like `nara:<connection-uuid>`. Also stores settings, compression config, etc. |
| `call_logs` | Per-request log rows; queryable. |
| `audit_log` | Admin actions. |

The encrypted key format is `enc:v1:<iv-or-salt>:<ciphertext>` with the `STORAGE_ENCRYPTION_KEY` in `.env`. Useful only if you control the instance; the agent should not attempt to decrypt.

## Provider model catalog format

Stored in `key_value` as a JSON array:

```json
[
  {"id": "tencent-hy3", "name": "Tencent Hy3", "source": "imported"},
  {"id": "mistral-large", "name": "Mistral Large", "source": "imported"},
  {"id": "mistral-medium-3-5", "name": "Mistral Medium 3.5", "source": "imported"}
]
```

Key format: `<provider-short-name>:<connection-uuid>`.

To list a connection's catalog:
```sql
SELECT value FROM key_value WHERE key = 'nara:cfe39644-bb0e-4939-9c9f-21772f714657';
```

To find the connection uuid from a provider name:
```sql
SELECT id, name, auth_type, is_active, test_status, last_error
FROM provider_connections
WHERE provider = 'nara';
```

## How the log records a "test"

When the user clicks "Test" on a model, look for these log events (timestamps are the authoritative "what just happened"):

```
[METHOD] POST /v1/chat/completions | <provider>/<model> | 1 msgs
[ROUTING] Provider: <provider>, Model: <model>
[AUTH]    Using <provider> account: <uuid-prefix>...
[ALIAS]   Model alias applied: <input-id> → <canonical-id>     # if any
[provider] Node <uuid> model not found (404) for <model> - locking model for 120s
[ERROR]   [404]: The requested model does not exist.
[ProxyEgress] <provider>/<account> in=? out=<ip> proxy=direct status=error|success
[USAGE]   NARA | in=<n> | out=<n> | account=<uuid-prefix>...
[STREAM]  NARA | <model> | <ms>ms | complete
[MODEL_TEST_ALL] Tested <model>: ok | error
[MODEL_TEST_ALL] Batch test complete: <ok>/<total> model(s)
```

The `lockout` line is the one that explains "I just changed config and it still 404s" — wait 120s or test a different model.

## Status code map (from observed behavior)

| Status | Meaning | What to check |
|---|---|---|
| 200 | works | nothing |
| 401/403 | credential invalid or unauthorized for model | key rotation, account status, model gating |
| 404 "model does not exist" | bad model ID upstream | update catalog or remove the entry |
| 404 on path | wrong base_url | check provider_nodes / connection base_url |
| 410 Gone | model permanently retired (end-of-life date in body) | remove from catalog; will not return |
| 429 | rate-limited | wait, don't retry-loop |
| 500/502/503 | upstream dead | provider status page |

## Common gotchas

- **Auto-lockout after 404 = 120s.** Models you've "fixed" still 404 for 2 minutes after the first failure.
- **Auto-lockout also fires on 410 (end-of-life).** The lockout applies to the model ID, not the provider. So if you test `nvidia/z-ai/glm-5.2` and get 410, the cooldown blocks the *model*, but other models on the NVIDIA provider are unaffected.
- **Re-tests inside the cooldown window return `<500ms` with `reset after Xs` in the body.** That's the smoking gun for "this is your own cooldown, not an upstream failure." Real upstream 404s don't include the reset hint and don't respond that fast.
- **Empty `provider_nodes` table is normal.** Don't assume your config is missing.
- **Catalog can include models that don't exist upstream.** The "imported" source flag is from a previous sync, not a live check. In the captured instance, NVIDIA NIM's catalog had 84 models; only 11 worked for chat at sub-10s latency; 4 were too slow (>25s); the rest returned 404 or 410.
- **The 16k-token test response for `mistral-medium-3-5` is normal** for OmniRoute's test prompt; latency was ~15s in the captured instance, vs ~3s for `minimax-m3-free` against the same provider.

## NVIDIA NIM — observed working models (OmniRoute, 2026-08-27)

Models that responded in <10s to `{"messages":[{"role":"user","content":"ping"}],"max_tokens":8,"stream":false}`:

| Model ID | Latency |
|---|---|
| `openai/gpt-oss-20b` | 1.2s |
| `deepseek-ai/deepseek-v4-flash-0731` | 1.6s |
| `deepseek-ai/deepseek-v4-pro-0813` | 2.1s |
| `moonshotai/kimi-k3` | 0.8s |
| `stepfun-ai/step-3.7-flash` | 4.8s |
| `nvidia/nemotron-3-ultra-550b-a55b` | 6.2s |
| `nvidia/nemotron-3-super-120b-a12b` | 1.8s |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.7s |
| `meta/llama-3.2-11b-vision-instruct` | 0.9s |
| `meta/llama-3.2-90b-vision-instruct` | 9.3s |
| `meta/muse-glimmer-30b` | 0.8s |

Models that returned 404 (do not exist on NVIDIA NIM with that ID): most `mistralai/*`, `writer/palmyra-*`, `nvidia/llama-3.1-nemotron-*`, `google/gemma-*`, `meta/llama2-70b`, `meta/codellama-70b`, `ibm/granite-*`, `ai21labs/jamba-*`, `01-ai/yi-large`, `zyphra/zamba2-7b-instruct`, `databricks/dbrx-instruct`, `bigcode/starcoder2-15b`, `aisingapore/sea-lion-7b-instruct`, `adept/fuyu-8b`, `deepseek-ai/deepseek-coder-6.7b-instruct`, `nvidia/cosmos-reason2-8b`, `nvidia/llama3-chatqa-1.5-70b`, `nvidia/mistral-nemo-minitron-8b-8k-instruct`, `nv-mistralai/mistral-nemo-12b-instruct`, `microsoft/phi-3*`, `google/codegemma-*`, `google/deplot`, `google/recurrentgemma-2b`, `google/gemma-2b`, `meta/llama-guard-4-12b`, `meta/muse-glimmer-30b` is in BOTH lists above — it works as a chat model but is sometimes categorized as vision-special in the catalog (the actual response determines usability).

Models that timed out at 25s (unusable in practice): `openai/gpt-oss-120b`, `mistralai/mistral-nemotron`, `poolside/laguna-xs-2.1`, `google/gemma-4-31b-it`. Don't put these in a combo — they'll make every request wait 25s before falling through.

Models that returned 410 (end-of-life): `z-ai/glm-5.2` (EOL 2026-08-21). Expect more over time; the catalog is not auto-pruned.

Audio/embeddings/specialty models preserved in the catalog but not tested for chat: `nvidia/embed-qa-4`, `nvidia/llama-3.1-nemoguard-8b-content-safety`, `nvidia/llama-3.1-nemoguard-8b-topic-control`, `nvidia/nemotron-4-340b-reward`, `nvidia/nemotron-parse`, `nvidia/nemotron-3.5-content-safety`, `nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1`, `nvidia/llama-3.2-nv-embedqa-1b-v1`, `nvidia/llama-nemotron-embed-vl-1b-v2`, `nvidia/nemotron-3-embed-1b`, `nvidia/nv-embedqa-mistral-7b-v2`, `snowflake/arctic-embed-l`, `nvidia/riva-translate-4b-instruct*`, `nvidia/ai-synthetic-video-detector`, `nvidia/ising-calibration-1.5-31b`, `nvidia/nvclip`, `nvidia/neva-22b`, `nvidia/vila`, `microsoft/kosmos-2`, `meta/llama-guard-4-12b`, `adept/fuyu-8b`, `google/deplot`, `google/recurrentgemma-2b`.
