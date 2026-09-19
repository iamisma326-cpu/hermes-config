# Wiring map — every touchpoint a new component must update

Missing any one of these produces a broken variant, empty registry JSON, or
stale metrics. Verified against the components catalog (72 components).

## The six touchpoints

1. **`src/lib/components.tsx`** — three places inside this one file:
   - entry in `components: CatalogComponent[]` (slug, name, description,
     family, category, registryDependencies, dependencies, demos, install);
   - import of the demo: `import { XDemo, xDemoCode } from "@/registry/components/<slug>-demo"`;
   - key in the `demos: Record<string, ComponentType>` map.
2. **`scripts/build-registry.ts`** — entry in `componentSources[]`:
   `{ slug, name, description, family, srcPath: "components/<family>/<slug>.tsx", targetPath: "<family>/<slug>.tsx", dependencies?, registryDependencies? }`.
   Blocks use `srcPath: "registry/blocks/<slug>-block.tsx"`.
3. **`src/app/r/[name]/route.ts`** — `resolveSourcePath()`: animated slugs
   live in a Set → `animated/<slug>.tsx`; utility slugs in a Set →
   `utility/<slug>.tsx`; blocks in a Set → `../registry/blocks/<slug>-block.tsx`;
   everything else falls through to `ui/<slug>.tsx`. Also `targetDir`:
   block → `blocks`, utility → `utility`, else `ui`.
4. **`src/lib/component-code.ts`** — `tailwindSourcePath()` switch on family
   (app → components/ui, animated → components/animated, utility →
   components/utility, block → registry/blocks). Missing case = code viewer
   shows empty TS+Tailwind tab.
5. **`scripts/build-metrics.ts`** — entry in its COMPONENTS list with deps
   and registryDeps (public/metrics.json feeds the "Coste de propiedad"
   strip on each detail page).
6. **Demo file** `src/registry/components/<slug>-demo.tsx` — exports BOTH
   `export function XDemo()` and `export const xDemoCode = \`...\``
   (camelCase + Demo/Code suffixes are load-bearing for the import line).

## Consistency requirements

- registryDependencies MUST be identical in touchpoints 1, 2 and 5.
- The `family` union type lives in `components.tsx` and is mirrored in
  build-registry.ts and build-metrics.ts; `catalog-explorer.tsx` ALSO
  hardcodes the family list (FamilyFilter type, toggle buttons array, and a
  filtered section block) — add new families there too. Detail-page badge
  (`components/[name]/page.tsx`) has its own family ternary.
- Categories: new `ComponentCategory` values need a CATEGORIES entry in
  `catalog-explorer.tsx`.

## Conventions

- CSS twins: import the sheet (`./<slug>.css`), root class = short prefix
  (`lf__*`, `vt__*`, `sp__*`…), tokens via `hsl(var(--*))`, alias the export:
  `export { XCSSL  as X }` pattern (internal `XCSS`, public `X`).
- Demos must be SSR-deterministic: no `Math.random()` in render paths — use
  a seeded generator or index-derived values.
- Blocks are catalog slugs WITHOUT the `-block` suffix (slug `login-form` →
  file `login-form-block.tsx`).
