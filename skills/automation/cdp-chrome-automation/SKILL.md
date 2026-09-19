---
name: cdp-chrome-automation
version: 1.0.0
description: Drive the logged-in Chrome via CDP for login-gated pages.
---

# CDP Chrome Automation (real session, Linux/Wayland)

## When to Use

- The task must run inside the user's real Chrome session (existing logins/cookies) — course platforms, dashboards, web-app flows that block or degrade for fresh automation browsers.
- cua-driver cannot enumerate windows (Hyprland/Wayland) but Chrome is running.
- NOT for: public pages with no auth (use Playwright MCP), or desktop UI outside the browser (use computer-use).

## Overview

Drive the user's actual Chrome via the DevTools Protocol on `localhost:9222`. Use this class when Playwright MCP / browser-use would get a cookie-less fresh browser, or when cua-driver cannot enumerate windows (Hyprland/Wayland — it only sees windows on the active workspace, if any).

## One-time setup (per machine)

1. Copy a MINIMAL profile — never the whole `~/.config/google-chrome` (can be 800MB+):
   `Local State` + `Default/{Cookies, Cookies-journal, Login Data, Web Data, Preferences, History, Local Storage/, Session Storage/}` → `~/.chrome-agent/Default/`. Keeps fCC/logins alive.
2. Launch Chrome as a tracked background process:
   `/opt/google/chrome/chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-agent --no-first-run --no-default-browser-check --ozone-platform=wayland <url>`
3. Python side: `uv venv ~/.chrome-agent/venv && uv pip install websocket-client`.
4. Copy `scripts/cdp_eval.py` (this skill) to `~/.chrome-agent/` as the one-shot evaluator.

## The one-shot eval pattern (critical)

- **Fresh websocket per command.** Long-lived connections time out on slow pages; every eval = new connection.
- `suppress_origin=True` on `create_connection` or Chrome 403s the WS handshake.
- **Result extraction:** success payload is `r['result']['value']` — a SINGLE `result` level. Reading `r['result']['result']['value']` returns None and makes working evals look broken; when in doubt print the raw JSON.
- `location.href = '...'` returns before load. Sleep, then a fresh eval reads the new page. After `location.reload()` allow 9–12s for SPA editors/questions to mount.

## Input that actually works

| Action | Method |
|---|---|
| Buttons / Radix tabs / accordions | **Real CDP mouse events** at element coords (`Input.dispatchMouseEvent` press+release). JS `.click()` is silently ignored by many React component libs. |
| React-managed tabs / collapsible blocks | Fiber onClick: `Object.keys(el).find(k => k.startsWith('__reactProps$'))` → `el[fk].onClick({})`. |
| headlessui radiogroup options (quizzes) | **Try plain JS `.click()` on the `[role=radio]` div first, then real CDP clicks.** NOT consistent across quizzes: v9 Colors quiz needed REAL clicks (fiber onClick left `aria-checked='false'` 0/20; real clicks 20/20), but v9 Styling Forms quiz (2026-08-31) real CDP clicks left `aria-checked='false'` (1/40) and plain `div[role=radio].click()` from page context marked 10/10. Verify by counting `[role=radio][aria-checked="true"]`; if one method doesn't register, switch. `scrollIntoView({block:'center'})` first — quiz pages are tall and option rects go off-viewport (negative y). |
| Select-all / submit | CDP key events (`Input.dispatchKeyEvent`, modifiers=2 for Ctrl) — Ctrl+A, Ctrl+Enter etc. **Quiz/review "Submit and go to next challenge" can ignore JS `.click()`; send Ctrl+Enter** (keyDown Control → keyDown Enter modifiers=2 → keyUp Enter → keyUp Control) to navigate — verified 2026-08-31 Styling Forms quiz. |
| Bulk text into editors | **`Input.insertText` (CDP trusted event) is the primary method.** The synthetic `ClipboardEvent('paste')` + `DataTransfer` approach intermittently stops working mid-session (Monaco internal focus management drops page-dispatched events) — if a paste that worked stops landing, switch to `Input.insertText` immediately instead of retrying the paste. `execCommand('insertText')` from page context is also unreliable; the CDP-level command is not. |
| Single-line insertText (dodge Monaco auto-indent) | **Multi-line `Input.insertText` triggers Monaco's auto-indent on every linebreak**, causing progressive indentation corruption (each subsequent line gets extra indentation, content duplicates). **Fix: pass the entire content as a single line.** CSS is whitespace-insensitive — tests pass. For HTML, `<!DOCTYPE>` and self-closing tags work fine inline. Always verify via preview iframe after insert. |
| Selection verification before insert | **If select-all (Ctrl+A) fails** — focus lost to donation popup, editor collapsed, or Monaco virtual textarea not synced — `Input.insertText` **appends** instead of replacing, producing duplicated content (len ≈ 2× original). **Fix: verify selection length BEFORE inserting** via `document.execCommand('selectAll'); const s = window.getSelection().toString(); JSON.stringify({len: s.length})`. If len is 0, retry focus (real mouse click on editor, or dismiss popup) before re-trying. |
| Ctrl+A must be `keyDown`, not `rawKeyDown` | **Monaco's select-all only registers from `Input.dispatchKeyEvent` with `type='keyDown'` + `key='a'`.** `rawKeyDown`+`keyUp` pairs are silently ignored — Ctrl+A appears to do nothing (selectionStart/End stay at end of text), so insertText appends. Verified 2026-08-30: the fix that finally worked was keyDown Ctrl+A → **Backspace** → insertText. |
| Full-replace = Ctrl+A + Backspace + insertText | **Even with selection verified > 0, insertText alone can still append** (Monaco virtualizes the textarea: insertText replaces only the visible portion, the rest of the model survives → duplicated content). The bulletproof full-replace is: keyDown Ctrl+A → sleep → **Backspace key event (empties the entire model)** → sleep 2-3 → `Input.insertText` with the full content. Verify emptiness via the preview iframe (model length drops to just the site's own injected styles) before inserting. |
| Paste truncation | Long pastes sometimes land **with the last line/rule silently cut off** (recurring on multi-rule CSS). Always verify via the site's data source (preview iframe srcdoc / aria state) for the LAST expected rule, not just the first. Fix: `Ctrl+End` (CDP key event) + `Input.insertText` of the missing rule, or select-all + full re-paste. |
| Char-by-char typing | `Input.dispatchKeyEvent` with `text=` per char works when paste is blocked; shifted chars need `modifiers=8` (`{`=`BracketLeft`, `}`=`BracketRight`, `:`=`Semicolon`, `(`=`Digit9`, `)`=`Digit0`). Slow — last resort. |
| Select-all / submit | CDP key events (`Input.dispatchKeyEvent`, modifiers=2 for Ctrl) — Ctrl+A, Ctrl+Enter etc. Read selection via `window.getSelection().toString()` (only reliable after a real mouse click focused the editor; JS `.focus()` alone may not register). |

## Focus gotchas (Wayland — the #1 time sink)

- `document.hasFocus() === false` → synthetic input is silently dropped or **applied seconds late, duplicated**. Check hasFocus before every paste burst.
- Notification apps (ZapZap/WhatsApp) and terminal-approval dialogs steal focus mid-flow. Re-check and re-focus.
- Hyprland window management: cua-driver can't see the windows. Use `hyprctl eval` Lua API: `hl.get_windows()` → match `class`/`address` → `hl.dsp.focus({ window = w })` (takes an OBJECT `{window=w}`, not the window itself). Classic `hyprctl dispatch` syntax is gone (Lua now); `hl.dsp.workspace` etc. are tables — enumerate with `pairs()` writing to a temp file since eval doesn't print returns.
- Foreground tool-approval prompts bring kitty to the front — a common root cause when a paste that worked stops working.

## Verification discipline

- **Never trust Monaco `.view-lines.innerText` as ground truth** — it is virtualized (only visible lines) AND lags ~2–5s behind the model after a paste. Read the site's own data instead: preview iframes (`srcdoc` contains the rendered HTML+CSS), `aria-checked`, `[role=dialog]`, result panels. Allow several seconds before verifying, and treat `len: 0` / stale content as "check again later" not "paste failed".
- `document.elementFromPoint` hit-test before every real click: donation popups, sticky headers and overlays silently eat clicks. Dismiss popups first (usually a "Ask me later" button).
- After state-changing clicks, sleep then re-read from the data source, never from the editor DOM.
- **JS-reported focus can lie**: `ta.focus()` + `document.activeElement === 'TEXTAREA'` may report success while Monaco internally never gave the editor keyboard focus (paste silently dropped). The reliable combo: real CDP mouse click inside the editor (get textarea coords via `getBoundingClientRect` if view-lines is virtualized) → verify `document.activeElement.tagName === 'TEXTAREA'` → `Ctrl+End` → `Input.insertText`.
- **Chrome losing CDP mid-session** (Connection refused on :9222, but a Chrome process remains): the debug instance died or a non-debug Chrome took over. Recover: `pkill -f '/opt/google/chrome/chrome'`, wait 3s, relaunch with `--remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-agent` as a tracked background process. fCC auto-saves editor content server-side — the in-progress step restores on reload; committed steps are safe.

## Pitfalls

- **Never guess content slugs/URLs from memory** — wrong slugs land on fCC's "Page not found" quote page. Always read the actual anchor hrefs from the course map page first.
- This user is impatient with detours ("que pasa porque te estás demorando") and gives batch instructions ("termina X, luego Y, luego Z"). Move straight through the whole batch; the expand-and-enumerate pattern above is the fast path — don't rediscover it by trial and error.
- Keep a persistent state file (e.g. `~/.chrome-agent/css_state.css`, quiz answer files) so an interrupted flow can resume without re-deriving content.

## See also

- `references/freecodecamp.md` — freeCodeCamp-specific DOM anatomy, quiz/lab workflows and known-good answers flow.
- `scripts/cdp_eval.py` — self-contained one-shot evaluator to install on the target machine.
- `scripts/fcc_step_set.py` — robust single-file setter for Monaco editors (reload → expand tab → focus → verify selection → single-line insertText → preview verify). Drop-in for the workshop step loop.
