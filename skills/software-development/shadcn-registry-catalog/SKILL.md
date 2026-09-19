---
name: shadcn-registry-catalog
description: Use when building or auditing shadcn UI registries.
---

# shadcn-registry-catalog

Class workflow for building and maintaining a shadcn-style component catalog:
validate uniqueness BEFORE building, author every component in ALL variants,
wire every catalog touchpoint, and gate completion on audits.

Primary repo: /home/isma/projects/components (npm monorepo — Next 16, React 19,
Tailwind 4, Radix, motion). Paths below are repo-relative to `apps/web/`.

## Golden rules (standing requirements from the user)

1. **Four variants per component — blocks included.** TS+Tailwind (source),
   JS+Tailwind (derived via `src/lib/ts-to-js.ts`), TS+CSS (hand-authored
   `src/registry/css/<slug>.tsx`) plus its `.css` sheet. The user explicitly
   required blocks to have CSS variants too — "todos los componentes deben
   tenerlo de forma correcta". Never exclude a family from a variant.
2. **Uniqueness gate before building.** Check candidate ideas against
   competitor censuses; only build what no competitor offers as a reusable
   component with a public API. Keep the dated verdict report as audit trail.
3. **Audits must PASS with 0 new findings** before declaring a batch done:
   `node scripts/audit/audit-components.mjs` (static quality, baseline-aware)
   and `node scripts/audit/audit-variants.mjs` (variant completeness+parity).
4. **Zero new npm dependencies** for utility components — rAF, Intl,
   ResizeObserver, Pointer Events, native `<input type="time">`, inline SVG.

## Workflow

1. **Research** (details: references/research-pipeline.md) — census from
   competitor `/r/index.json` + sitemap fallbacks + official CLI directory;
   demand mining via arctic-shift (Reddit) and HN Algolia; diff with synonym
   normalization into a dated report.
2. **Author** — Tailwind source in `src/components/<family>/<slug>.tsx`;
   CSS twin in `src/registry/css/<slug>.tsx` + `.css` (same props, same
   behavior, `hsl(var(--*))` tokens, `prefers-reduced-motion` for
   `@keyframes`); demo in `src/registry/components/<slug>-demo.tsx` exporting
   both the demo component and a `demoCode` template string.
3. **Wire** (details: references/wiring-map.md) — six touchpoints; missing
   one means a broken variant, JSON, or metric. registryDependencies must be
   identical in components.tsx, build-registry.ts and build-metrics.ts.
4. **Verify** — `npx tsc --noEmit` immediately after EVERY new file; both
   audit scripts; `npx tsx scripts/build-registry.ts` +
   `npx tsx scripts/build-metrics.ts`; `curl :3000/r/<slug>.json` has
   non-empty `files[0].content`; final `npx next build`.

## Pitfalls (each bit this codebase for real)

- **write_file output corruption**: large new component files have landed
  with spurious tokens mid-body (stray words, duplicated attrs, broken JSX).
  Countermeasure: typecheck immediately after each write; on failure REWRITE
  the whole file — patching a corrupted region made it worse both times it
  was tried. Never trust a write you have not type-checked.
- **Static-audit false positives — whitelist, don't "fix"**: `role="option"`
  lists (correct pattern is `aria-activedescendant` on the combobox input;
  options never take focus); Sonner `className` inside `toastOptions`
  (official shadcn shape, not DOM); `style={{}}` for CSS custom properties
  and dynamic layout (gridTemplateColumns, virtualization top/height);
  `prefers-reduced-motion` only mandatory for `@keyframes`/`animation`, not
  hover/focus transitions.
- **Introducing gates to legacy code**: use a baseline file (findings keyed
  `rel|check` accepted as backlog) so the gate fails only on NEW findings —
  `audit-components.mjs --update-baseline` regenerates it. Current baseline
  is 27 findings (mostly missing reduced-motion in older css/ sheets).
- **Monorepo script drift**: root `build:registry` uses `pnpm --filter` but
  the repo is npm workspaces — run `npx tsx scripts/build-registry.ts`
  inside apps/web. `next lint` no longer exists in Next 16 and there is no
  eslint config; the two audit scripts are the effective lint layer.
- **rAF cleanup**: every `requestAnimationFrame` loop stores its id in a ref
  and `cancelAnimationFrame`s on unmount (and before re-scheduling) —
  auditors check the pairing, and mid-animation unmount genuinely calls
  setState after unmount otherwise.
- **Export aliasing in CSS twins**: export the internal name aliased to the
  public name (`export { LoginFormBlockCSS as LoginFormBlock }`). The
  variant auditor resolves `A as B` aliases: public name is B, A is not a
  missing export.
- **Props colliding with native attributes**: `title`, `onChange` etc. must
  be `Omit`-ed when a component extends `React.ComponentProps<"tag">` with a
  same-named prop of a different type (tsc catches it — expect one round).

## References

- references/research-pipeline.md — census endpoints, demand mining APIs, report format
- references/wiring-map.md — annotated catalog touchpoints + snippets
- references/audit-rules.md — audit rule set, baseline workflow, variant-parity mechanics
