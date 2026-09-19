# Atria ASI — api.atria-asi.ai

Provider verified 2026-09-15. Simple OpenAI-compatible API, no separate plugin needed.

## Setup (native custom provider)

```bash
hermes config set model.provider custom
hermes config set model.base_url https://api.atria-asi.ai/v1
hermes config set model.api_key atr_YOUR_KEY_HERE
hermes config set model.default Atria-Dawn-Preview
```

## Model

- `Atria-Dawn-Preview` (only model available)
- Reasoning model: returns `reasoning_content` in response
- May return `content: null` with small `max_tokens` (budget spent on thinking)
- Verify with `max_tokens >= 500`

## Verification

```bash
# List models
curl -s https://api.atria-asi.ai/v1/models \
  -H "Authorization: Bearer $ATRIA_API_KEY"

# Chat test (max_tokens 500+ to get actual content, not just reasoning)
curl -s https://api.atria-asi.ai/v1/chat/completions \
  -H "Authorization: Bearer $ATRIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"Atria-Dawn-Preview","messages":[{"role":"user","content":"di solo HOLA_OK"}],"max_tokens":500}'
```

## Notes

- Backend: vllm-0.26.0-tp8
- Auth: standard `Authorization: Bearer`
- No x-api-key needed