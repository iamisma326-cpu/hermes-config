# Census sources — competitor registries & demand mining

All endpoints verified 2026-08-29 from this machine. Counts may drift; re-run
`bash apps/web/scripts/research/fetch-census.sh` to refresh `census/`.

## Registry census endpoints

| Registry | Endpoint | Status | Verified count |
|---|---|---|---|
| shadcn/ui oficial | `https://ui.shadcn.com/r/index.json` | ✅ works | 63 items |
| DiceUI | `https://diceui.com/r/index.json` | ✅ works | 44 items |
| Aceternity | `https://ui.aceternity.com/registry/index.json` (NOTE: `/r/index.json` does not exist) | ✅ works | 278 items |
| Magic UI | `https://magicui.design/sitemap.xml` (filter `/components/<slug>`) | ✅ works | 76 components |
| React Bits | `https://reactbits.dev/sitemap.xml` | ✅ works | 183 urls total |
| Kokonut UI | `https://kokonutui.com/sitemap.xml` (filter `/docs/<cat>/<slug>`) | ✅ works | 46 component docs |
| Kibo UI | `https://www.kibo-ui.com/r/index.json` + sitemaps | ❌ blocks (500 / HTML error page) | 41 comps + 6 blocks (from their docs page text) |
| Origin UI | `/r/index.json` | ❌ redirects to coss.com HTML | 484 claimed (ShadcnDeck) |
| Animate UI | `/r/index.json` | ❌ returns 288-byte style stub, no items | — |
| Cult UI | `/r/index.json` | ❌ 429 rate-limited / HTML | — |
| ElevenLabs UI | `/r/index.json` | ❌ HTML | — |
| CLI directory (all registries) | `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/directory.json` | ✅ works | 290 registries |

Notes:
- Several registries return a single-item `registry:style` stub at `/r/index.json`
  (magicui, animateui) — that is NOT their component list; use sitemaps for those.
- The official docs page for the directory is `apps/v4/content/docs/(root)/directory.mdx`
  in shadcn-ui/ui, but the real data is `apps/v4/registry/directory.json`.
- User-Agent matters: send a browser-like UA (`Mozilla/5.0 (X11; Linux x86_64)
  AppleWebKit/537.36 Chrome/126 Safari/537.36`); curl's default UA gets blocked faster.
- Registry URLs that 404/500 sometimes resolve at different paths
  (`/registry/index.json`, `/r/index.json`, `/r/registry.json`) — try those before
  concluding a registry has no index.

## diff-ideas.mjs matching

Slugs are normalized (lowercase, strip non-alphanumerics) and passed through a
SYNONYMS map (counter≈numberticker≈countup, shimmer≈shine, marquee≈logoloop,
spotlight≈spotlightcard, plus a text-effects cluster). Extend SYNONYMS when a new
collision family appears. Candidate list lives in the `CANDIDATES` array in
`diff-ideas.mjs` — update it each tanda.

Baseline report (2026-08-29): 15/16 candidates unique. `timeline` exists in
DiceUI + Aceternity → demoted to backlog. Candidate slugs and their tanda:

- Tanda 1: virtual-table, state-boundary, a11y-announcer, stepper-form, sparkline,
  compact-stat, copyable-field, duration-picker
- Tanda 2 backlog: cron-picker, file-drop, breadcrumbs, resizable-split,
  command-palette, data-table-inline-edit, blur-up-media, (timeline — colisión)

## Reddit demand mining (arctic-shift archive API)

`www.reddit.com/*.json` returns non-JSON to curl (bot-blocked). Use the public
archive instead — it is slow and rate-limited, so space requests 8–20s and save
each response to a file:

```
https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=reactjs&title=component&limit=100&sort=desc
https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=shadcnui&limit=100&sort=desc
https://arctic-shift.photon-reddit.com/api/comments/search?link_id=<post_id>&limit=20
```

- `title=` query REQUIRES `author` or `subreddit` alongside (returns an error otherwise).
- "Timeout. Maybe slow down a bit" = rate limit; wait 15–20s and retry.
- pullpush.io returned empty data in testing; prefer arctic-shift.
- Signal-quality caveat: recent-post harvests are mostly low-score self-promo.
  The useful signal came from (a) comment threads of posts matching
  redesign/wish/missing/what would you add, and (b) the a11y pile-on pattern
  (focus states, document outline) in "redesigned my library" threads.

## HN Algolia (demand signals)

```
https://hn.algolia.com/api/v1/search?query=shadcn&tags=story&hitsPerPage=10&numericFilters=points%3E50
```

- URL-encode `>` as `%3E` — a raw `>` yields 400 Bad Request.
- Verified top signal: "The Overcomplexity of the Shadcn Radio Button" (528 pts) —
  a11y-complexity complaints are a recurring theme.

## Key community threads mined (2026-08-29)

- shadcn discussion #1869 (multi-step forms, unanswered since 2023) → stepper-form
- r/reactjs "component registry for data-dense interfaces" thread → data-dense positioning
- r/reactjs app-states library thread (error/empty/loading in one component) → state-boundary
