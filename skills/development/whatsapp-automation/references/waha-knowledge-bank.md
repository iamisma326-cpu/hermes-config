# WAHA + WhatsApp integration knowledge bank

Facts distilled from live research 2026-09-12 (gestionest1 WhatsApp analysis v5 —
full write-up with citations in
`~/projects/gestionest1/docs/analisis_whatsapp_automatizacion_v5.md`).
Dated facts below EXPIRE — pricing dates are stable, model offerings are not.

## WAHA (WhatsApp HTTP API)

- Open source (Apache-2.0), ~7.3k stars, self-hosted Docker, REST + Swagger
  dashboard, 1-500 sessions per server, webhook events.
- Engines: WEBJS (browser/Puppeteer — ONLY one with buttons; `:chrome` image adds
  video), NOWEB (Node WS, lightest), GOWS (Go WS), WPP, VENOM. Default engine via
  `WHATSAPP_DEFAULT_ENGINE` env.
- Docker image tags: `devlikeapro/waha:latest` (Chromium), `:chrome` (Chrome+video),
  `:noweb`, `:gows`, `-arm` variants.
- Send text: `POST /api/sendText` `{"session":"default","chatId":"<num>@c.us","text":"..."}`
  — number international WITHOUT `+`, suffixed `@c.us`. Auth: `X-Api-Key` header.
- Receive: webhooks configured at session creation —
  `POST /api/sessions {"name":"bot","config":{"webhooks":[{"url":"...","events":["message","message.reaction","message.ack"]}]}}`.
  `message.reaction` carries `payload.reaction.text` (emoji, empty on removal) and
  `.messageId` → maps cleanly to "staff confirms alert T-XXXX with ✅".
- Session persistence: mount `/app/.sessions` volume → scan QR once, survives restarts.
- Clicking a button programmatically (testing): `POST /api/send/buttons/reply` with
  `selectedButtonID` — WEBJS only.
- Anti-ban doc advice: send `sendSeen` before replying to unread messages.
- CE edition is free; WAHA Plus (paid) adds横向 features — core REST/webhooks/sessions
  are all in CE.

## Buttons/Lists fragility (why commands-first)

- Meta war-stories: buttons in unofficial libs patched/broken repeatedly since 2021;
  maintainers of Baileys + whatsapp-web.js removed buttons/lists from official repos
  (purpshell's dev.to write-up documents the whole cat-and-mouse).
- WAHA docs on Send List: "List Messages are fragile creatures and may stop working
  at any time. We recommend adding fallback logic using Send Text or Polls."
- WAHA discussion #938 (community asking for lists) met with the same fragility answer.
- Stable UX substitutes: text commands, reply-quoting (replyTo), emoji reactions
  (all-engine events), and the chat history itself as the chronological "listado".

## Official Cloud API (lane B) — dated facts

- Coexistence (May 2025): Business-app number joins Cloud API keeping the app,
  history (6 months sync), groups, calls. One-directional (app→API, not back).
- Pricing from Oct 1 2026: service messages billed per delivery AFTER 1,000
  free/month PER NUMBER (reset monthly, no rollover); inbound always free; utility
  templates ~$0.02/msg in Peru; utility-inside-window also billed from that date.
  Conversation-based pricing ended Jul 2025 (per-message model).
- Free entry point: Click-to-WhatsApp ad opens a 72h free window.
- Onboarding cost is PAPERWORK: Meta Business portfolio verification — one-time.

## Tested free-LLM failover chain (2026-09-12)

tokenrouter `z-ai/glm-5.3-free` → tokenharbor `deepseek-v4.1-flash:free` →
unorouter `glm-5.3-flash:free` (intermittent) → nvidia `z-ai/glm-5.3-flash` →
Groq `llama-3.1-8b-instant` (30 RPM / 14.4K req/day free, no card; untested — needs
account) → fixed no-LLM courtesy reply. Error triage + probe script: see
`custom-provider-setup` skill → `references/free-router-probes.md`.

## MCP (dev tooling, not production)

- seejux/waha-whatsapp-mcp — chat ops + MCP resources, stdio.
- Maheidem/waha-mcp-server — 28 tools incl. transcription, voice-note auto-replies.
- Use for debugging/exploring from a coding agent; a production PHP bot talks
  REST directly.

## Alternative: Evolution API

Open source, more bundled integrations (Typebot/Chatwoot/n8n), Baileys + Cloud API
channels. Pick WAHA for simpler REST/Docker; Evolution if those integrations matter.
