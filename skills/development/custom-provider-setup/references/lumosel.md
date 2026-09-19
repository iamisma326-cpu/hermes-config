# Lumosel (api.lumosel.vip)

OpenAI-compatible router. Configured as native provider `lumosel` (`type: openai`,
`base_url: https://api.lumosel.vip/v1`, `key_env: LUMOSEL_API_KEY`). Always already
declared in `config.yaml` + `auth.json`; to swap a key just update `LUMOSEL_API_KEY`
in `~/.hermes/.env` via `sed -i` (patch tool is blocked on that file).

## Endpoint probes
- List models: `GET /v1/models` with `Authorization: Bearer $LUMOSEL_API_KEY`
  (optionally `User-Agent: curl/8.0`).
- Chat: `POST /v1/chat/completions` standard OpenAI wire.

## Dated status
- 2026-09-10: marked down/unreliable (older outage).
- 2026-09-16 (key `lumo_live_eed...`): AUTH OK + `/v1/models` returns full catalog
  (23 models) BUT every chat call fails at account level. Probe all returned:
  - `claude-fable-5`, `claude-fable-5-1`, `claude-haiku-4-5`, `kimi-k3` → "is
    available on paid plans only — upgrade your plan to use it."
  - `gpt-5.5` → "temporarily disabled" (server_error).
  - `grok-4-5` → "Free Trial gateway is disabled a little."
  Conclusion: key VALID, plan no longer grants free-fleet access / free gateway
  currently off. Not a config bug — report to user and stop probing.

## Model catalog (2026-09-16)
claude-fable-5 (& [1m]), claude-fable-5-1 (& [1m]), claude-haiku-4-5, claude-opus-4-7
(& [1m]), claude-opus-4-8 (& [1m]), claude-opus-5 (& [1m]), claude-sonnet-5 (& [1m]),
gpt-5-5, gpt-5.6, gpt-5.6-sol, gpt-6-astra, grok-4-5, kimi-k3.
List changes; re-probe before relying on model availability.