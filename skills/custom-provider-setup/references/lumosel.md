# Lumosel Provider — Hermes Agent

**Status:** Configured, service temporarily offline (HTTP 503)

## Configuration

```bash
# Add to ~/.hermes/.env
LUMOSEL_API_KEY=lumo_live_491faabcc47c7745df275c219ad2f0f6c9002d9d

# Add to ~/.hermes/config.yaml under providers:
lumosel:
  type: openai
  base_url: https://api.lumosel.vip/v1
  key_env: LUMOSEL_API_KEY
```

## Model Plugin

Location: `~/.hermes/plugins/model-providers/lumosel/__init__.py`

```python
"""Lumosel provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile


lumosel = ProviderProfile(
    name="lumosel",
    aliases=("lumo",),
    env_vars=("LUMOSEL_API_KEY",),
    display_name="Lumosel",
    description="Lumosel — OpenAI-compatible endpoint (Claude, GPT, Grok, Kimi)",
    signup_url="https://api.lumosel.vip",
    fallback_models=(
        "claude-sonnet-5",
        "claude-opus-5",
        "gpt-5.6-sol",
        "grok-4-5",
        "kimi-k3",
    ),
    base_url="https://api.lumosel.vip/v1",
)

register_provider(lumosel)
```

## Available Models

The `/v1/models` endpoint returns these models:

- `claude-fable-5`, `claude-fable-5[1m]` — Claude Fable 5 / 1M context
- `claude-fable-5-1`, `claude-fable-5-1[1m]` — Claude Fable 5.1 / 1M context
- `claude-haiku-4-5` — Claude Haiku 4.5
- `claude-opus-4-7`, `claude-opus-4-7[1m]` — Claude Opus 4.7 / 1M context
- `claude-opus-4-8`, `claude-opus-4-8[1m]` — Claude Opus 4.8 / 1M context
- `claude-opus-5`, `claude-opus-5[1m]` — Claude Opus 5 / 1M context
- `claude-sonnet-5`, `claude-sonnet-5[1m]` — Claude Sonnet 5 / 1M context
- `gpt-5-5` — GPT 5.5
- `gpt-5.6` — GPT-5.6
- `gpt-5.6-sol` — GPT-5.6 SOL
- `gpt-6-astra` — GPT-6 Astra
- `grok-4-5` — Grok 4.5
- `kimi-k3` — Kimi K3

All support up to 200K tokens, some support 1M context window.

## Current Issue

As of 2026-09-10, all model endpoints return **HTTP 503: Gateway is offline**. The `/v1/models` list works fine; only the chat/completions endpoint is down. This may be:
- A temporary service outage
- The API key only has read access (list models but no inference)
- The gateway requires additional authorization or credits

## Testing

```bash
# List models (works)
curl -s https://api.lumosel.vip/v1/models \
  -H "x-api-key: $LUMOSEL_API_KEY"

# Test chat completions (returns 503)
curl -s https://api.lumosel.vip/v1/chat/completions \
  -H "x-api-key: $LUMOSEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-5", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}'

# In Hermes
hermes chat -q "test" --provider lumosel -m claude-sonnet-5
```

## Quick Start (when service is back)

```bash
# Set as default
hermes config set model.provider lumosel
hermes config set model.default claude-sonnet-5

# Or use inline
hermes -m lumosel/claude-sonnet-5
```
