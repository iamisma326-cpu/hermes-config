# freeCodeCamp automation notes (session-verified, 2026-08)

All of this was learned live against `freecodecamp.org/learn/responsive-web-design-v9/` using CDP on the user's Chrome. Companion to the cdp-chrome-automation umbrella.

## Page anatomy per challenge type

### Lecture ("Theory") pages
- An "Interactive Editor" info modal may appear at top — ignorable.
- 3 multiple-choice questions at the bottom (`.mcq-fieldset`), each option is `label` wrapping `input[type=radio]` (sr-only).
- Flow: click correct option labels → click `Check your answer` → repeat until 0 incorrect → click `Submit and go to next challenge`.
- Option texts are EXACT strings including trailing period ("An inline style.").
- If a corrected answer still shows "Incorrect." after re-checking: **re-read the question** — either the answer is genuinely different (fCC quirk: specificity tuples are (inline, id, class, type)) or the page state desynced; `location.reload()` and re-answer is the reliable fix.
- Quiz results appear in `body.innerText` as `Correct!` count and `You have N out of 20 questions correct.`

### Workshop steps (step-N pages)
- Left = instructions (read via `body.innerText`, regex `Step \d+\n\n(...)`), right = Monaco editor(s), bottom = `Check Your Code` button.
- Two file tabs (`.monaco-editor-tabs button`): "index.html Editor" / "styles.css Editor" — accordion behavior, `aria-expanded` attribute.
- Clicking the already-active file tab COLLAPSES the editor (editors count drops to 0) — a broken state that persists until reload.
- Check button flow: `Check Your Code` → on success becomes `Submit and continue` → click again. `Ctrl+Enter` (editor focused) does the check directly.
- On success a `[role=dialog]` appears ("Congratulations... N% complete") with `Submit and go to next challenge` INSIDE the dialog — query `document.querySelector('[role=dialog]')` and click the button scoped to the dialog.
- After advancing, the new step page may render stale content; `location.reload()` then wait 9–12s.

### Workshop steps — robust step loop (session-verified 2026-08-30, Colored Markers)
The reliable per-step loop that advanced ~40 steps in one session:

1. `location.reload()` → sleep 9. This fixes SPA desync AND resets Monaco's corrupted editor state (fCC restores the step seed from its own storage, so a reload yields a clean single-line-able canvas).
2. Read the instruction from `.challenge-instructions` (data-cy="challenge-instructions"); the actionable sentence usually ends with the CSS/HTML to write. Use `body.innerText` fallback if empty.
3. Click the right file tab ONLY if `aria-expanded !== 'true'` (guards against the collapse trap): `[...document.querySelectorAll('.monaco-editor-tabs button')].find(e => e.textContent.includes('<file>'))`.
4. Focus the textarea, **Ctrl+A, then VERIFY selection length is > 0** (see SKILL.md "Selection verification before insert"): `document.execCommand('selectAll'); window.getSelection().toString().length`. Empty selection ⇒ insertText appends ⇒ content duplicates.
5. `Input.insertText` with the FULL content as **one line** (dodges Monaco auto-indent corruption).
6. sleep 5–8 (insertText arrival is lazy; verify BEFORE trusting it).
7. Verify via the **preview iframe**, not the editor textarea: read `iframe.contentDocument.querySelectorAll('style')` cssText (or the DOM for HTML) and assert the LAST rule/property is present. The iframe reflects what fCC's parser actually sees.
8. **Click the `Check Your Code` button — more reliable than Ctrl+Enter** (Ctrl+Enter sometimes leaves the button unchanged with no dialog). sleep ~5; the button may flip to `Submit and continue` a few seconds late — if it's still `Check Your Code`, click it once more before diagnosing a failure.
9. **Donation popup**: after a successful check the "Support us" modal can reappear and block the submit button. Dismiss with a **real mouse click** on "Ask me later" (class `close-button`) — JS `.click()` on it is unreliable and it can instantly reappear; Escape key also closes it. Then find `Submit and continue` again (it's behind the modal; re-query after close).
10. Click `Submit and continue` → sleep 6 → assert URL changed to `step-N+1`.

Notes that bit this session (2026-08-30, steps 38→89):
- **The `fcc_step_set.py` in this skill's scripts/ folder is the corrected, working version** — it uses keyDown Ctrl+A + Backspace + single-line insertText + preview verification. Copy it to `~/.chrome-agent/set_fcc.py` as the drop-in for the step loop.
- **Ctrl+A must be `type='keyDown'` with `key='a'` — NOT `rawKeyDown`.** rawKeyDown pairs are ignored by Monaco's keybinding: Ctrl+A does nothing, insertText appends, content duplicates (len ≈ 2×). The `key()` helper in the corrected script sends keyDown+keyUp with the `key=` field.
- **Even verified selection doesn't guarantee a replace.** Monaco virtualizes its textarea (value can be ~500 chars while the model is ~775+); insertText replaces only the visible portion. The reliable full-replace is: keyDown Ctrl+A → Backspace (empties the WHOLE model) → insertText. Confirm the model emptied via the preview iframe (cssText length drops to just the site's injected `head *{display:none}` style, ~80 chars) before inserting.
- **Stuck "Reset this lesson" dialog**: clicking Reset (`.icon-botton`) opens a confirmation dialog (`h2` "Reset this lesson?" + button "Reset this lesson") that can REFUSE to close via JS `.click()`, fiber onClick, real mouse clicks, or Escape. Don't fight it — **navigate directly to the step URL** (`window.location.href = '.../step-N'`) which closes the dialog and loads a clean seed (preview len ≈ 800, no user edits).
- **Tab-collapse trap is worse than a reload can fix alone**: clicking the already-active file tab collapses BOTH editors (editors=0, textarea absent). Always re-expand via the `aria-expanded !== 'true'` guard after any reload; verify `document.querySelectorAll('.monaco-editor').length === 1` before focusing.
- **After applying CSS, `Check Your Code` may not flip to `Submit and continue`** even with correct content (no dialog, no "Passed" text). A `location.reload()` then re-clicking `Check Your Code` makes the transition register. This happened on step 87/88 — reload is the fix, not re-editing.
- Verify **by preview iframe**, never by `getSelection()` alone — the editor textarea view is virtualized and can show stale/duplicated text while the model is fine (or vice versa).
- Duplicated content (len ≈ 2× expected, braces unbalanced) means the select-all failed; the reliable fix is reload (step 1) then a clean single-line insert, or the in-page `Reset` button (`.icon-botton` with "Reset" text) to restore the seed.
- `balanced` brace check (`s.split('{').length === s.split('}').length`) is a good CSS sanity check but gives false negatives on HTML (the `<!DOCTYPE>` declaration) — for HTML check the preview DOM instead.
- The fCC tests parse the rendered DOM/CSS, so cosmetic whitespace corruption from Monaco never fails a test; only the actual rule/DOM must be right.

### Labs (project pages)
- Tab bar has an extra `Instructions` tab (Radix UI `[role=tab]`). Radix tabs ignore JS `.click()`; they respond to: real CDP mouse click at element coords, or ArrowRight `KeyboardEvent` dispatched on the currently-selected tab.
- File tabs inside Code view are React accordion buttons — use fiber onClick (`__reactProps$` → `onClick({})`); double-expanding gives split view with BOTH editors mounted.
- **Dual-editor targeting: `document.querySelector('.monaco-editor textarea')` grabs editor index 0 — which may be the WRONG file.** With both tabs expanded (indexes 0=html, 1=css — verify content, don't assume), write each file via `document.querySelectorAll('.monaco-editor textarea')[i]` + focus + Ctrl+A(keyDown) + Backspace + single-line `Input.insertText`. Session bug 2026-08-30 (Colored Boxes lab): the single-editor `fcc_step_set.py` wrote CSS into the HTML editor, and the preview iframe rendered the CSS as visible text in `<body>` — read `preview iframe` content to catch this.
- **Preview injects user CSS inline**: the preview iframe inlines `styles.css` content into `<style>` tags and drops/ignores the `<link rel="stylesheet">` tag — a `link`-presence check in the preview is a red herring; verify the actual computed styles / rule text instead (e.g. `getComputedStyle(document.body).backgroundColor`).
- Lab tests: click `Check Your Code` → results render as `Passed:` lines in the page body (no dialog) → button flips to `Submit and continue` → click → back to course map (`/#lab-...`).
- To verify work: read the preview iframe `srcdoc` (contains the merged HTML + user CSS inlined in `<style>` tags). fCC auto-saves; after reload the last-active file editor remounts with saved content.

### Reviews ("Review" pages)
- Long reference text + a checkbox assignment (label with inner `input`) + `Submit` button.
- Flow: click checkbox → Submit → dialog → `Submit and go to next challenge`.

### Final quizzes (20 questions)
- Structure: `.quiz-question-label` + 4 `.quiz-answer-label` (each inside `div[role=radio]` headlessui radiogroup option, `aria-checked`).
- **Option click: use REAL CDP mouse clicks, not fiber onClick** (session-verified 2026-08-30, CSS Colors quiz): fiber onClick with a fake event fires without error but leaves `aria-checked='false'` on all 20 options (0/20 marked). The working method: `div.scrollIntoView({block:'center'})` → read `getBoundingClientRect()` center → `Input.dispatchMouseEvent` press+release → verify `aria-checked === 'true'` after a short sleep. Quiz pages are tall; without scrollIntoView the option rects are off-viewport (negative y).
- Group answers by iterating DOM order: `.quiz-question-label, .quiz-answer-label` and splitting into groups on each question label.
- Passing threshold 18/20. Flow: answer all 20 → `Finish the quiz` → confirm dialog `Yes, I am finished` → score shown (`You have N out of 20 questions correct`) → `Submit and go to next challenge` — note the button text is "next challenge" (not "next"), and after submit the map shows the module's remaining steps.
- The finish dialog lists unanswered question numbers if any — re-answer those by group index and retry.
- Known-good quiz answers for completed modules are NOT reusable (content varies), but the answering MACHINERY (scrollIntoView + real click) is reusable.

### Styling Forms session (2026-08-31) — quiz/review gotchas that refine the above

- **HeadlessUI quiz option marking is NOT consistently "real clicks"**: on the v9 Styling Forms quiz, real CDP mouse clicks at option coords left `aria-checked='false'` (only 1/40), while **plain JS `div[role=radio].click()` from page context marked all 10/10**. The Colors quiz (earlier) wanted real clicks. Rule: try JS `.click()` on the radio div first; if `aria-checked` stays false after a sleep, fall back to real CDP clicks (scrollIntoView + dispatchMouseEvent). Verify by counting `[role=radio][aria-checked="true"]`.
- **Quiz flow that worked**: answer all → plain JS click `Finish the quiz` → plain JS click `Yes, I am finished` in the confirm dialog → **"Submit and go to next challenge" ignored JS `.click()`** → **Ctrl+Enter** (Input.dispatchKeyEvent keyDown Control → keyDown Enter with modifiers=2 → keyUp Enter → keyUp Control) navigated to the map (`/#quiz-styling-forms`). Module counter went 80→81.
- **Review checkbox is React-controlled**: the native setter + input/change events does NOT stick (checkbox flips back). The working toggle is **`label.click()` on the `.video-quiz-option-label`** (the label carries React's onClick; a trailing `cb.click()` on the input undoes the mark). Then plain JS click `Submit` → `Submit and go to next challenge` appears → JS click navigates to map (`/#review-styling-forms`). Counter 81→82.
- **CSS corruption signature `& body {`: autosave merged rules as SCSS-style nesting** (`input[type="submit"] { ...\n  & body { ... }`) — computed styles show stale values (margin 10px instead of 0 auto) and the test stays on "Check Your Code". Fix: `location.reload()` restores the clean step seed, then reapply the full CSS in one line; verify via preview iframe styleSheets (cssLen), not the textarea.
- **Review/Quiz blocks are `<a>` anchors, not `<button>`**: after clicking a module header, the visible button list may omit Review/Quiz — search ALL `a, button` for the block name (or `/review|quiz/i`) and read the `href` (`review-styling-forms/...`, `quiz-styling-forms/...`). Direct navigation to those slugs works even when the review shows "Not started".
- **Module counter deltas**: workshops advance it per step; the module's review (+1) and quiz (+1) register on the map after their flows complete. A "Passed...Completed" tag on the block confirms it.

## Answering strategy that worked
- Extract all question+option text in one eval (`body.innerText` slice from `1.`), decide answers reading the whole set, write them to a file (one per line, exact option text), then a loop script clicks each via fiber and verifies aria-checked, then finish.
- Watch for commas inside options (e.g. `(0, 0, 1, 0)`) — use `|` as answer-file separator or line-per-answer.
- Duplicate option texts across different questions exist — always resolve options WITHIN the question group, never document-wide.

## Course map navigation (v9)
- The map `/learn/responsive-web-design-v9/` lists modules with "X of Y steps complete". Each module header is a BUTTON that expands on click to reveal its lab/review/quiz links — query those `a[href*="/learn/"]` anchors AFTER clicking the module header button. Direct `window.location.href` to a guessed block slug often lands on fCC's "Page not found" quote page (e.g. `learn-css-colors-...` does NOT exist); the safe path is: read anchor hrefs from the map, never guess.
- A module's step-progress counter ("98 of 98 steps complete") is the ground truth for whether a module is finished — verify it before moving on. "Not Passed" + "Not started" tags appear on incomplete items.
- Labs/reviews/quizzes have deterministic slugs you can read off the expanded map (`lab-contact-form/design-a-contact-form`, `review-styling-forms/...`, `quiz-styling-forms/...`).
- After finishing a block, `Submit and go to next challenge` returns to the map (URL `/#<block-id>`), not to the next step — so drive module transitions from the map, not by URL guessing.

## Session state (2026-09-01)

- Certificate: Responsive Web Design v9.
- Completed: HTML (302/302), Computers (16/16), Basic CSS (122/122), Design (23/23), Absolute and Relative Units (8/8), Pseudo Classes and Elements (74/74), Colors (98/98).
- **Styling Forms: 84/84 COMPLETED** (Best Practices lectures 3/3 + Registration Form workshop 61/61 + Game Settings Panel workshop 16/16 + Lab Contact Form + Lab Feature Selection Page + Review + Quiz 10/10).
- **The Box Model: 54/54 COMPLETED** (7 lectures + Rothko Painting workshop 44 steps + Lab Confidential Email Page + CSS Layouts and Effects Review + CSS Layout and Effects Quiz 20/20). Note: Rothko step 9 had to be re-done after the module showed 53/54 — a step can pass its check yet fail to register on the map; re-navigate and redo.
- **Flexbox: in progress (~46/70)** — 2 lectures completed, Photo Gallery workshop 22/22 COMPLETED, Colorful Boxes workshop 24 steps (all approved up to `align-content: start`). Remaining: Lab "Design a Pricing Plans Layout Page", CSS Flexbox Review, CSS Flexbox Quiz.
- Next modules: Typography (78), Accessibility (72), Positioning (88), Attribute Selectors (71), Responsive Design (37), plus certification blocks.
- Lab answers kept for reference (don't reuse blindly — fCC accepts variants):
  - Confidential Email lab (Box Model): `#email { padding: 50px; margin-top: 50px; width: 500px; border: 2px solid black; box-sizing: border-box; } #confidential, #top-secret { display: inline-block; padding: 10px; margin-left: 10px; border: 1px solid black; }` + rotate transforms + `.blurred { filter: blur(3px); }`; HTML: main#email with the two divs, 3+ paragraphs each with a span.blurred.
  - Business card: name "Carlos Campos", designation "Web Developer", company "Campus Dev", body bg rosybrown.
- Lab answers used (kept for reference, don't reuse blindly — fCC accepts variants):
  - Business card: name "Carlos Campos", designation "Web Developer", company "Campus Dev", body bg rosybrown.
  - To-do list: 4 items task1..task4 with sub-item links to example.com; link pseudo-classes :link darkblue, :visited purple, :hover orange, :active red, :focus teal outline.
  - Blog post card: post-img full width + border-bottom, .read-more inline-block navy button with :hover royalblue.
  - Colored boxes lab (Colors): body bg #f4f4f4; .color-grid flex gap 10px centered; .color-box 100x100; .color1 hex #ff0000, .color2 rgb(0,255,0), .color3 blue, .color4 hsl(240,100%,50%), .color5 purple. HTML: `<link rel="stylesheet" href="styles.css">` + 5 divs `class="color-box colorN"` inside `.color-grid`.
