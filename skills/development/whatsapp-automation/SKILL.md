---
name: whatsapp-automation
description: Use when wiring WhatsApp alerts or bots into any app.
version: 1.0.0
---

# WhatsApp Automation

Two lanes for integrating WhatsApp with an app, plus the bot architecture and
LLM-fallback pattern that work on both. (Full detail: `references/waha-knowledge-bank.md`.)

## When to use

- An app must SEND WhatsApp alerts/notifications (trámites, pagos, pedidos).
- A bot must RECEIVE commands/reactions from staff or users.
- Choosing between self-hosted (free, ban-risk) and official (paid, zero-risk).

## 1. Choose the lane

| Lane | Cost | Risk | When |
|---|---|---|---|
| A. Self-hosted WAHA/Evolution (Docker) | $0 | Bot number CAN be banned (ToS) | MVP, demos, low volume (10-30 msg/day) |
| B. Official Cloud API + Coexistence | ~$0.02/utility msg; 1,000 free service msgs/mo per number since oct-2026 | Zero (official channel) | Production with institutional numbers |

Key facts:
- RECEIVING messages is always free; cost and risk live in the SENDER only.
- Coexistence (since May 2025): an existing WhatsApp Business app number can join
  the Cloud API without losing the app or chat history — decisive for institutional
  proposals where staff already use the app daily.
- Lane A ban isolation: run the bot on a DEDICATED cheap prepaid SIM, never the
  official numbers. If banned: new SIM, rescan QR, ~30 min. Contained by design.
  Lowest-risk pattern: bot only writes to 2-3 whitelisted staff numbers, tiny volume.

## 2. WAHA setup (lane A)

```bash
docker run -d --restart=always --name waha \
  -p 3000:3000/tcp \
  -e WHATSAPP_DEFAULT_ENGINE=WEBJS \
  -e WHATSAPP_API_KEY=<secret> \
  -v waha-sessions:/app/.sessions \
  devlikeapro/waha:chrome
```

- Motor WEBJS is the ONLY engine with buttons support; `:chrome` image also does video.
- `.sessions` volume ⇒ QR scanned ONCE, survives restarts.
- Send: `POST /api/sendText` with `{"session":"default","chatId":"<phone>@c.us","text":"..."}`,
  auth header `X-Api-Key`. chatId = international number, no `+`, `@c.us` suffix.
- Receive: webhooks are configured AT session creation (`POST /api/sessions` with
  `config.webhooks`), events `message`, `message.reaction`, `message.ack` POST to
  your endpoint.

## 3. Bot architecture: commands-first, NO IA required

90% of a staff bot is deterministic (SQL + text formatting). Build in this order:

1. Webhook inbox endpoint — verify `X-Api-Key` signature, whitelist numbers by role.
2. Text commands: `pendientes`, `validar T-XXXX`, `resumen` (regex → SQL → reply).
3. Emoji reactions as confirmations (`message.reaction` event) — supported by ALL
   engines, stable forever.
4. LLM only for free-language queries — a single optional layer with failover (§4).

If the LLM layer dies, the bot answers "No entendí. Comandos: ..." — graceful
degradation, still $0.00.

## 4. Free-LLM failover chain (OmniRoute-inspired, ~80 lines)

Order providers by live-probed latency; on 429/5xx/timeout skip to the next with a
~5 min cooldown; on 404 lock out only that MODEL; end with a fixed courtesy reply.
Probe live with the script in the `custom-provider-setup` skill
(`references/free-router-probes.md`) — free-router availability churns weekly.
Reasoning models need `max_tokens >= 500` or they return empty content.

## Pitfalls

- **Buttons/lists in unofficial libraries are FRAGILE.** Meta actively breaks them;
  Baileys/whatsapp-web.js maintainers removed them; WAHA's own docs recommend
  text/poll fallback. Design with text commands + reactions, not interactive buttons.
- **Chat history is NOT a database.** The app's DB stays the source of truth;
  WhatsApp is the notification door and shortcut only.
- Free-tier LLM routers churn weekly — re-probe the chain before every demo.
- MCP servers for WhatsApp (seejux/waha-whatsapp-mcp, Maheidem/waha-mcp-server)
  are DEV tools for coding agents, not a production bot runtime. Don't add a
  Node runtime to a PHP bot for nothing.
- Official Cloud API: from Oct 1 2026 service messages are billed after 1,000
  free/month per number; inbound stays free. Utility templates ~$0.02/msg in Peru.

## References

- `references/waha-knowledge-bank.md` — WAHA endpoints/engine matrix, Coexistence
  and oct-2026 pricing facts (dated), tested failover chain, pointer to the full
  v5 analysis in gestionest1.
