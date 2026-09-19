---
name: didactic-code-commenting
description: "Use when commenting student code line-by-line for study."
---

# Didactic code commenting (coursework)

The user (student) wants his own code explained in comments so the file doubles as study material for his course. Apply his style EXACTLY — he corrects deviations.

## Style rules (user-corrected, non-negotiable)

1. Comments in Spanish, brief, one per line of code (above the line or inline at the end).
2. **EXPLAIN ONCE**: the FIRST occurrence of a concept gets the full explanation (e.g. the whole `var x by remember { mutableStateOf(value="") }` pattern broken down word by word). Every later occurrence gets only a short tag: `// DNI del cliente`, `// Etiqueta DNI`, `// Caja editable del X (mismo patrón)`. Repeating the same explanation verbatim is redundant — he explicitly asked to strip the duplicates.
3. **No semicolons in comment prose** — use commas: `// Button: botón táctil, entre sus { } va lo que muestra`.
4. Chained modifier calls each get their own short comment (`.fillMaxSize()`, `.background()`, `.padding()`) — he noticed a missing one.
5. **Imports: ONE collective block comment, not per-line comments.** When a key pattern depends on specific imports (e.g. Compose state needs `Composable`/`getValue`/`setValue`/`mutableStateOf`/`remember`), list only those, each with a one-liner.
6. Annotate closing braces with what they close: `} // cierra la Column`.
7. **Do not alter code logic — comments only.** Prefer `patch`. If a full-file rewrite is unavoidable (mass commenting), re-read the file after writing and check no code line — especially the import block — was dropped, then compile.
8. Keep his existing comments and voice (`// llama la funcion que crea la interfaz`); merge, don't rewrite.

## Study-guide .txt (when asked for a "guía")

Format: (a) brief plain-words intro of the toolchain (what Android Studio is, what Kotlin is — no jargon dumps), (b) the full commented code with the import section condensed per rule 5, (c) **NO conclusion section**. Plain text — it's a .txt, no markdown rendering.

## Pitfalls

- A full rewrite to inject comments once dropped the entire import block — caught only because the follow-up re-read showed it. Always re-read + compile after any rewrite.
- Commenting passes are the only change: run the project build after each pass and report the real result.

## Verification

Compile after every commenting pass (`bash gradlew :app:compileDebugKotlin --console=plain`) and report the actual `BUILD SUCCESSFUL` output. Zero diffs in code lines (verify by re-reading the file).

See `references/compose-glossary-es.md` for the Spanish Compose/Kotlin explanations already approved by this user — reuse those phrasings when commenting his Android coursework.
