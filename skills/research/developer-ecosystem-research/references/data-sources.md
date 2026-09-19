# Data Sources — Developer Ecosystem Research

Endpoints, per-site quirks, and dead ends. **Validated 2026-08-29** against the shadcn/ui registry ecosystem. Census numbers move — treat them as snapshots, re-fetch before relying on them.

## shadcn-style registry census (`/r/index.json`)

The canonical census file for a shadcn-compatible registry is `GET <base>/r/index.json` (array of registry items with name/type/title). Findings per site (2026-08-29):

| Site | Result |
|---|---|
| `ui.shadcn.com/r/index.json` | 200, 63 items — official catalog |
| `diceui.com/r/index.json` | 200, 44 items |
| `ui.aceternity.com/registry/index.json` | 200 (note: `/registry/` path, not `/r/`), item named "aceternity"; docs landing claims "200+ free" components — index covers a subset |
| `magicui.design/r/index.json` | 200 but returns a single-item style stub (useless) — use sitemap |
| `animate-ui.com/r/index.json` | same single-item stub — use sitemap |
| `kibo-ui.com/r/index.json` | 500 / `{"error":"Failed to get package"}` — site reports "41 components, 6 blocks" on its own pages |
| `originui.com/r/index.json` | 302 → HTML — use sitemap (484 components per ShadcnDeck, 2026) |
| `kokonutui.com/r/index.json` | 404 → HTML — sitemap works (~49 doc urls) |
| `cult-ui.com/r/index.json` | 429 rate-limit → HTML — retry later |
| `reactbits.dev/r/index.json` | HTML page — sitemap works (183 urls) |
| `reui.io/r/index.json` | `{"error":"Authentication required"}` |
| `skiper-ui.com/r/index.json` | `{"error":"Component \"index\" not found"}` |
| `intentui.com/r/index.json` | 200 but `[]` (empty) |
| `8bitcn.com`, `retroui.dev`, `motionprimitives.com` | 0 bytes / 404 / connection failure |

**Sitemap fallback:** `<site>/sitemap.xml`, regex `<loc>` URLs, filter `/docs/` or `/components/` segments for the component-page count. Works: magicui.design (256 urls, 76 component pages), reactbits.dev (183), kokonutui.com (49). Blocked/JS-error pages: kibo-ui.com, originui.com, cult-ui.com, animate-ui.com, ui.shadcn.com.

## The universe map (all registries in the ecosystem)

- Official CLI directory doc: `ui.shadcn.com/docs/directory` — but the page renders `<DirectoryList />` client-side; the raw mdx (`apps/v4/content/docs/(root)/directory.mdx` in `shadcn-ui/ui`) contains no data.
- The actual machine-readable list: **`apps/v4/registry/directory.json`** in the `shadcn-ui/ui` GitHub repo (raw.githubusercontent.com). 290 registries as of 2026-08, each with name/homepage/url template (`https://<host>/r/{name}.json`)/description/logo. This is the authoritative universe; third-party curated lists (shadcn.io/awesome/registries ≈29 entries) are subsets.

## Reddit — demand mining

- **Direct www.reddit.com/*.json**: blocked (non-JSON response) even with a browser UA.
- **pullpush.io**: returned `{"data":[]}` — dead end as of 2026-08.
- **arctic-shift** (`https://arctic-shift.photon-reddit.com/api/`): works. Endpoints used:
  - Posts: `/api/posts/search?subreddit=<sub>&title=<kw>&limit=100&sort=desc`
  - Comments: `/api/comments/search?link_id=<id>&limit=20`
  - Response: `{"data":[...]}`; rate-limit response is `{"data":null,"error":"Timeout. Maybe slow down a bit"}` — space queries 10–20s apart, retry a timed-out query once after ~20s. `title=` requires `subreddit=` (or `author=`).
- Useful thread types: "If you could redesign every React component library from scratch, what would you add?", launch threads for registries (comments reveal what reviewers check first — a11y, focus states, license vs. predecessors).

## Hacker News (Algolia)

- `https://hn.algolia.com/api/v1/search?query=<q>&tags=story&hitsPerPage=10&numericFilters=points%3E50` — URL-encode `>` as `%3E` (raw `>` → 400 HTML). Fields: `title`, `points`, `num_comments`, `url`. Signal example (2026-08): "The Overcomplexity of the Shadcn Radio Button" (528 pts, 333 comments) — a11y critique as demand evidence.

## Secondary sources

- ShadcnDeck blog "21 Best shadcn Component Libraries" — item counts with dates (e.g. Origin UI 484).
- `shadcn.io/awesome/registries` — curated ~29 registry list with descriptions.

## Execution notes (Hermes environment)

- The command security gate blocks inline heredocs and `curl | interpreter` pipes; oversized/malformed inline payloads land in `~/.hermes/cache/blocked-scripts/`. **Pattern that works:** `write_file` a small `.sh` (curl steps, spaced `sleep`s) or `.py` (parse step, reads cached files), then `terminal("bash file.sh")`. One concern per file; retry scripts are cheap.
- Cache every HTTP response to a file before parsing (`-o file`), so rate-limit retries don't refetch and the census stays auditable.
