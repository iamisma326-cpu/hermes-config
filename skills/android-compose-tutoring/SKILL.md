---
name: android-compose-tutoring
version: 1.0.0
author: isma
license: MIT
description: Use when tutoring/pairing on Android Compose learning apps.
metadata:
  hermes:
    tags: [android, kotlin, jetpack-compose, tutoring, code-review]
    related_skills: []
---

# Android Compose Tutoring (modo tutor)

## When to Use

The user is a student building a small Android app to LEARN (first signals:
they ask what `var`, `remember` or `Modifier` mean, ask you to comment their
code line by line, or ask "¿cómo sería X?" before wanting it implemented).
Currently `~/projects/Desktop/belleza1` (package `com.example.appservicios`).
NOT for professional Android work where shipping quality is the goal and
extra fixes are welcome.

Pairing sessions where the user is LEARNING Android development and builds a
small app incrementally (currently `~/projects/Desktop/belleza1`, package
`com.example.appservicios`). The user is the student: the goal is that THEY
understand the code, not just that the app works.

## Core workflow

1. **Explain first, implement on signal.** When a feature or fix comes up, the
   user asks "cómo sería" — present the approach (options, trade-offs, a code
   sketch) and STOP. Only edit code when they explicitly say to ("corrige X",
   "hazlo así"). Never implement while still explaining.
2. **No extra changes.** Touch ONLY what was asked. If you spot other defects
   (wrong label, unused imports, bad indentation), list them as numbered
   findings with `path:line` and let the user pick. Fixing unasked things in a
   learning project destroys their authorship trail.
3. **Audit requests are read-only.** "¿qué falta / qué está mal / qué más
   haría?" → read the file(s), report a numbered list with line references,
   ordered by impact, and make zero edits.
4. **Verify after every edit.** From the project root run
   `bash gradlew :app:compileDebugKotlin --console=plain` (the wrapper lacks
   +x; invoke it through bash) and report the BUILD SUCCESSFUL line. Never
   claim an edit is done without a passing compile.
5. **Reply in Spanish.** Code identifiers, API names and build output stay in
   English.

## Line-comment conventions (when the user asks to comment the code)

- Spanish, one brief comment per line/block, written at beginner level (they
  asked what `var`, `by remember`, `mutableStateOf`, `it`, `.dp`, `.sp` and
  `Modifier` are).
- **Explain each concept ONCE, at its first occurrence** — the full
  word-by-word breakdown goes on the first instance only (state pattern,
  Modifier chain, Text/TextField parameters, `onValueChange`/`it`, dp vs sp).
  Every later occurrence gets a short label only: `// Etiqueta DNI`,
  `// Caja editable (mismo patrón)`. The user explicitly rejected repeated
  explanations as redundant.
- **Commas, never semicolons**, inside Spanish comments.
- Keep the user's own comments and their (irregular) indentation — do not
  reformat, reorder or "improve" their code; comments only. Do not comment
  imports ("no cuentes los imports").
- After commenting, re-compile and confirm the build still passes.

## References

- `references/belleza1-polleria.md` — current state, agreed plan and pending
  items for the pollería order-form app.
