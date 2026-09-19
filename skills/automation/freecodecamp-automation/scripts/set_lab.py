#!/usr/bin/env python3
"""Set both HTML and CSS files in an fCC lab using React fiber + Monaco model.setValue().
Usage: set_lab.py '<html-content>' '<css-content>'

This approach bypasses Input.insertText (which always targets the first Monaco editor)
and directly sets the Monaco model values through the React fiber tree.

Created 2026-09-06 for the Newspaper Article lab (Typography module).
Verified: 30/30 tests passed.
"""
import json, time, sys
sys.path.insert(0, '/home/isma/.chrome-agent')
from cdp import CDP, get_tab

def evc(c, js):
    r = c.cmd('Runtime.evaluate', expression=js, returnByValue=True, awaitPromise=True, timeout=20000)
    if r.get('exceptionDetails'):
        return {'ERROR': r['exceptionDetails']}
    return r.get('result', {}).get('value')

def set_model_via_fiber(c, container_index, content):
    """Set Monaco model content via React fiber tree."""
    escaped = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    return evc(c, f"""(() => {{
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

def main():
    html = sys.argv[1]
    css = sys.argv[2]

    tab = get_tab('freecodecamp')
    c = CDP(tab['webSocketDebuggerUrl'])

    # Reload for clean state
    evc(c, "location.reload()")
    time.sleep(15)

    # Close donation modal
    evc(c, "(() => { const m = document.querySelector('.donation-modal'); if(m) m.remove(); })()")
    time.sleep(2)

    # Wait for editors to load
    for i in range(10):
        r = evc(c, "document.querySelectorAll('.react-monaco-editor-container').length")
        if int(str(r)) >= 1:
            print(f'editors loaded after {i+1} checks')
            break
        time.sleep(2)

    # Set both models via fiber
    print('Setting index.html...')
    r1 = set_model_via_fiber(c, 0, html)
    print(f'  HTML: {r1}')

    print('Setting styles.css...')
    r2 = set_model_via_fiber(c, 1, css)
    print(f'  CSS: {r2}')

    # Click Check Your Code
    print('Clicking Check Your Code...')
    evc(c, """(() => {
      const btn = [...document.querySelectorAll('button')].find(x => /Check Your Code/i.test(x.textContent));
      if (btn) { btn.click(); return 'clicked'; }
      return 'no btn';
    })()""")
    time.sleep(15)

    # Results
    r = evc(c, """(() => {
      const btn = [...document.querySelectorAll('button')].find(x => /submit and continue/i.test(x.textContent));
      if (btn) return 'PASSED';
      const body = document.body.innerText;
      const passed = (body.match(/Passed:/gi) || []).length;
      const failed = (body.match(/Failed:/gi) || []).length;
      return passed + ' passed, ' + failed + ' failed';
    })()""")
    print(f'Result: {r}')

if __name__ == '__main__':
    main()
