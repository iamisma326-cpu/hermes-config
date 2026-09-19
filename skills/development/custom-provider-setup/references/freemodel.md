# Freemodel CC — cc.freemodel.dev

Provider added 2026-09-11. Setup: plugin `~/.hermes/plugins/model-providers/freemodel/`,
env `FREEMODEL_API_KEY` in `~/.hermes/.env`, config `providers.freemodel`
(type=openai, base_url `https://cc.freemodel.dev/v1`).

## Endpoints

- Auth: `Authorization: Bearer` works (no x-api-key needed).
- `/v1/models` lists 8 models, all `owned_by: anthropic` and
  `supported_endpoint_types: ["anthropic"]` — but the OpenAI-style
  `/v1/chat/completions` ALSO responds, so `type: openai` in config is correct.
  (Lesson: probe both endpoints; don't trust the `supported_endpoint_types` tag.)
- Models: claude-opus-5, claude-opus-4-8, claude-opus-4-7, claude-opus-4-6,
  claude-fable-5-1, claude-sonnet-4-6, claude-sonnet-5, claude-haiku-4-5-20251001.

## Status (re-check before relying on it)

- 2026-09-11: key authenticates (models list OK) but every model returns
  `{"error":"Insufficient balance"}` on both `/v1/chat/completions` and
  `/v1/messages`. Account has no credit — the Hermes config is correct; do not set
  as default until topped up.
- In this state `hermes chat -q` with this provider hangs silently (see SKILL.md
  pitfalls) — always verify with curl first.

## Verify (after top-up)

```bash
curl -s https://cc.freemodel.dev/v1/chat/completions \
  -H "Authorization: Bearer $FREEMODEL_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-5","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```
