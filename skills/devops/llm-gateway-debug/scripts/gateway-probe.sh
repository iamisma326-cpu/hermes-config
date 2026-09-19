#!/bin/bash
# Test a list of provider models via a local LLM gateway, with cooldown awareness.
#
# Usage: gateway-probe.sh <base_url> <provider> <auth_header> <max_wait_for_cooldown_sec>
#   base_url: e.g. http://localhost:20128
#   provider: e.g. nvidia
#   auth_header: e.g. "Authorization: Bearer dummy"
#   max_wait_for_cooldown_sec: how long to wait before declaring results valid
#
# Reads model IDs from stdin, one per line. Prints a table with HTTP code,
# response time, and a short classification.
#
# Pitfall: gateways apply per-model cooldowns after 404. If you test the same
# model twice in a row, the second result is the local circuit breaker, not
# the upstream. This script waits up to N seconds for the cooldown to clear
# and re-tests once if it sees a "reset after" pattern.

set -e
BASE_URL="${1:?usage: gateway-probe.sh <base_url> <provider> <auth_header> <max_wait>}"
PROVIDER="${2:?missing provider}"
AUTH="${3:?missing auth header}"
MAX_WAIT="${4:-120}"

models=()
while IFS= read -r line; do
  [[ -n "$line" && "$line" != \#* ]] && models+=("$line")
done

probe() {
  local m="$1"
  local resp code time body
  resp=$(curl -sS --max-time 60 -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" -H "$AUTH" \
    -d "{\"model\":\"$PROVIDER/$m\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":3,\"stream\":false}" \
    -w "\n__HTTP__%{http_code}__%{time_total}" 2>/dev/null)
  code=$(echo "$resp" | grep -oP '__HTTP__\K[0-9]+')
  time=$(echo "$resp" | grep -oP '__HTTP__[0-9]+__\K[0-9.]+')
  body=$(echo "$resp" | sed 's/__HTTP__.*//')
  echo "$code|$time|$body"
}

wait_for_cooldown() {
  local hint="$1"
  local sec
  sec=$(echo "$hint" | grep -oP 'reset after \K[0-9]+s?' | grep -oP '[0-9]+' | head -1)
  sec=${sec:-0}
  if [[ "$sec" -gt 0 && "$sec" -le "$MAX_WAIT" ]]; then
    echo "  (cooldown ${sec}s detected, waiting)"
    sleep $((sec + 1))
  fi
}

printf "%-50s %-6s %-8s %s\n" MODEL HTTP TIME STATE
for m in "${models[@]}"; do
  r=$(probe "$m")
  code=$(echo "$r" | cut -d'|' -f1)
  time=$(echo "$r" | cut -d'|' -f2)
  body=$(echo "$r" | cut -d'|' -f3-)
  if [[ "$code" == "200" ]]; then
    state="ok"
  elif [[ "$code" == "000" ]]; then
    state="timeout"
  elif echo "$body" | grep -q "reset after"; then
    state="cooldown"
    wait_for_cooldown "$body"
    r=$(probe "$m")
    code=$(echo "$r" | cut -d'|' -f1)
    time=$(echo "$r" | cut -d'|' -f2)
    body=$(echo "$r" | cut -d'|' -f3-)
    if [[ "$code" == "200" ]]; then
      state="ok-after-cooldown"
    fi
  elif echo "$body" | grep -q "end of life"; then
    state="deprecated-410"
  elif echo "$body" | grep -qi "not exist\|not_found"; then
    state="not-in-upstream-404"
  else
    state="error"
  fi
  printf "%-50s %-6s %-8s %s\n" "$m" "$code" "${time}s" "$state"
  sleep 0.3
done
