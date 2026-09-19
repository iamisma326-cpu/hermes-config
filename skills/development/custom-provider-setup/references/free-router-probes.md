# Free-router live probes (OpenAI-compatible)

Dated 2026-09-12. Results EXPIRE WEEKLY — free-tier routers add/remove `:free`
models constantly. Re-run before relying on any chain; never store probe results
as permanent facts in memory.

## Probe script (stdlib only; reads ~/.hermes/.env; never prints keys)

```python
import json, urllib.request, urllib.error, time

keys = {}
for line in open('/home/isma/.hermes/.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        keys[k] = v.strip().strip('"\'').strip()

def chat(name, url, model, key, timeout=40):
    # max_tokens=500: reasoning models spend small budgets on thinking → empty content
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": "Responde solo: HOLA_OK"}],
                       "max_tokens": 500}).encode()
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('User-Agent', 'curl/8.0')   # WAFs reject AsyncOpenAI UA
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
            txt = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"OK  {name:14} {model:28} {str(txt)[:35]!r} ({time.time()-t0:.1f}s)")
            return True
    except urllib.error.HTTPError as e:
        print(f"ERR {name:14} {model:28} HTTP {e.code}: {e.read()[:100].decode(errors='replace')}")
    except Exception as e:
        print(f"ERR {name:14} {model:28} {type(e).__name__}: {str(e)[:70]}")
    return False

CHAIN = [
    ("tokenrouter", "https://api.tokenrouter.com/v1", "z-ai/glm-5.3-free",        "TOKENROUTER_API_KEY"),
    ("tokenharbor", "https://tokenharbor.ai/v1",      "deepseek-v4.1-flash:free", "TOKENHARBOR_API_KEY"),
    ("unorouter",   "https://api.unorouter.com/v1",   "glm-5.3-flash:free",       "UNOROUTER_API_KEY"),
    ("nvidia",      "https://integrate.api.nvidia.com/v1", "z-ai/glm-5.3-flash",  "NVIDIA_API_KEY"),
]
for name, url, model, env in CHAIN:
    chat(name, url, model, keys.get(env, ""))
```

Also probe `/v1/models` (same auth) to discover current `:free`/`flash` IDs before
chat-probing — model IDs churn faster than anything else.

## Error triage

| Signal | Meaning | Action |
|---|---|---|
| HTTP 402 payment_required / insufficient credits | Key valid, account broke | Drop provider from chain |
| HTTP 403 plan does not include model | Model needs paid plan | Try another model ID |
| HTTP 404 model does not exist | Model gone / renamed | Swap candidate (weekly churn) |
| HTTP 403 + UA/blocked wording | WAF rejecting client UA | Use `User-Agent: curl/8.0` |
| DNS "No address associated with hostname" | Wrong base_url (you guessed it) | Check `~/.hermes/auth.json` for real URL |
| Timeout (read timed out) | Intermittent/overloaded | Keep as LOW-priority fallback |
| HTTP 200 + empty content | Reasoning model, budget too small | Re-probe with max_tokens >= 500 |

## Dated results (2026-09-12, from gestionest1 WhatsApp analysis)

| Provider | Model | Result |
|---|---|---|
| tokenrouter (api.tokenrouter.com) | z-ai/glm-5.3-free | OK 4.5-7.6s, 148 tokens, reasoning model |
| tokenharbor | deepseek-v4.1-flash:free | OK 2.7s |
| tokenharbor | deepseek-v4-flash:free | OK 21.7s |
| unorouter | glm-5.3-flash:free | OK 13s first hit, then 2 timeouts — intermitente |
| nvidia | z-ai/glm-5.3-flash | HTTP 200 3.1s, reasoning model (needs max_tokens>=500) |
| bynara (router.bynara.id) | glm-5.3-free / deepseek-v4.1-flash-free | 402 sin saldo / 403 plan |
| xkiro | *:free | 404/403 — ya no ofrece modelos free (había en ago-2026) |
| b.ai | glm-5.3-flash | 402 balance=0 |
| apinex / orcarouter | — | DNS muerto (domains down) |

## For building a failover chain (OmniRoute-inspired)

Order by probe latency; on 429/5xx/timeout skip to next provider with a ~5 min
cooldown; on 404 lock out only that MODEL (not the provider); always end with a
fixed no-LLM courtesy reply so the caller never hard-fails. Working PHP design in
`~/projects/gestionest1/docs/analisis_whatsapp_automatizacion_v5.md` §6.
