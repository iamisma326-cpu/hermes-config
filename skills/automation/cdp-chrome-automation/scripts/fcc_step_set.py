#!/home/isma/.chrome-agent/venv/bin/python
"""Robust single-file setter for fCC workshop steps (Monaco editors).

Usage: fcc_step_set.py <index.html|styles.css> '<full file content as ONE line>'

Steps (matches references/freecodecamp.md 'robust step loop' — 2026-08-30 verified):
  1. location.reload() -> sleep 9  (fixes SPA desync AND resets Monaco corruption)
  2. expand the target file tab ONLY if aria-expanded != 'true'
  3. focus textarea, Ctrl+A via type='keyDown' (rawKeyDown does NOT register Monaco's select-all)
  4. Backspace — EMPTIES the model before insert. Ctrl+A + insertText alone silently
     APPENDS instead of replacing (Monaco virtualizes the textarea: insertText replaces
     only the visible portion). Backspace-then-insert is the bulletproof replace.
  5. Input.insertText with full content on ONE line (dodges Monaco auto-indent corruption)
  6. sleep 5-8, then verify via the PREVIEW IFRAME (source of truth), not getSelection()

If the editor stays corrupted/duplicated after a reload, navigate DIRECTLY to the step URL
(window.location.href = '.../step-N') instead of fighting the stuck "Reset this lesson" dialog.

Requires: ~/.chrome-agent/cdp.py (CDP + get_tab), Chrome on :9222 with the fCC tab.
"""
import json, time, sys
sys.path.insert(0, '/home/isma/.chrome-agent')
from cdp import CDP, get_tab

def evc(c, js):
    r = c.cmd('Runtime.evaluate', expression=js, return_by_value=True,
              await_promise=True, timeout=20000)
    if r.get('exceptionDetails'):
        return {'ERROR': r['exceptionDetails']}
    return r.get('result', {}).get('value')

def key(c, code, vk, mods=2, key=''):
    # IMPORTANTE: type='keyDown' (NOT 'rawKeyDown') for shortcuts like Ctrl+A so
    # Monaco processes the select-all. rawKeyDown does not register with Monaco.
    c.cmd('Input.dispatchKeyEvent', type='keyDown', modifiers=mods,
          windowsVirtualKeyCode=vk, code=code, key=key or '')
    time.sleep(0.3)
    c.cmd('Input.dispatchKeyEvent', type='keyUp', modifiers=mods,
          windowsVirtualKeyCode=vk, code=code, key=key or '')

def main():
    fname, text = sys.argv[1], sys.argv[2]
    tab = get_tab('freecodecamp')
    c = CDP(tab['webSocketDebuggerUrl'])

    # 1. reload for clean state
    evc(c, "location.reload()")
    time.sleep(9)

    # 2. expand target tab (guard collapse trap)
    r = evc(c, f"""(() => {{
      const el = [...document.querySelectorAll('.monaco-editor-tabs button')]
        .find(e => e.textContent.includes('{fname}'));
      if (!el) return 'no-tab';
      if (el.getAttribute('aria-expanded') !== 'true') {{ el.click(); return 'clicked'; }}
      return 'already-open';
    }})()""")
    print('tab:', r)
    time.sleep(2)

    # 3. focus textarea
    f = evc(c, "(() => { const ta = document.querySelector('.monaco-editor textarea'); ta.focus(); return document.activeElement.tagName; })()")
    print('focus:', f)
    if f != 'TEXTAREA':
        box = evc(c, """(() => {
          const r = document.querySelector('.monaco-editor').getBoundingClientRect();
          return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + Math.min(r.height/2, 200))});
        })()""")
        b = json.loads(box)
        c.cmd('Input.dispatchMouseEvent', type='mousePressed', x=b['x'], y=b['y'], button='left', clickCount=1)
        c.cmd('Input.dispatchMouseEvent', type='mouseReleased', x=b['x'], y=b['y'], button='left', clickCount=1)
        time.sleep(1)
        evc(c, "(() => { const ta = document.querySelector('.monaco-editor textarea'); ta.focus(); return document.activeElement.tagName; })()")

    # 4. Ctrl+A (keyDown) + Backspace: empty the model so insert REPLACES not appends
    key(c, 'KeyA', 65, 2, 'a')
    time.sleep(1.5)
    sel = evc(c, "(() => { document.execCommand('selectAll'); return JSON.stringify({len: window.getSelection().toString().length}); })()")
    print('sel-before:', sel)
    key(c, 'Backspace', 8, 0, 'Backspace')
    time.sleep(2.5)
    empty = evc(c, "(() => { const ta = document.querySelector('.monaco-editor textarea'); return JSON.stringify({len: ta ? ta.value.length : 0}); })()")
    print('after-backspace:', empty)

    # 5. single-line insert
    c.cmd('Input.insertText', text=text)
    time.sleep(6)

    # 6. verify via PREVIEW IFRAME (source of truth)
    prev = evc(c, """(() => {
      const f = document.querySelector('iframe');
      if (!f || !f.contentDocument) return 'no-iframe';
      let cssText = '';
      f.contentDocument.querySelectorAll('style').forEach(st => cssText += st.textContent);
      return JSON.stringify({cssLen: cssText.length, cssHead: cssText.replace(/\\s+/g, ' ').slice(0, 120)});
    })()""")
    print('preview:', prev)

if __name__ == '__main__':
    main()
