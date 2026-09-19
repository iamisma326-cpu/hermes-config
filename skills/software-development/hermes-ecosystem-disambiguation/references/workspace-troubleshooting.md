# Hermes Workspace — architecture & troubleshooting

Verified against a live install (hermes-agent v0.20.5, Workspace from git,
Linux, Aug 2026). Workspace repo: `~/hermes-workspace` (Vite + TanStack Start).

## Three-service architecture

| Service | Port | Started by | Role |
|---|---|---|---|
| Workspace UI | 3000 | `pnpm dev` (vite) | Web frontend + its own API routes (`/api/*`) |
| Hermes gateway | 8642 | vite auto-spawns `hermes gateway run` as a child process | chat/completions, sessions, `/v1/*` API |
| Hermes dashboard | 9119 | **nobody auto-starts it** — must be launched manually | backs Workspace's Skills, MCP, Config, Jobs, Kanban |

Key facts:

- `vite.config.ts` checks `:8642` health at startup; reuses a running gateway
  or spawns one (`detached: false`, so Ctrl+C on vite kills the gateway too).
- The dashboard serves a PRE-BUILT UI from `hermes_cli/web_dist/` inside the
  hermes-agent install — no npm build needed, starts in ~2 seconds.
  (`web/dist` being empty is normal and irrelevant.)
- Workspace capability probes (`src/server/gateway-capabilities.ts`):
  `skills = dashboard.available || /api/skills on gateway`, same for config
  and jobs. The gateway's `/v1/skills` exists but Workspace probes
  `/api/skills` (404 on gateway), so **dashboard is the effective source**.
- MCP: Workspace probes `/api/mcp` on gateway then dashboard. Older
  hermes-agent versions have no native `/api/mcp`; Workspace then falls back
  to `mcpFallback` (CRUD via dashboard `config.mcp_servers`, loopback-only).
  Test/Discover/Logs tabs stay disabled in fallback mode until hermes-agent
  is updated (`hermes update`).

## Auth wiring

- Gateway: `API_SERVER_ENABLED=true` + `API_SERVER_KEY=*** in `~/.hermes/.env`.
- Workspace: `HERMES_API_TOKEN=*** in `hermes-workspace/.env` must equal the
  gateway's `API_SERVER_KEY`, else 401s.
- Dashboard: Workspace scrapes the dashboard's ephemeral session token from
  its root HTML automatically. Never hardcode that token (changes on restart).

## Symptom → fix

**"Not available on this backend. Connect to a Hermes Agent gateway to unlock
Skills / MCP Servers"** (or `/api/skills`, `/api/mcp` return
`capability_unavailable`):

1. Check what's listening: `ss -tlnp | grep -E ':(3000|8642|9119)\b'`.
   Almost always `:9119` is missing.
2. Start the dashboard:
   `hermes dashboard --port 9119 --host 127.0.0.1 --no-open`
   (background it; log to /tmp/hermes-dashboard.log).
3. Verify: `curl -s http://127.0.0.1:9119/api/status` → 200 JSON.
   (`/api/skills`, `/api/mcp` on the dashboard return 401 without its
   ephemeral token — that's expected; Workspace handles the token.)
4. Force Workspace to reprobe:
   `curl -X POST http://localhost:3000/api/gateway-reprobe`
   Expect `skills: true, config: true, jobs: true, dashboard.available: true`,
   `mcp: true` or `mcpFallback: true`.
5. Refresh the browser (F5).

**Probe ordering pitfall:** if Workspace boots before the dashboard, it caches
capabilities as unavailable (PROBE_TTL window). Always have the dashboard up
FIRST, or fix afterwards with the reprobe POST above — no restart needed.

**Verify endpoints directly** (gateway needs the API key):
```bash
KEY=*** '^API_SERVER_KEY' ~/.hermes/.env | cut -d= -f2-)
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/skills   # 200
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/capabilities
```
`/v1/capabilities` shows `skills_api: true` even when Workspace reports
skills unavailable — that mismatch is the dashboard-missing signature.

## One-command startup

A wrapper script is the reliable pattern (dashboard first, wait for it, then
Workspace). Working example lives on this machine at
`~/.local/bin/hermes-workspace-up`:

```bash
#!/usr/bin/env bash
set -u
HERMES_BIN="$HOME/.hermes/hermes-agent/venv/bin/hermes"
if curl -s -m 2 http://127.0.0.1:9119/api/status >/dev/null 2>&1; then
  echo "[up] Dashboard already running on :9119"
else
  nohup "$HERMES_BIN" dashboard --port 9119 --host 127.0.0.1 --no-open \
    >/tmp/hermes-dashboard.log 2>&1 &
  for i in $(seq 1 60); do
    curl -s -m 2 http://127.0.0.1:9119/api/status >/dev/null 2>&1 && break
    sleep 1
  done
fi
cd "$HOME/hermes-workspace" && exec pnpm dev
```

Ctrl+C kills Workspace + gateway (parent/child); the dashboard survives and is
reused on the next run (idempotent health check prevents duplicates).

## Changing the default model for Workspace chats

Workspace chat sends no explicit model unless the UI picks one, so the gateway
falls back to `model.default` in `~/.hermes/config.yaml`. Set it with:
`hermes config set model.default <model-id>` (never hand-edit config.yaml).
The gateway re-reads config per request — no restart needed. Verify the model
id exists on the provider first (`/v1/models` on the provider's base_url).
