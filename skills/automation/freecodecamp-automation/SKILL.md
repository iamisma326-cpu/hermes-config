---
name: freecodecamp-automation
description: Automate freeCodeCamp RWD v9 curriculum via Chrome CDP.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [freecodecamp, chrome, cdp, automation, education]
    related_skills: [cdp-chrome-automation, linux-desktop-automation]
---

# freeCodeCamp CDP Automation

Drive Chrome via CDP (`~/.chrome-agent/` scripts) to complete fCC RWD v9 challenges autonomously.

## When to Use

- Navigating freeCodeCamp interactive lessons, workshops, labs, reviews, or quizzes
- Automating Monaco editor content insertion via CDP
- Submitting HeadlessUI-powered quizzes or reviews
- Recovering from CSS corruption or focus-stealing donation popups

## Prerequisites

- Chrome profile at `~/.chrome-agent/` with fCC logged in
- CDP on port 9222: `/opt/google/chrome/chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-agent --no-first-run --no-default-browser-check --ozone-platform=wayland <URL>`
- Scripts: `~/.chrome-agent/cdp.py`, `~/.chrome-agent/set_fcc.py`, `~/.chrome-agent/quiz2.py`, `~/.chrome-agent/lecture_quiz.py`
- Step-through helpers (created 2026-08-31, used for the 68-step Nutritional Label workshop): `~/.chrome-agent/fcc_step.py` and `~/.chrome-agent/fcc_next.py`
- Multi-file lab helper (created 2026-09-06, uses React fiber + model.setValue): `~/.chrome-agent/set_lab.py`
- venv: `~/.chrome-agent/venv/bin/python`

## Navigation

```python
from cdp import CDP, get_tab
def evc(c, js):
    r = c.cmd('Runtime.evaluate', expression=js, returnByValue=True, awaitPromise=True, timeout=20000)
    return r.get('result', {}).get('value')
tab = get_tab('freecodecamp')
c = CDP(tab['webSocketDebuggerUrl'])
```

Navigate with `location.href = '...'` + `time.sleep(12)` then `location.reload()` + `time.sleep(10)`.

After each step submit: click "Submit and continue", sleep 8s, print URL, `location.reload()`, sleep 10s, read instruction.

## Workshop Step-Through Loop (Long Workshops)

For multi-file workshops with many steps (e.g. Nutritional Label = 68 steps, Colorful Boxes = 43), run the loop with the two helper scripts instead of hand-typing the full CDP sequence every step. This session verified ~45 consecutive steps of the Nutritional Label workshop with this loop (2026-08-31).

```bash
# Each iteration:
# 1. Advance to the next step, close popups, reload, print URL + instruction
~/.chrome-agent/venv/bin/python ~/.chrome-agent/fcc_next.py
# 2. Apply the full HTML or CSS for the CURRENT step
~/.chrome-agent/venv/bin/python ~/.chrome-agent/fcc_step.py html '<!DOCTYPE html>...'   # or css '...'
```

Key properties of the helpers (read them before editing):
- `fcc_step.py` takes `html|css` + the FULL file content, closes donation modal up to 3× (falls back to `modal.remove()`), collapses the OTHER tab so only ONE editor is visible, expands the target tab, Ctrl+A → Backspace → insertText, clicks "Check Your Code", and prints `SUBMIT-VISIBLE` (pass) or `checking` (fail/not-yet).
- `fcc_next.py` closes the donation modal, clicks "Submit and continue", reloads, and prints the URL + instruction text.
- Always write the FULL file (index.html or styles.css) each step — the helper replaces the whole model, so a partial edit would clobber prior steps. Reconstruct the full content from the accumulated step history.

**Pitfall — apply the whole file, not just the diff.** Each step builds on the previous; the helper does a full-model replace. Keep the accumulated HTML/CSS up to date as you go, or re-navigate to the step URL (fresh seed) and reapply the full content.

**Style rule — never ask "shall I continue?"** The user expects autonomous progress. When running a multi-step workshop, execute each step and advance to the next without pausing for confirmation. Only stop if a test actually fails and requires diagnosis — resume immediately after fixing. This applies to all fCC automation tasks.

**Pitfall — "checking" status means the test DID NOT pass, not "still running".** When `STATUS: checking` prints, one of these is true: (a) the CSS/HTML content is correct but the editor got corrupted by deep indentation (Monaco autosave bug), (b) the content has an error the test rejects, or (c) the page is in a read-only review state. Diagnosis:
1. Check the preview iframe: if computed styles/HTML look correct, it's likely (a) — navigate directly to the step URL (`Page.navigate`) for a clean seed and reapply BOTH files (HTML + CSS). Do NOT use `location.reload()` — it restores the corrupted autosave.
2. If the preview is wrong, re-check the CSS/HTML content against the instruction.
3. Check for a `"You have N out of 20"` message — you're in quiz review state; re-navigate for a fresh quiz.

This recovery pattern was verified repeatedly on the Nutritional Label workshop (steps 28, 31, 32, 34, 36, 37, 65 all recovered this way) and the Flexbox quiz (review state → away-and-back navigation).

## Monaco Editor: Single-File (Workshop Steps)

Use `set_fcc.py` for single-file workshops (index.html or styles.css only):

```
~/.chrome-agent/venv/bin/python ~/.chrome-agent/set_fcc.py <filename> '<single-line-content>'
```

The script: reloads → expands target tab → Ctrl+A → execCommand('selectAll') → Backspace → insertText → verifies.

**Pitfall**: `set_fcc.py` targets the FIRST `.monaco-editor textarea`. In multi-file labs (both tabs expanded), it writes to the WRONG editor. Use the multi-file approach below.

**Pitfall — the reliable full-replace pattern for large CSS models.** When the CSS model grows past ~500 chars, Monaco's textarea becomes virtualized (textarea.value shows only a viewport slice, not the full model). `setSelectionRange(0, len)` + dispatch `select` event does NOT reliably select the full model. The verified sequence:

1. Close donation modal first (see above). Always diagnose with `elementFromPoint` before assuming the editor is broken (see Donation Popup section).
2. Collapse the other tab, expand the target tab — only ONE editor visible.
3. Focus textarea, verify `document.activeElement.tagName === 'TEXTAREA'`. If it returns `BODY` or `BUTTON`, a popup/modal overlay is covering the editor — see the Donation Popup section.
4. Ctrl+A via keyDown (NOT rawKeyDown): `Input.dispatchKeyEvent(type='keyDown', modifiers=2, windowsVirtualKeyCode=65, code='KeyA', key='a')` — Monaco intercepts this as native select-all of the FULL model.
5. Verify selection via `execCommand('selectAll'); window.getSelection().toString().length` — should return the full model size (e.g. 771 chars). If length is 0, the editor wasn't actually focused — retry step 3.
6. **Backspace key event** to empty the model: `Input.dispatchKeyEvent(type='keyDown', windowsVirtualKeyCode=8, key='Backspace', code='Backspace', modifiers=0)`. Sleep 2–3s.
7. **Verify model is truly empty**: `ta.value.length === 0` (or check preview iframe — only ~80 chars of injected site styles remain). If the backspace didn't empty (length stays > 0), the selection didn't cover the full model — retry from step 4, or use Reset lesson button.
8. `Input.insertText(text=<single-line CSS>)` — replaces the empty model.
9. Verify via preview iframe computed styles, NOT the textarea value.

This was verified across 20+ steps of the Flexbox Photo Gallery and Colorful Boxes workshops (2026-08-31). The backspace step is critical: even with full selection verified, `insertText` alone can still append (Monaco replaces only the virtualized viewport, leaving the rest of the model intact).

## Monaco Editor: Multi-File (Labs with index.html + styles.css)

Labs have TWO files. **Critical discovery (2026-09-06)**: `Input.insertText` with TWO Monaco editors in the DOM **always writes to the FIRST editor** regardless of which tab is expanded or which textarea has focus. The tab-click + insertText approach described below works ONLY when one editor is collapsed (hidden from DOM). When both editors exist simultaneously, you must use the **React fiber + model.setValue()** approach.

### Approach A: Single-editor-at-a-time (collapse the other)

Works when only ONE editor is visible in the DOM. Click the tab, which expands that file's editor and collapses the other:

```python
def write_to_editor(c, fname, text):
    # CRITICAL: check aria-expanded BEFORE clicking — clicking an already-expanded
    # tab COLLAPSES it, leaving NO visible editor!
    r = evc(c, f"""(() => {{
      const el = [...document.querySelectorAll('.monaco-editor-tabs button')]
        .find(e => e.textContent.includes('{fname}'));
      if (!el) return 'no-tab';
      if (el.getAttribute('aria-expanded') !== 'true') {{ el.click(); return 'clicked'; }}
      return 'already-open';
    }})()""")
    time.sleep(3)
    # Verify only ONE editor is visible
    ta = evc(c, """(() => {
      const ta = [...document.querySelectorAll('.monaco-editor textarea')]
        .find(t => t.offsetParent !== null);
      if (ta) { ta.focus(); return 'ok'; }
      return 'no-ta';
    })()""")
    if ta != 'ok': return False
    # Ctrl+A → Backspace → insertText
    key(c, 'KeyA', 65); time.sleep(2)
    key(c, 'Backspace', 8, 0, 'Backspace'); time.sleep(3)
    c.cmd('Input.insertText', text=text); time.sleep(6)
    return True
```

**Pitfall — clicking an already-expanded tab COLLAPSES it.** After a fresh page load, `index.html` is already `aria-expanded="true"`. Clicking it again sets `aria-expanded="false"`, removing the editor textarea from the DOM. `set_fcc.py` correctly checks `aria-expanded` before clicking — always do the same.

### Approach B: React fiber + model.setValue() (RECOMMENDED for multi-file labs)

When both editors exist in the DOM (common after expanding both tabs), `Input.insertText` is unreliable. Instead, access the Monaco editor instances through React's fiber tree and call `model.setValue()` directly on each model. **This was verified on the Newspaper Article lab (2026-09-06) — 30/30 tests passed.**

```python
def set_model_via_fiber(c, container_index, content):
    """Set Monaco model content via React fiber tree. container_index: 0=index.html, 1=styles.css"""
    escaped = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    r = evc(c, f"""(() => {{
      const containers = document.querySelectorAll('.react-monaco-editor-container');
      const container = containers[{container_index}];
      if (!container) return 'no container {container_index}';
      const fiberKey = Object.keys(container).find(k => k.startsWith('__reactFiber'));
      if (!fiberKey) return 'no fiber key';
      let fiber = container[fiberKey];
      let depth = 0;
      let editor = null;
      let current = fiber;
      while (current && depth < 50) {{
        if (current.stateNode && current.stateNode.editor) {{
          editor = current.stateNode.editor;
          break;
        }}
        if (current.memoizedState) {{
          let state = current.memoizedState;
          while (state) {{
            if (state.memoizedState && state.memoizedState.current &&
                typeof state.memoizedState.current === 'object') {{
              const ref = state.memoizedState.current;
              if (ref && typeof ref.getModel === 'function') {{ editor = ref; break; }}
            }}
            state = state.next;
          }}
          if (editor) break;
        }}
        current = current.child || current.sibling || (depth > 0 ? null : fiber.return);
        depth++;
      }}
      if (editor && typeof editor.getModel === 'function') {{
        const model = editor.getModel();
        model.setValue(`{escaped}`);
        return 'set, len=' + model.getValue().length;
      }}
      return 'no editor found';
    }})()""")
    return r
```

Usage:
```python
set_model_via_fiber(c, 0, html_content)   # index.html
set_model_via_fiber(c, 1, css_content)    # styles.css
# Then click "Check Your Code"
```

**Helper script**: `~/.chrome-agent/set_lab.py` implements this approach for both files in one pass (reload → close modal → wait for editors → set both models → check). Usage:
```bash
~/.chrome-agent/venv/bin/python ~/.chrome-agent/set_lab.py '<html>' '<css>'
```

**Pitfall — the fiber key name changes per session.** The key is `__reactFiber$<random>`. Always discover it dynamically with `Object.keys(container).find(k => k.startsWith('__reactFiber'))` — never hardcode the hash.

**Pitfall — container index may not match file order.** After page load, `containers[0]` is typically `index.html` and `containers[1]` is `styles.css`, but verify with `model.uri.toString()` (e.g. `inmemory://model/1` vs `inmemory://model/3`) if uncertain.

Write index.html first, then styles.css. Verify after each write via the preview iframe.

## Quiz: HeadlessUI (no native radio inputs)

fCC quizzes use HeadlessUI with `[role="radio"]` divs, NOT `<input type="radio">`.

### Question-set rotation — CRITICAL GOTCHA

fCC CSS quizzes (especially Flexbox, Typography, Accessibility) have a POOL of questions. Each time you hit the quiz URL, the server selects 20 questions from this pool at random. Furthermore, the **order of answer options within each question also shuffles** between attempts. This means:

- **Never hardcode answer indices** from a previous extraction. The same Q index (`groups[5]`) may be a completely different question on a fresh load.
- **Never rely on option position** (e.g. "index 3 is correct"). The correct answer for "space-between" may be option [3] in one load and [0] in the next.
- **Always extract the current questions right before answering** in the same script that selects them. Do NOT extract questions, then submit (which opens review), then navigate away, come back, and try to reuse the old answers — the set will have rotated.

**Detection**: after the first submit fails with a low score (e.g. 4/20), examine which questions were actually in the REVIEW state. Compare the review's question set to the one you extracted before submission. If they differ, the pool rotated between extraction and submission — you answered a stale set.

**Strategy**: extract questions on each FRESH quiz load (no prior review state), derive correct answers programmatically for that specific set, select with text matching, and submit in ONE script so the set cannot change mid-workflow.

**Pitfall — text-match substring traps.** When matching option text, watch for these patterns:  
  - `"flex-start"` matches `"flex-starts;"` (invalid value) and `"flex-start;"` (valid). Fix: include the trailing delimiter: `"flex-start;"` or `"flex-start "`.  
  - `"flex-wrap: wrap"` matches both `"flex-wrap: wrap;"` and `"flex-wrap: wrap-reverse;"`. Fix: match `"flex-wrap: wrap;"` with the semicolon (or `"wrap-reverse"` to exclude).  
  - `"row"` appears in `"row-reverse"`, `"flex-direction: row"`, and standalone `"row"`. Fix: for plain keyword options, use exact normalized-text equality (`norm(r) === 'row'`). For CSS blocks, include enough context (`"flex-direction: row; flex-wrap: wrap-reverse"`).  
  - `"flex"` matches everything containing the word "flex". Never substring-match short generic terms.
- **Apostrophe in answer text breaks JS single-quoted strings.** When embedding answer text into a JS template via Python f-string, an apostrophe/quote (e.g. `container's`) closes the string prematurely. Fix: use `json.dumps(substr)` to safely embed the substring into the JS expression:
  ```python
  import json
  substr = "to the beginning of the container's main axis"
  evc(c, f"""(() => {{
    const match = labels.find(l => l.textContent.includes({json.dumps(substr)}));
    ...
  }})()""")
  ```

### Review state is read-only

When you submit a quiz and get fewer than the passing threshold, the page transitions to a **review** state. The radios become **read-only** (no selection change, no dialog). Detecting this state:

- The page shows a message like `"You have 12 out of 20 questions correct."`  
- Radios show `aria-checked="true"` but clicking them has no effect  
- `"Finish the quiz"` button is visible but clicking it does nothing  

**Fix**: navigate to the course map first, then back to the quiz URL (forces a fresh editable load). Do NOT use location.reload() on the review page — fCC autosave restores the review state. Navigate away-and-back:

```python
c.cmd('Page.navigate', url='https://www.freecodecamp.org/learn/responsive-web-design-v9/')
time.sleep(12)
c.cmd('Page.navigate', url='https://www.freecodecamp.org/learn/responsive-web-design-v9/quiz-css-flexbox/quiz-css-flexbox')
time.sleep(14)
```

This clears the persisted review state and gives you a fresh quiz with a potentially different question set — extract and answer from scratch.

### Extracting which answers were wrong (17/20 → 20/20 path)

When the score is below the pass threshold but close (e.g. "You have 17 out of 20 questions correct." — pass = 18/20 for Flexbox), the review state marks the wrong options inline. Extract them to fix only what's needed instead of re-deriving all 20:

```python
st = evc(c, """(() => {
  const groups = [...document.querySelectorAll('[role="radiogroup"]')];
  const labels = [...document.querySelectorAll('label')];
  const wrong = [];
  groups.forEach((g, i) => {
    const label = labels.find(l => l.closest('[role="radiogroup"]') === g && /^\\d+\\./.test(l.textContent.trim()));
    const q = label ? label.textContent.trim().replace(/\\s+/g,' ').slice(0,110) : '?';
    const opts = [...g.querySelectorAll('[role="radio"]')].map(r => {
      const t = r.textContent.trim().replace(/\\s+/g,' ');
      const sel = r.getAttribute('aria-checked') === 'true';
      // "Incorrect" is a sibling/parent marker; check nearby text of the checked option
      const inc = sel && r.parentElement.textContent.match(/Incorrect/i);
      return {t: t.slice(0,80), sel, inc: !!inc};
    });
    const checked = opts.find(o => o.sel);
    if (checked && checked.inc) wrong.push({q, checked: checked.t});
  });
  return JSON.stringify(wrong);
})()""")
```

The wrong questions come back with the question text and the WRONG option that was selected; the correct answer is one of the other options in that group. Correct those groups, then navigate away-and-back for a fresh editable quiz, re-select ALL 20 (set may have rotated), and re-submit.

**Pitfall — 17/20 is still a FAIL.** The pass threshold is 18/20 (fCC states it on the quiz page: "To pass the quiz, you must correctly answer at least 18 of the 20 questions"). Do not submit once — verify the score message says "20 out of 20" or "18+" before relying on it.

### Batch selection pattern

Instead of one text-search per question (slow, error-prone for text-matching pitfalls), extract all 20 questions + their options in a single query, then derive correct answers and select them:

```python
# Step 1: Extract all questions and options
st = evc(c, \"\"\"(() => {
  const groups = [...document.querySelectorAll('[role=\"radiogroup\"]')];
  const labels = [...document.querySelectorAll('label')];
  return JSON.stringify(groups.map((g, i) => {
    const label = labels.find(l => l.closest('[role=\"radiogroup\"]') === g && /^\\\\d+\\\\./.test(l.textContent.trim()));
    const q = label ? label.textContent.trim().replace(/\\\\s+/g,' ') : '?';
    const opts = [...g.querySelectorAll('[role=\"radio\"]')].map(r => r.textContent.trim().replace(/\\\\s+/g,' '));
    return {q, opts};
  }));
})()\"\"\")
```

Step 2: Read the JSON, determine correct answer for each question programmatically (or by hardcoded mapping based on the extracted question text).

Step 3: For each answer, find the radio whose normalized text matches your answer. For short keywords use exact equality; for CSS blocks use `.includes()` on the normalized text with enough context to be unique.

Step 4: Verify the total (`selected === 20`) before submitting.

**Selecting an option**: find the label containing the answer text, climb to the `[role="radio"]` div, call `.click()`:

```python
evc(c, f"""(() => {{
  const labels = [...document.querySelectorAll('label')].filter(l => l.offsetParent !== null);
  const match = labels.find(l => l.textContent.includes('{answer_fragment}'));
  const opt = match ? (match.closest('[role="radio"]') || match.parentElement) : null;
  if (opt) {{ opt.scrollIntoView({{block: 'center'}}); opt.click(); }}
}})()""")
```

**Submitting**: "Finish the quiz" → "Yes, I am finished" → Ctrl+Enter (not button click):

```python
# Step 1: "Finish the quiz" — dispatchEvent with a real MouseEvent WORKS (verified 2026-08-31)
evc(c, """(() => {
  const b = [...document.querySelectorAll('button')].find(x => /Finish the quiz/i.test(x.textContent));
  if (b) { b.scrollIntoView({block: 'center'}); b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return 'clicked'; }
  return 'no';
})()""")
time.sleep(5)

# Step 2: "Yes, I am finished" — same dispatchEvent pattern
evc(c, """(() => {
  const b = [...document.querySelectorAll('button')].find(x => /Yes, I am finished/i.test(x.textContent));
  if (b) { b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return 'clicked'; }
  return 'no';
})()""")
time.sleep(7)

# Step 3: check score message, then navigate via Ctrl+Enter on "Submit and go to next challenge"
c.cmd('Input.dispatchKeyEvent', type='keyDown', windowsVirtualKeyCode=17, key='Control', code='ControlLeft', modifiers=0)
c.cmd('Input.dispatchKeyEvent', type='keyDown', windowsVirtualKeyCode=13, key='Enter', code='Enter', modifiers=2)
time.sleep(0.5)
c.cmd('Input.dispatchKeyEvent', type='keyUp', windowsVirtualKeyCode=13, key='Enter', code='Enter', modifiers=2)
c.cmd('Input.dispatchKeyEvent', type='keyUp', windowsVirtualKeyCode=17, key='Control', code='ControlLeft', modifiers=0)
```

**Pitfall**: `optDiv.click()` JS must be used — real mouse clicks at coordinates do NOT register with HeadlessUI's React state.

**Pitfall — text-matching hits wrong questions.** When answer text appears in multiple questions (e.g. "align-items: center" appears in Q11 and Q13), the text-search finds the FIRST match and clicks it, skipping the other question. Detection: after selecting all answers, verify each radiogroup has a selected option. Fix: select by GROUP INDEX with exact option index per group:

```python
# Check which groups are missing
st = evc(c, """(() => {
  const groups = [...document.querySelectorAll('[role="radiogroup"]')];
  return JSON.stringify(groups.map((g, i) => {
    const radios = [...g.querySelectorAll('[role="radio"]')];
    const sel = radios.find(r => r.getAttribute('aria-checked') === 'true');
    return {q: i+1, selected: sel ? 'OK' : 'NONE'};
  }).filter(x => x.selected === 'NONE').map(x => x.q));
})()""")
# Select by group index and option index
evc(c, """(() => {
  const groups = [...document.querySelectorAll('[role="radiogroup"]')];
  const g = groups[9];  # Q10 (0-indexed)
  const radios = [...g.querySelectorAll('[role="radio"]')];
  radios[3].click();  # 4th option
})()""")
```

**Pitfall — "Yes, I am finished" seems to do nothing (usually a WRONG-ANSWER / review-state issue, not a broken dialog).** Observed on quiz-css-flexbox (2026-08-31): "Finish the quiz" opened the dialog, "Yes, I am finished" closed it, but no score appeared and the module counter stayed 69/70. Root cause discovered: the quiz had been submitted with WRONG answers, so the page sat in the read-only review state ("You have 4 out of 20 questions correct") — re-selecting radios had no effect, and the "Yes" click just closed a stale dialog. The dialog itself was never broken. **Diagnosis order when submit "fails":**
1. Search the page for `You have N out of 20` — if present, you're in review mode; the answers were wrong. Fix: correct the answers (question set rotates — see above), then navigate away-and-back to a fresh editable quiz, re-select, re-submit.
2. Only treat it as a backend/UI dead end if you've submitted a CONFIRMED-correct set (20/20 selected, verified) and the dialog still won't close or the score still won't appear.

Ground truth is the module counter on the course map (`\d+ of \d+ steps`), not the quiz page URL. When the module shows N/20 on the quiz block but the map counter is already complete, the quiz actually passed — the page URL just lags.

## Review Page (Video-Quiz style)

fCC reviews use a checkbox in a `label.video-quiz-option-label`. The checkbox is React-controlled.

**Marking the checkbox**: click the LABEL, NOT the input:

```python
evc(c, "(() => { const label = document.querySelector('.video-quiz-option-label'); if(label) label.click(); })()")
```

Then click "Submit" → "Submit and go to next challenge" → Ctrl+Enter.

## CSS Corruption Recovery

When Monaco's CSS model gets corrupted (characterized by `& body` nesting in parsed stylesheets), the autosave restores the bad state even after reload.

**Fix**: Reset the lesson (click Reset button → confirm "Reset this lesson") OR navigate directly to the step URL. Then verify by checking `cssLen` from the preview iframe's stylesheets, NOT the textarea value.

## Donation Popup / Modal Overlay

After each reload, fCC shows a donation popup that steals focus. Close it immediately:

```python
evc(c, "(() => { [...document.querySelectorAll('button')].filter(b => /Ask me later|Close/i.test(b.textContent) && b.offsetParent !== null).forEach(b => b.click()); return 'ok'; })()")
```

**Pitfall — the modal can be an INVISIBLE overlay covering the editor, not a visible popup.** Symptom: `ta.focus()` keeps returning `BODY` (or `BUTTON`) no matter how many times you focus / click-fallback, and `elementFromPoint` at the editor's position returns `DIV.donation-modal` or `DIV.fixed ...` instead of the Monaco editor. Root cause: a `.donation-modal` or `.project-preview-modal` div is transparently stacked on top of the editor and eats all focus events. **Always diagnose with `elementFromPoint` before assuming the editor is broken**:

```python
# Quick diagnostic: what's actually on top of the editor?
st = evc(c, """(() => {
  const el = document.elementFromPoint(365, 300);
  return el ? el.tagName + '.' + (el.className||'').toString().slice(0,40) : 'none';
})()""")
print('at editor:', st)  # If shows DIV.donation-modal, close it first
```

Close the donation modal:

```python
evc(c, """(() => { const modal = document.querySelector('.donation-modal');
  if (modal) { const b = [...modal.querySelectorAll('button')].find(x => /ask me later/i.test(x.textContent));
    if (b) { b.click(); return 'closed'; } modal.remove(); return 'removed'; }
  return 'no-modal'; })()""")
```

**Pitfall — "Ask me later" click may NOT close the modal.** Observed on step-41 of Nutritional Label workshop (2026-08-31): clicking "Ask me later" returned successfully (button was found and clicked), but the modal's `.offsetParent` was still non-null (visible), and the element was still in the DOM with `display: block`. Root cause suspected: the donation modal's React state rejects the click if its internal iframe has focus. **Fix — force-remove the modal from the DOM instead of clicking the button**:

```python
evc(c, """(() => { const m = document.querySelector('.donation-modal');
  if (m) { m.remove(); return 'removed'; } return 'none'; })()""")
```

After removal, verify `!!document.querySelector('.donation-modal')` returns `false` and `document.activeElement.tagName` returns `"BODY"` before attempting to focus the textarea.

Also: a `Close×` button at negative y (off-viewport, e.g. `y:-153` or `y:-17`) still counts as the focused element and steals focus — close it or `location.reload()` to clear it.

## Chrome Crash / Port 9222 Recovery

Chrome A (the fCC automation browser) can die mid-session: the page's WS connections time out (`WebSocketTimeoutException: Connection timed out`), then `curl http://localhost:9222/json` returns empty / `Connection refused`, and `ss -tlnp | grep 9222` shows nothing listening.

**Symptom chain**: repeated `WebSocketTimeoutException` while reading the course map → `/json` unresponsive → `Connection refused` → port 9222 gone.

**Fix — relaunch with the SAME profile** (keeps the fCC login and all progress):

```bash
# 1. Verify it's really dead
ss -tlnp 2>/dev/null | grep 9222 || echo "port 9222 not listening"

# 2. Relaunch as a background process (use terminal background=true, NOT '&')
#    (note: you may need to pkill leftover chrome first)
pkill -f 'user-data-dir=/home/isma/.chrome-agent' 2>/dev/null; sleep 2
/opt/google/chrome/chrome --remote-debugging-port=9222 --user-data-dir=/home/isma/.chrome-agent --no-first-run --no-default-browser-check --disable-features=TranslateUI about:blank

# 3. Verify
sleep 5; curl -s --max-time 5 http://localhost:9222/json/version | head -3
```

**Pitfall — `/json/new` returns 405** after relaunch. The GET create-tab endpoint is disabled; don't use it to open a fresh map tab. Instead, connect to an existing `about:blank` page target and use `Page.navigate`:

```python
import json, urllib.request
tab = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=10).read())
pages = [t for t in tab if t['type'] == 'page']
c = CDP(pages[0]['webSocketDebuggerUrl'])
c.cmd('Page.navigate', url='https://www.freecodecamp.org/learn/responsive-web-design-v9/')
time.sleep(14)
```

**Pitfall — closing Stripe iframe targets can kill Chrome.** Stripe creates dozens of iframe page targets (`js.stripe.com/...`, `m.stripe.network/...`). Closing them via `/json/close/<id>` to declutter has, in practice, taken down the whole browser (port 9222 dies). If you must declutter, use `Page.close` on a CDP connection to that specific target, or just live with the iframes and keep using the main page target. Prefer a fresh `about:blank` tab + `Page.navigate` over killing iframes.

**Pitfall — reading the course map right after `location.href =` may hit a stale SPA or WS timeout.** After navigating to the map, wait ≥12s, then read module counters. If the URL still shows the old quiz/challenge page after navigating, force `location.reload()`; if the WS times out mid-read, reconnect (new `CDP(ws_url)`) and retry once.

## Module Structure (RWD v9)

Each module has: lectures (3-4 steps) → workshops (many steps) → labs (1-2) → review (1) → quiz (1). Total steps vary (e.g. Styling Forms = 84, Box Model = 54).

**Verified module step counts** (as of 2026-09-06):
- Typography: 78 total = 7 lectures×3 (21) + workshop Nutritional Label (68) + lab Newspaper Article (1) + review (1) + quiz (1) = 92? No — the lecture steps are 7×3=21 but only count as 7 steps in the module counter. Actual: 78 = 7 (lectures) + 68 (workshop) + 1 (lab) + 1 (review) + 1 (quiz).
- Accessibility: 72 total (3 already done from prior session)
- Positioning: 88 total
- Attribute Selectors: 71 total
- Responsive Design: 37 total
- Variables: 120 total
- Grid: 91 total
- Animations: 139 total
- CSS grand total: 1234 steps

Navigate to specific URLs:
- Lecture: `.../lecture-<slug>/<slug>`
- Workshop: `.../workshop-<slug>/step-<N>`
- Lab: `.../lab-<slug>/<slug>`
- Review: `.../review-<slug>/review-<slug>`
- Quiz: `.../quiz-<slug>/quiz-<slug>`