# Research pipeline — uniqueness validation for new components

Validated 2026-08-29 against the components catalog. Goal: prove an idea has
no equivalent in the competitive set BEFORE building it.

## 1. Census sources (what worked, what didn't)

| Source | Endpoint | Status |
|---|---|---|
| shadcn official | `https://ui.shadcn.com/r/index.json` | works (63 items) |
| DiceUI | `https://diceui.com/r/index.json` | works (44 items) |
| Aceternity | `https://ui.aceternity.com/registry/index.json` | works (278 items) |
| Magic UI | `https://magicui.design/sitemap.xml` | works (76 component pages) |
| React Bits | `https://reactbits.dev/sitemap.xml` | works (183 urls) |
| Kokonut UI | `https://kokonutui.com/sitemap.xml` | works (~46 docs pages) |
| Official registry directory | `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/directory.json` | works (290 registries) |
| Kibo UI, Origin UI, Animate UI, Cult UI | `/r/index.json` | blocked (500/redirect/HTML/429) — verify manually on their sites |

Always send a browser User-Agent header. Sitemap pattern for component slugs:
`<loc>.../components/<slug></loc>` or `.../docs/<category>/<slug></loc>`.

## 2. Demand mining (what users complain about)

- **Reddit via arctic-shift** (public archive API, no auth):
  `https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=reactjs&title=component&limit=100&sort=desc`
  - Heavily rate-limited: sleep 15-20s between requests or you get
    `{"error":"Timeout. Maybe slow down a bit"}`. Cache responses to disk.
  - `title` param REQUIRES `subreddit` or `author`.
  - Comments: `.../api/comments/search?link_id=<id>&limit=20`.
  - www.reddit.com JSON endpoints return non-JSON (blocked) via curl.
- **HN Algolia**: `https://hn.algolia.com/api/v1/search?query=shadcn&tags=story&hitsPerPage=10`
  — URL-encode numericFilters (`points%3E50`); raw `>` gives a 400.
- Signal found this way: demand concentrates in data-dense UIs, verifiable
  a11y, app-state components (empty/error/loading), and multi-step forms —
  NOT in more decorative animations (those are saturated: ~90% of the
  catalog's "animated" set is duplicated by Magic UI / React Bits).

## 3. Diff mechanics (apps/web/scripts/research/diff-ideas.mjs)

- Own census: regex `slug:\s*"([\w-]+)"` over `src/lib/components.tsx`.
- Normalization: lowercase, strip non-alphanumerics, then a SYNONYMS map
  (counter ≈ numberticker ≈ countup; shimmer ≈ shine; marquee ≈ logoloop…).
- Output: `report-<date>.md` with per-candidate verdict (UNIQUE / exists in X)
  plus collisions of existing own components. Keep the report — it is the
  audit trail justifying each batch.
- Honest scope adjustments are allowed but must be stated: e.g. skipped
  `resizable-split` because our own SplitView already covers it; degraded
  `timeline` to backlog when DiceUI+Aceternity turned out to have it;
  built `auto-breadcrumb` with a differentiating angle (real-width
  measurement, auto-collapse) since shadcn's breadcrumb needs manual ellipsis.

## 4. Positioning thesis (evidence-backed)

The market is saturated on aesthetics and near-empty on function. Winning
angle for this catalog: "componentes que trabajan, no solo presumen" —
data-density, app states, accessibility. Product differentiators no
competitor has: per-component ownership metrics (LOC, real gzip KB, deps)
via `scripts/build-metrics.ts` → `public/metrics.json`, and the
Tailwind⇄CSS variant toggle on every code tab.
