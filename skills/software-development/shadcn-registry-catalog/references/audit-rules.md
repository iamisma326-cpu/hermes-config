# Audit rules — the two gates and how the baseline works

## Gate 1: audit-components.mjs (static quality)

Run: `node apps/web/scripts/audit/audit-components.mjs [slug-filter]`
Exit 1 on NEW findings; baseline findings print as `PASS*` and don't block.

Checks per .tsx: `"use client"` when hooks/events present; no `any`; no hex
inside className literals; `style={{}}` only for CSS vars/dynamic layout
(cosmetic-property blocklist: color, backgroundColor, fontSize, border,
boxShadow, padding…); focus-visible present when `role="button|tab|gridcell"`
used; no onClick/onKeyDown on non-semantic elements without role/tabIndex;
img has alt; rAF/listener/interval registration paired with cleanup (rAF
accepted via `ref.current = requestAnimationFrame(...)` + `cancelAnimationFrame`); `cn()` imported when className used — only enforced for
distributed dirs (components/ui|animated|utility, registry/css) and only
when the component accepts className.

Checks per .css: no `!important`; ≤4 raw hex (tokens otherwise);
`prefers-reduced-motion` required when `@keyframes`/`animation` present
(hover/focus `transition` is exempt).

Known whitelisted false positives (encoded in the script, do not re-litigate):
`role="option"` lists use `aria-activedescendant` — options never take focus;
Sonner sets className inside `toastOptions` (official shape).

### Baseline workflow
First run on a legacy tree: `node ... --update-baseline` writes
`scripts/audit/baseline.json` (keys `rel|check`). Gate = findings NOT in
baseline. Regenerate deliberately when accepting backlog debt; current
baseline ≈27 findings (mostly missing reduced-motion in older css sheets).

## Gate 2: audit-variants.mjs (variant completeness + parity)

Run: `node apps/web/scripts/audit/audit-variants.mjs`
Exits 1 on any gap. For every catalog slug (parsed from components.tsx):

- TW source exists at family path (app→components/ui, animated→components/animated,
  utility→components/utility, block→registry/blocks/<slug>-block.tsx);
- CSS variant `src/registry/css/<slug>.tsx` AND sheet `.css` exist for ALL
  families including blocks (user requirement);
- tsToJs (imported live from src/lib/ts-to-js.ts — Node TS-strip) output for
  BOTH variants free of residue: leftover interfaces, hook generics
  `useState<`, function generics, `as const`/`as React.*`, return-type
  annotations, field annotations;
- API parity: JSDoc-documented props and public exports match across TW⇄CSS;
  export aliases `A as B` resolve to B (A is internal, not "missing");
- No orphans: css/<slug>.tsx files whose slug is not in the catalog.

## Human checklist (scripts/audit/CHECKLIST.md)

Seven blocks that can't be automated: TS conventions (typed props, no any,
cn for consumer className), JS behavior (cleanup, SSR-safety, edge cases),
Tailwind (tokens only, focus-visible), CSS variant (same API, prefixed vars,
reduced-motion, dark mode), a11y (role, keyboard, aria, contrast AA both
themes), visual verification in browser (light+dark, interaction, responsive),
and the full wiring/integration list (touchpoints + JSON curl + clean-project
`npx shadcn add` smoke test).

## Verification snippets

Registry JSON: `curl -s http://localhost:3000/r/<slug> | python3 -m json.tool | head`
→ must show `files[0].content` non-empty and correct `target` (utility/…).
All-registry smoke: `curl -s http://localhost:3000/r` → index item count.
Builds: `npx tsx scripts/build-registry.ts` then
`npx tsx scripts/build-metrics.ts` (inside apps/web; the root npm script
wrongly uses pnpm). Production: `npx next build`.
