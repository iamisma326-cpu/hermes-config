#!/usr/bin/env python3
"""
Bulk-probe all chat models in an OmniRoute provider's catalog and classify
each as ok / slow / 404 / 410 / cooldown / timeout.

Usage:
    python3 probe_provider.py <provider-short-name> [gateway_url] [max_latency_s]

Example:
    python3 probe_provider.py nvidia http://localhost:20128 10

Reads the model catalog from ~/.omniroute/storage.sqlite (key_value table,
key = '<provider>:<connection-uuid>') and tests each via the gateway's
OpenAI-compatible /v1/chat/completions endpoint.

Output: a Markdown table with status, status code, latency, and a short
error excerpt. Skips models that look non-chat (embed, vision-specialty
keywords — see --include-non-chat to override).
"""

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DB = Path.home() / ".omniroute" / "storage.sqlite"
NON_CHAT_KEYWORDS = (
    "embed", "asr", "tts", "whisper", "parakeet", "tacotron",
    "fastpitch", "riva-translate", "flux", "rerank", "video-detector",
    "safety-guard", "nemoguard", "llama-guard", "reward", "parse",
    "kosmos", "nvclip", "recurrentgemma", "fuyu-8b", "deplot", "vila",
    "neva-22b", "muse-glimmer", "arctic-embed", "nv-embedqa", "tacotron2",
)


def list_connections(provider):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "SELECT id, name, is_active, test_status FROM provider_connections WHERE provider=?",
        (provider,),
    )
    rows = cur.fetchall()
    con.close()
    return rows


def load_catalog(provider, connection_id):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT value FROM key_value WHERE key=?", (f"{provider}:{connection_id}",))
    row = cur.fetchone()
    con.close()
    if not row:
        return []
    return json.loads(row[0])


def is_chat_model(model_id):
    return not any(k in model_id.lower() for k in NON_CHAT_KEYWORDS)


def test_model(gateway, provider, model_id, timeout_s):
    payload = json.dumps(
        {
            "model": f"{provider}/{model_id}",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8,
            "stream": False,
        }
    )
    try:
        result = subprocess.run(
            [
                "curl", "-sS", "--max-time", str(timeout_s),
                "-X", "POST", f"{gateway}/v1/chat/completions",
                "-H", "Content-Type: application/json",
                "-H", "Authorization: Bearer dummy",
                "-d", payload,
                "-w", "\n__HTTP__%{http_code}__%{time_total}",
            ],
            capture_output=True, text=True, timeout=timeout_s + 5,
        )
        out = result.stdout
    except subprocess.TimeoutExpired:
        return "000", timeout_s, "curl timed out"

    if "__HTTP__" not in out:
        return "000", timeout_s, (result.stderr or "no response")[:200]

    body, _, meta = out.rpartition("__HTTP__")
    code, _, time_s = meta.partition("__")
    return code.strip(), float(time_s or 0), body.strip()[:200]


def classify(code, latency_s, max_latency_s, body):
    if code == "200":
        return f"✅ OK ({latency_s:.1f}s)"
    if code == "000":
        return f"⏱️ TIMEOUT"
    if "reset after" in body.lower():
        return f"🟡 COOLDOWN (HTTP {code})"
    if code == "410" or "end of life" in body.lower():
        return f"💀 EOL (HTTP 410)"
    if code == "404":
        return f"❌ NOT_FOUND (HTTP 404)"
    if code == "429":
        return f"🚦 RATE_LIMIT (HTTP 429)"
    if code in ("500", "502", "503"):
        return f"🔥 UPSTREAM (HTTP {code})"
    return f"❓ HTTP {code}: {body[:80]}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    provider = sys.argv[1]
    gateway = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:20128"
    max_latency = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    include_non_chat = "--include-non-chat" in sys.argv

    connections = list_connections(provider)
    if not connections:
        print(f"No connections for provider '{provider}' in {DB}")
        sys.exit(1)

    print(f"## Probing {len(connections)} connection(s) for provider '{provider}'")
    print(f"Gateway: {gateway}  |  max acceptable latency: {max_latency}s")
    print()

    for conn_id, conn_name, is_active, test_status in connections:
        print(f"### Connection: {conn_name} ({conn_id}) — active={is_active}, status={test_status}")
        catalog = load_catalog(provider, conn_id)
        if not catalog:
            print("  (no catalog in key_value)")
            continue

        chat_models = [m["id"] for m in catalog if include_non_chat or is_chat_model(m["id"])]
        skipped = len(catalog) - len(chat_models)
        print(f"  {len(chat_models)} chat models, {skipped} non-chat skipped")
        print()

        ok = []
        bad = []
        cooldown = []
        slow = []
        eol = []
        for mid in chat_models:
            code, latency, body = test_model(gateway, provider, mid, int(max_latency) + 5)
            verdict = classify(code, latency, max_latency, body)
            print(f"  - `{mid}`: {verdict}")
            if code == "200":
                if latency <= max_latency:
                    ok.append((mid, latency))
                else:
                    slow.append((mid, latency))
            elif "COOLDOWN" in verdict:
                cooldown.append(mid)
            elif "EOL" in verdict:
                eol.append(mid)
            else:
                bad.append(mid)
            time.sleep(0.2)  # gentle on the gateway

        print()
        print(f"**Summary for {conn_name}:**")
        print(f"  - OK (≤{max_latency}s): {len(ok)}")
        print(f"  - Slow (>{max_latency}s but <timeout): {len(slow)}")
        print(f"  - Cooldown (own previous test): {len(cooldown)}")
        print(f"  - End-of-life (410): {len(eol)}")
        print(f"  - Broken (404/other): {len(bad)}")
        if bad:
            print()
            print("**Broken models to remove from catalog:**")
            for m in bad:
                print(f"  - `{m}`")
        if slow:
            print()
            print("**Slow models (consider removing from combos):**")
            for m, lat in slow:
                print(f"  - `{m}` ({lat:.1f}s)")


if __name__ == "__main__":
    main()
