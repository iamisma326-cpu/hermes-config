#!/bin/bash
# fetch_registry_census.sh — cache /r/index.json (or sitemap fallback) for each
# shadcn-compatible registry into a census dir. Usage:
#   bash fetch_registry_census.sh [output-dir]     (default: ./census)
#
# Cached files are the audit trail: cite file + date in any uniqueness claim.
# Sites that fail index.json (see skill references/data-sources.md) are also
# fetched via /sitemap.xml when available.

set -u
OUT="${1:-census}"
mkdir -p "$OUT"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
GAP=2   # seconds between requests; raise if a site starts 429-ing

# pairs:  <slug>|<index.json url>|<sitemap url or ->
SITES="
official|https://ui.shadcn.com/r/index.json|-
diceui|https://diceui.com/r/index.json|-
aceternity|https://ui.aceternity.com/registry/index.json|-
magicui|https://magicui.design/r/index.json|https://magicui.design/sitemap.xml
animateui|https://animate-ui.com/r/index.json|https://animate-ui.com/sitemap.xml
kibo|https://www.kibo-ui.com/r/index.json|-
kokonut|https://kokonutui.com/r/index.json|https://kokonutui.com/sitemap.xml
cultui|https://cult-ui.com/r/index.json|https://cult-ui.com/sitemap.xml
reactbits|https://reactbits.dev/r/index.json|https://reactbits.dev/sitemap.xml
originui|https://originui.com/r/index.json|-
eightbitcn|https://8bitcn.com/r/index.json|-
retroui|https://retroui.dev/r/index.json|-
reui|https://reui.io/r/index.json|-
skiper|https://skiper-ui.com/r/index.json|-
intentui|https://intentui.com/r/index.json|-
eldoraui|https://eldoraui.site/r/index.json|-
hextaui|https://hextaui.com/r/index.json|-
pureui|https://pure-ui.com/r/index.json|-
shadix|https://shadix-ui.vercel.app/r/index.json|-
elevenlabs|https://ui.elevenlabs.io/r/index.json|-
"

# Ecosystem universe map: official directory of all 290 registries (2026-08).
curl -s --max-time 20 -A "$UA" -o "$OUT/_directory.json" \
  "https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/directory.json"
echo "universe map: $OUT/_directory.json ($(wc -c < "$OUT/_directory.json") bytes)"

echo "$SITES" | while IFS='|' read -r slug idx smap; do
  [ -z "$slug" ] && continue
  curl -sL --max-time 25 -A "$UA" -o "$OUT/$slug.json" "$idx"
  size=$(wc -c < "$OUT/$slug.json")
  looks_json=$(head -c 1 "$OUT/$slug.json" | grep -c '\[' || true)
  if [ "$looks_json" -eq 0 ] && [ "$smap" != "-" ]; then
    echo "  $slug: index not usable (${size}b) — fetching sitemap fallback"
    curl -sL --max-time 25 -A "$UA" -o "$OUT/$slug-sitemap.xml" "$smap"
  fi
  echo "  $slug: done"
  sleep "$GAP"
done

echo
echo "Census summary:"
for f in "$OUT"/*.json; do
  n=$(python3 -c "import json,sys;print(len(json.load(open('$f'))))" 2>/dev/null || echo "?")
  echo "  $(basename "$f"): $n items"
done
