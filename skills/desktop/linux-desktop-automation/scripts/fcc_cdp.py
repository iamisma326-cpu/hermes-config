#!/usr/bin/env python3
"""Reusable CDP client for driving a real Chrome started with
--remote-debugging-port=9222. Condensed from a validated freeCodeCamp
automation session (Aug 2026, Chrome 151 / Wayland / Hyprland).

CLI:
  fcc_cdp.py eval "<js expression>"        # evaluate, print JSON result
  fcc_cdp.py tabs                         # list page targets
Requires: python -m pip install websocket-client  (uv venv recommended)

Library use:
  import sys; sys.path.insert(0, <skill_dir>/scripts)
  from fcc_cdp import get_tab, CDP, ev
"""

import json
import urllib.request

import websocket  # pip install websocket-client

CDP_HTTP = "http://localhost:9222"


def get_tabs():
    return json.load(urllib.request.urlopen(f"{CDP_HTTP}/json"))


def get_tab(url_substr="freecodecamp"):
    """Return the first page target whose URL contains url_substr."""
    for t in get_tabs():
        if t.get("type") == "page" and url_substr in t.get("url", ""):
            return t
    raise SystemExit(f"no page target matching {url_substr!r}; targets: "
                     + json.dumps([(t.get('type'), t.get('url', '')[:60]) for t in get_tabs()]))


class CDP:
    """Minimal synchronous CDP connection to one target."""

    def __init__(self, ws_url):
        # suppress_origin=True is REQUIRED: Chrome rejects WS connections
        # carrying an Origin header unless --remote-allow-origins was set.
        self.ws = websocket.create_connection(ws_url, timeout=30,
                                              suppress_origin=True)
        self._id = 0

    def cmd(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method,
                                 "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(f"CDP error: {msg['error']}")
                return msg.get("result", {})


def make_client(url_substr="freecodecamp"):
    return CDP(get_tab(url_substr)["webSocketDebuggerUrl"])


def ev(js, cdp=None):
    """Runtime.evaluate with return_by_value + await_promise. Returns the
    JSON value, raising on JS exceptions."""
    if cdp is None:
        cdp = make_client()
    r = cdp.cmd("Runtime.evaluate", expression=js, return_by_value=True,
                await_promise=True, timeout=20000)
    if r.get("exceptionDetails"):
        desc = r["exceptionDetails"].get("exception", {}).get(
            "description", str(r["exceptionDetails"]))
        raise RuntimeError(desc)
    return r.get("result", {}).get("value")


# ---- input helpers (real input pipeline: lands like user input) ----------

def key(cdp, vk, code, key_name, modifiers=0, text=None):
    """Press + release. modifiers: 2=Ctrl, 8=Shift, 1=Alt, 4=Meta."""
    params = dict(type="rawKeyDown" if text is None else "keyDown",
                  modifiers=modifiers, windowsVirtualKeyCode=vk,
                  code=code, key=key_name)
    if text:
        params["text"] = text
    cdp.cmd("Input.dispatchKeyEvent", **params)
    cdp.cmd("Input.dispatchKeyEvent", type="keyUp", modifiers=modifiers,
            windowsVirtualKeyCode=vk, code=code, key=key_name)


def ctrl_key(cdp, vk, code, key_name):
    key(cdp, vk, code, key_name, modifiers=2)


def click(cdp, x, y):
    cdp.cmd("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y,
            button="left", clickCount=1)
    cdp.cmd("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y,
            button="left", clickCount=1)


def synthetic_paste(cdp, js_prefix_for_textarea, text, ev_fn=ev):
    """Dispatch a ClipboardEvent('paste') with arbitrary text on a given
    textarea selector expression. Focus-independent and reliable; Monaco
    handles it verbatim (no auto-indent)."""
    return ev_fn(
        "(t => { const ta = " + js_prefix_for_textarea
        + "; const dt = new DataTransfer(); dt.setData('text/plain', t); "
          "ta.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, "
          "bubbles: true, cancelable: true })); return 'pasted'; })"
        + "(" + json.dumps(text) + ")")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tabs"
    if cmd == "tabs":
        for t in get_tabs():
            if t.get("type") == "page":
                print(t.get("url", ""))
    elif cmd == "eval":
        print(json.dumps(ev(sys.argv[2]), ensure_ascii=False, indent=1))
