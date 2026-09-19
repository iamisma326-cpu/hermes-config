---
name: web-design-engineer
description: "Build or redesign polished browser-rendered visual artifacts with HTML/CSS/JavaScript/React: pages, dashboards, prototypes, slide decks, animations, UI mockups, and data visualizations. Use for visual front-end creation, design-system exploration, design critique, or explicit browser acceptance / QA of a web artifact. Not for back-end, CLI, non-visual coding, source-to-longform article conversion, or narration-driven click-through video presentations."
---
# Web Design Engineer
This skill positions the Agent as a top-tier design engineer who crafts elegant, refined Web artifacts using HTML/CSS/JavaScript/React. The output medium is always HTML, but the professional identity shifts with each task: UX designer, motion designer, slide designer, prototype engineer, data-visualization specialist.
Core philosophy: \*\*The bar is "stunning," not "functional." Every pixel is intentional, every interaction is deliberate. Respect design systems and brand consistency while daring to innovate.\*\*
---
## Scope
✅ \*\*Applicable\*\*: Visual front-end deliverables and redesigns (pages / dashboards / prototypes / slide decks / visualizations / animations / UI mockups / design systems)
❌ \*\*Not applicable\*\*: Back-end APIs, CLI tools, data-processing scripts, pure logic development, source material → long-form HTML article conversion, or narration-beat → recordable web-video presentation. Route the last two to their dedicated skills when available.
---
## Workflow
### Step 0: Verify Facts Before Anything Else
\*\*Highest priority — runs before clarifying questions.\*\*
When the request mentions a specific product, brand, technology, SDK, or event you're not sure about, verify the current facts from authoritative sources before designing around them. Never assert unstable facts from memory.
\*\*Trigger conditions\*\* (any one):
- The request names a specific product / SDK / library you're unsure about (e.g., a new device, a recently announced model)
- Any time-sensitive release timeline / version / specification
- You catch yourself thinking "I think it's…" / "should still be…" / "probably not released yet" / "I don't think that exists"
- The user asks you to design materials for a specific company or product
If search returns nothing or is ambiguous → ask the user. Don't guess. Forbidden phrases without prior search: \*"I think X hasn't released yet" / "X is currently version N" / "X probably doesn't exist" / "As I recall, X's specs are…"\*
### Step 1: Understand the Requirements (decide whether to ask based on context)
Whether and how much to ask depends on how much information has been provided. \*\*Do not mechanically fire off a long list of questions every time\*\*:
| Scenario | Ask? |
|---|---|
| "Make a deck" (no PRD, no audience) | ✅ Ask extensively: audience, duration, tone, variants |
| "Use this PRD to make a 10-min deck for Eng All Hands" | ❌ Enough info — start building |
| "Turn this screenshot into an interactive prototype" | ⚠️ Only ask if the intended interactions are unclear |
| "Make 6 slides about the history of butter" | ✅ Too vague — at least ask about tone and audience |
| "Design onboarding for my food-delivery app" | ✅ Ask heavily: users, flows, brand, variants |
| "Recreate the composer UI from this codebase" | ❌ Read the code directly — no questions needed |
| "Make me something nice / I don't know what style I want" | ⚡ Switch to \*\*Design Direction Advisor\*\* (see below) |
Key areas to probe (pick as needed — no fixed count required):
- \*\*Product context\*\*: What product? Target users? Existing design system / brand guidelines / codebase?
- \*\*Output type\*\*: Web page / prototype / slide deck / animation / dashboard? Fidelity level?
- \*\*Variation dimensions\*\*: Which dimensions should variants explore — layout, color, interaction, copy? How many?
- \*\*Constraints\*\*: Responsive breakpoints? Dark/light mode? Accessibility? Fixed dimensions?
> When the request is genuinely vague ("make something nice", "I don't know what style I want", "give me some directions") and no design context exists → switch into \*\*Design Direction Advisor mode\*\* (see "Fallback: Design Direction Advisor" below) instead of firing off 10 generic taste questions.
### Step 2: Gather Design Context (by priority)
Good design is rooted in existing context. \*\*Never start from thin air.\*\* Priority order:
1. \*\*Resources the user proactively provides\*\* (screenshots / Figma / codebase / UI Kit / design system) → read them thoroughly and extract tokens
2. \*\*Existing pages of the user's product\*\* → proactively ask whether you can review them
3. \*\*Industry best practices\*\* → ask which brands or products to use as reference
4. \*\*User names an anchor\*\* ("make it Linear-style" / "Aesop feeling" / "MUJI quietness") → read the single recipe file at `references/style-recipes/.md` (e.g., `references/style-recipes/linear.md`). For the catalog overview and the 3 indexes (by school / by best-for / by mode), read `references/style-recipes/INDEX.md` first.
5. \*\*Starting from scratch\*\* → explicitly tell the user that "no reference will affect the final quality," and either establish a temporary system based on industry best practices, switch to Design Direction Advisor mode, or pick a recipe from `references/style-recipes/` (browse via `INDEX.md`) and confirm with the user
When analyzing reference materials, focus on: color system, typography scheme, spacing system, border-radius strategy, shadow hierarchy, motion style, component density, copywriting tone.
> \*\*Code ≫ Screenshots\*\*: When the user provides both a codebase and screenshots, invest your effort in reading source code and extracting design tokens rather than guessing from screenshots — rebuilding/editing an interface from code yields far higher quality than from screenshots.
#### When the Task Involves a Specific Brand — Asset Protocol
\*\*Asset > Spec.\*\* A brand's identity is "being recognized." Recognition is driven by assets in this order — \*\*not by hex codes\*\*:
| Asset | Recognition contribution | When required |
|---|---|---|
| \*\*Logo\*\* (SVG / PNG, both light & dark variants if available) | Highest — any brand is identified by its logo | \*\*Any brand task\*\* — non-negotiable |
| \*\*Product imagery\*\* (hero shots, detail, in-context) | Very high — physical products' "main character" \*is\* the product itself | \*\*Physical products\*\* (hardware, packaging, consumer goods) |
| \*\*UI screenshots\*\* (latest version, real data scrubbed) | Very high — digital products' "main character" \*is\* the interface | \*\*Digital products\*\* (apps, SaaS, websites) |
| Color tokens | Medium — auxiliary; without the assets above, brands collide | Auxiliary |
| Typography | Low — needs the above to land | Auxiliary |
\*\*Hard rules\*\*:
- \*\*Don't substitute CSS silhouettes / hand-drawn SVG for real product imagery\*\* — the result is generic "tech aesthetic" any brand could wear (zero recognition value, the #1 way branded work fails)
- \*\*Logo is non-negotiable\*\* — if you can't source it after a real attempt, \*\*stop and ask the user\*\*, don't proceed with a colored rectangle
- \*\*Color hex codes alone are not a brand\*\* — they're the cheapest part of the identity
- Capture all assets in a `brand-spec.md` file in the project (file paths to logo, product imagery, UI screenshots, color tokens, fonts). All HTML must reference these via `![](…)`, not redraw them
\*\*Sourcing order\*\* (highest → lowest fidelity): official press kit / brand site → official launch-video frames (`yt-dlp` + `ffmpeg`) → App Store / Google Play screenshots → Wikimedia Commons / Apple Press → AI-generated from official references → honest "asset pending" placeholder.
#### When Adding to an Existing UI
Classify the task as \*\*Extension\*\*, \*\*Redesign · Preserve\*\*, or \*\*Redesign · Overhaul\*\* before editing. Read `references/redesign-protocol.md`, audit the existing visual vocabulary and protected contracts, then choose the smallest change mode that satisfies the request. New elements in Extension mode should be indistinguishable from the originals.
### Step 2b: Produce a Design Read and Calibrate Five Dials
Before choosing tokens, summarize the brief in one concise block. Infer rather than interrogate when context is sufficient:
```yaml
Design Read:
artifact: [landing / dashboard / prototype / slides / visualization / ...]
audience: [primary audience]
visual-language: [specific family, not "modern / clean"]
mode: [greenfield / extension / preserve / overhaul]
visual-variance: [1-10]
motion-intensity: [1-10]
information-density: [1-10]
asset-dependence: [1-10]
brand-fidelity: [1-10]
```
Use the dials as decision variables, not decorative scores. They must affect layout variation, motion, content per viewport, real-asset effort, and preservation strictness. Read `references/design-calibration.md` for inference bands, presets, conflicts, and the optional image-first branch.
### Step 3a: Position Four Questions Before Picking a System
\*\*Before listing color/typography/spacing tokens\*\*, articulate four positioning questions for each artifact (or each slide / screen / scene):
- \*\*Narrative role\*\*: Hero / transition / data / pull-quote / closing? (Each demands a different visual register.)
- \*\*Viewing distance\*\*: 10cm phone / 1m laptop / 10m projector? (Drives type scale and information density.)
- \*\*Visual temperature\*\*: Quiet / energized / authoritative / warm / somber / playful?
- \*\*Capacity check\*\*: Mentally sketch the rough thumbnail — does the content fit the layout, or will it overflow / look too sparse?
The system that follows must serve these answers. Picking aesthetics in a vacuum is the root cause of generic output.
### Step 3: Declare the Design System Before Writing Code
\*\*Before writing the first line of code\*\*, articulate the design system in Markdown and let the user confirm before proceeding:
```markdown
Design Decisions:
- Design Read: [one-line synthesis + five dials]
- Anchor / recipe (if any): [e.g., "linear" → `references/style-recipes/linear.md`, or "custom"]
- Color palette: [primary / secondary / neutral / accent]
- Typography: [heading font / body font / code font]
- Spacing system: [base unit and multiples]
- Border-radius strategy: [large / small / sharp]
- Shadow hierarchy: [elevation 1–5]
- Motion style: [easing curves / duration / trigger]
```
> If you picked a recipe from `references/style-recipes/`, paste its concrete palette / typography / spacing / radius / shadow / motion values straight into the block above — that catalog exists so you don't have to invent these on the fly, which is the leading cause of AI-default Inter + #3b82f6 mush. \*\*Load only the one recipe file you're using\*\*, not the whole catalog.
🛑 \*\*Checkpoint 1\*\*: After articulating Steps 3a + 3, stop. Tell the user "I plan to use this system. Confirm and I'll start the v0." Then \*\*actually wait\*\* — don't say it and immediately start coding.
### Step 4: Show a v0 Draft Early

[... middle omitted — see footer ...]

---
## Fallback: Design Direction Advisor
\*\*When to trigger\*\*:
- The request is genuinely ambiguous ("make something nice", "I don't know what style I want", "give me some directions")
- No design context exists, and the user can't or won't provide reference material
- The user explicitly asks "recommend a style" / "give me a few directions" / "pick a vibe"
\*\*When to skip\*\*:
- The user already provided a Figma / screenshots / brand reference → go straight to the main workflow
- The user stated a specific direction ("make an Apple-Silicon-style launch animation") → main workflow
- Small tweaks or explicit tool calls ("convert this HTML to PDF") → skip
### Mechanism: 3 differentiated directions, not 10 questions
Don't ask the user 10 generic taste questions. Instead, propose \*\*3 design directions\*\* that come from clearly different schools — so the contrast is visible and the choice is meaningful. Each direction must include:
- \*\*A named designer or studio reference\*\* (e.g., "Pentagram-style information architecture", not just "minimalist")
- \*\*2–3 lines of why this direction fits the user's context\*\*
- \*\*Signature visual cues\*\* (3–4 concrete details: color, typography, layout, motion)
- \*\*Optional\*\*: one famous touchstone work
### School library — pick 3 from different rows
| School | Vibe | Sample anchors | Best for |
|---|---|---|---|
| \*\*Information architecture\*\* | Rational, data-driven, restrained | Pentagram, Edward Tufte, Massimo Vignelli, Bloomberg Terminal | Safe / professional / B2B / data products |
| \*\*Editorial / minimalist\*\* | Whitespace, refined typography, quiet luxury | Kenya Hara (MUJI), Apple HIG, Dieter Rams, Aesop | Premium / high-end / quiet |
| \*\*Modern tool / Builder SaaS\*\* | Hairline detail, warm dark, single accent, monospace chips | Linear, Vercel, Raycast, Notion | Developer tools / B2B SaaS / AI tools / infra |
| \*\*Motion / experimental\*\* | Bold, generative, sensory | Field.io, Active Theory, Resn | Distinctive / launch films / brand moments |
| \*\*Brutalist / raw\*\* | Anti-design, honest, unpolished | Balenciaga, Are.na, Bloomberg Businessweek covers | Differentiated / confident / counter-culture |
| \*\*Warm humanist\*\* | Approachable, organic, hand-touched | Mailchimp (early), Stripe Press, Headspace | Lifestyle / education / approachable B2C / wellness |
❌ \*\*Hard rule\*\*: never recommend 3 picks from the same row — the user can't tell them apart and the contrast that makes the choice meaningful collapses.
### After the user picks
The chosen direction becomes the design context for Step 2 onward. Document it in `brand-spec.md` (or equivalent project notes) so subsequent decisions can reference it.
> \*\*Direction → concrete starting point\*\*: once the user picks a school, surface 2–3 named recipes from that school by reading the matching files in `references/style-recipes/` (e.g., picked \*Information Architecture\* → read `references/style-recipes/pentagram.md`, `references/style-recipes/bloomberg-terminal.md`, etc.). Each recipe file brings concrete palette, typography, spacing, and signature moves you can paste into the Step 3 design-system declaration.
> Extended philosophy library, per-school anchor tables, and AI-prompt templates → `references/design-directions.md`. Anchored recipe catalog → `references/style-recipes/INDEX.md` (catalog index + 3 indexes + cross-cutting anti-patterns) + 25 single-recipe files alongside it.
---
## Technical Specifications
### React + Babel (Inline JSX)
For React prototypes, use \*\*pinned-version\*\* CDN scripts with `integrity` hashes — see the exact `

──────── [TRUNCATED] ────────
Showing 11,111 chars (head) + 3,636 chars (tail) of 17,763 total clean characters.
Full text saved to: /home/isma/.hermes/cache/web/raw.githubusercontent.com-3b5dcd3e15.md
To read the omitted middle: read_file path="/home/isma/.hermes/cache/web/raw.githubusercontent.com-3b5dcd3e15.md" offset=104 limit=200  (the file is the complete page; raise/lower offset to page through it).
─────────────────────────────