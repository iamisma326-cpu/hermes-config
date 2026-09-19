---
name: hermes-ecosystem-disambiguation
description: Use when "Hermes" refers to two tools (Agent vs Workspace).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, disambiguation, naming-collision, third-party, workspace, ecosystem]
---

# Hermes Ecosystem Disambiguation

## When to Use

Use when a user asks about "Hermes" and it is unclear whether they mean Hermes
Agent (Nous Research, the agent running this session) or a third-party tool
sharing the name (e.g. Hermes Workspace at `hermes-workspace.com`), or when
they conflate the two — e.g. "the GUI is different from hermes-workspace.com".

"Hermes" is an overloaded name. Before answering a question about "Hermes",
keep the major products separate — conflating them produces wrong install
commands and wrong claims about what the tool is.

## The two (or more) "Hermes" products

### 1. Hermes Agent — Nous Research (this agent)
- Framework/agent by Nous Research (Teknium).
- Surfaces: CLI, Ink TUI (`hermes --tui`), native desktop app (`hermes desktop`
  / `hermes gui`), web dashboard (`hermes dashboard`), messaging gateway, ACP
  for IDEs.
- Repo: `github.com/NousResearch/hermes-agent`
- Docs: `https://hermes-agent.nousresearch.com/docs/`
- Primary docs index (one line per feature): `/docs/llms.txt`

### 2. Hermes Workspace — third party (`hermes-workspace.com`)
- Community/third-party project, repo `github.com/outsourc-e/hermes-workspace`
  (~5.5k stars, MIT).
- A Vite + TanStack Start web frontend that WRAPS Hermes Agent. Three services
  make it work: Workspace UI on `:3000` (`pnpm dev`), the Hermes Agent gateway
  on `:8642`, and the Hermes Agent **dashboard on `:9119`**.
- `pnpm dev` auto-spawns `hermes gateway run` as a CHILD process of vite
  (see `vite.config.ts`) — it reuses an already-running gateway or starts one.
  Running `hermes gateway run` manually first is redundant (harmless).
- The Workspace NEVER auto-starts the dashboard. Skills, MCP, Config, and Jobs
  in the Workspace UI are backed by the dashboard (`:9119`), not the gateway —
  without it the UI shows "Not available on this backend. Connect to a Hermes
  Agent gateway to unlock Skills/MCP". Fix recipe and full architecture:
  `references/workspace-troubleshooting.md`.
- Pitches itself as an "AI agent's command center": chat, memory, skills,
  browser-native terminal (pty), dashboard metrics, "Conductor" mission
  orchestrator.
- Install: `curl -fsSL https://hermes-workspace.com/install.sh | bash`

## Pitfalls

- **Not the same product.** "the GUI" for Hermes Agent is `hermes desktop` (or
  `hermes dashboard`); Hermes Workspace is a separate third-party web layer.
- **Confusing surfaces**: if a user asks to "open the Hermes Workspace" they may
  mean the native desktop app, the dashboard, or this third-party frontend.
  Ask which one before issuing an install/launch command.
- **Third-party trust check**: when the answer involves a `curl | bash`
  installer from a non-Nous domain, advise reviewing the script before running
  it (download and inspect first), rather than blindly piping to bash.

## Clarify pattern

When "Hermes Workspace" / "open Hermes" is ambiguous, offer these options:
1. Hermes Agent CLI/terminal (the chat this agent runs in)
2. Hermes Desktop (`hermes desktop` / `hermes gui`) — native GUI
3. Hermes Dashboard (`hermes dashboard`) — web admin panel
4. `~/.hermes` directory (config/files)
5. Hermes Workspace (third-party `hermes-workspace.com` web frontend)

## Launch commands quick reference

```bash
hermes desktop      # native GUI  (alias: hermes gui)
hermes dashboard    # web admin panel + embedded chat
hermes gateway run  # backend gateway (used by Hermes Workspace too)
```