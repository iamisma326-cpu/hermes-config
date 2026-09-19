# Automating logged-in SPA pages over CDP (freeCodeCamp case study)

Validated live in Aug 2026 (Chrome 151, Wayland, Hyprland): drove the
freeCodeCamp "Design a Cafe Menu" workshop from step 70 to 89 and the
"Design a Business Card" lab (41/41 tests) to completion. Everything below
was learned by hitting the failure first.

## Source of truth for page state: the preview iframe

The on-screen editor text is virtualized (only visible lines in
`.view-lines`) and lags behind. The reliable mirror of user code is the
preview `<iframe srcdoc>`:

- JS target: iframe whose `srcdoc` includes a marker of the challenge
  (`'<article'` for HTML, `'<style'` for CSS).
- CSS is inside one of SEVERAL `<style>` tags — grab the one containing a
  known selector (e.g. `.item p`), not the first match of
  `/<style[^>]*>([\s\S]*?)<\/style>/`.
- Regexes must escape the closing slash when embedded in heredocs
  (`<\/style>`), and JS `\n` inside Python heredocs must be written `\\n`.

## Editing Monaco without the model API

freeCodeCamp encapsulates Monaco in React — no global `monaco`, no AMD
`window.require`, so `model.setValue()` is unreachable. Ranked techniques
that actually worked, most-reliable first:

1. **Synthetic paste (best)** — focus the editor's textarea, Ctrl+A to
   select, then dispatch a `ClipboardEvent('paste')` with a `DataTransfer`
   payload. Monaco inserts verbatim, focus-independent, no auto-indent.
   ```js
   (t => {
     const ta = document.querySelector('.monaco-editor textarea');
     const dt = new DataTransfer(); dt.setData('text/plain', t);
     ta.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt,
       bubbles: true, cancelable: true }));
   })("...text...")
   ```
2. **execCommand('insertText')** — works only with genuine keyboard focus.
3. **Input.insertText (CDP)** — worked all session on the cafe-menu pages;
   became unreliable in the split-editor lab page. Always verify the write
   landed (preview srcdoc is the truth) and re-run once on silent failure;
   delayed/duplicated input was observed.
4. **Character-by-character keyDown/text** — last resort; error-prone.
5. DEAD ENDS (do not retry): `Input.insertText` on a not-really-focused
   editor; `document.execCommand` without focus; typing into the WRONG
   editor when two are mounted (verify which editor you hit).

### Multi-line paste corrupts: use single-line CSS

Monaco auto-indents every newline of a pasted/typed multi-line block: each
line lands more indented than the last, braces stop matching, checkers fail.
Two clean fixes (both verified passing):
- Paste CSS as ONE line (CSS is whitespace-insensitive).
- Or paste normal multi-line and run Monaco's doc formatter Shift+Alt+F.

### Split-editor pages (labs): two editors at once

Labs mount index.html + styles.css side-by-side after clicking the second
file tab; then `document.querySelector('.monaco-editor')` may grab the wrong
one. Target by index and click its own `.view-lines` at a point that really
hits it (`document.elementFromPoint` to pick a clickable spot), Ctrl+A
there, and dispatch the paste on THAT editor's textarea.

## freeCodeCamp UI mechanics

- **Two-phase check button**: "Check Your Code" -> on pass, the same button
  becomes "Submit and continue" -> click again. Ctrl+Enter in the editor
  equals clicking Check. Don't abandon the step after one click.
- **Donation popup blocks everything** ("Support us" dialog): JS-click
  "Ask me later" before any editor work. Symptom of it blocking: clicks/keys
  silently no-op, no dialog, no failure text.
- **Instructions vs Code tab (labs)**: top-level tabs are Radix; the Code
  panel must be opened before editors exist.
- **File tabs are Radix roving-tabindex**: JS `.click()` on
  `.monaco-editor-tabs button` does nothing (or, if the tab is already
  active, it COLLAPSES the editor accordion to zero editors!). Working
  switches: (a) invoke the React `onClick` from the button's
  `__reactProps$` fiber key; (b) dispatch
  `new KeyboardEvent('keydown', {key:'ArrowRight', bubbles:true})` on the
  active tab; (c) **reload the page** — fCC re-mounts the editor of the
  last-active file tab. Rule: after any tab switch, RELOAD for a clean
  single-editor mount; then confirm which file is mounted by content
  (CSS: contains `.item p` or `body {`; HTML: contains `<!DOCTYPE`).
- **SPA staleness after submit**: URL may advance (step-71) while title and
  instruction text still show the old step; a failed-looking check without
  any failure text means nothing ran. Reload before reading the next step's
  instructions; wait for editor + preview before acting.

## Hyprland/Wayland specifics for these pages

- cua-driver window discovery is workspace-scoped: Chrome on another
  workspace is invisible to capture/list/focus.
- The user's real Chrome is `/opt/google/chrome/chrome`, class
  `google-chrome`; ground truth is `hyprctl clients -j`.
- New Hyprland Lua API: `hyprctl dispatch <name> <args>` evaluates as Lua
  (`hl.dsp.*`); `hyprctl eval "<lua>"` prints only "ok", so write output to
  a file and cat it. Programmatic focus attempts were unreliable live;
  asking the user to switch/focus worked. Tirith blocks `hyprctl | python3`
  pipes and socat to the raw socket — avoid them.
- `document.hasFocus() === false` (Chrome window behind others) is why
  clipboard paste / raw keys do nothing; JS/DOM routes still work. Focus the
  Chrome window or use the focus-free synthetic-paste route.
- fCC publishes each challenge seed inside the running app, not in the
  static HTML — `__NEXT_DATA__` is absent on challenge pages; don't waste
  time fetching the seed by URL, reconstruct state from the preview srcdoc.

## Session artifacts to recreate

- `~/.chrome-agent/` — the agent Chrome profile dir + venv (websocket-client)
  + `cdp.py`/`fcc.py` helpers. See SKILL.md for the profile-copy recipe.