#!/home/isma/.chrome-agent/venv/bin/python
"""One-shot CDP evaluator for the user's debug Chrome (localhost:9222).

Usage:
  cdp_eval.py "<js expression>"          # evaluate, print the value
Install with the minimal-profile Chrome described in SKILL.md.
Key details baked in: fresh websocket per call (long-lived ones time out),
suppress_origin (Chrome 403s the handshake otherwise), correct single-level
result extraction r['result']['value'].
"""
import json, sys, urllib.request
import websocket

def get_tab(url_substr='freecodecamp'):
    data = json.load(urllib.request.urlopen('http://localhost:9222/json', timeout=10))
    pages = [t for t in data if t.get('type') == 'page']
    tab = next((t for t in pages if url_substr in t.get('url', '')), pages[0] if pages else None)
    if not tab:
        raise SystemExit('no matching tab')
    return tab

def run_js(js, timeout_ms=20000):
    tab = get_tab()
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=30,
                                     suppress_origin=True)
    try:
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                            'params': {'expression': js, 'return_by_value': True,
                                       'await_promise': True, 'timeout': timeout_ms}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get('id') == 1:
                if 'exceptionDetails' in msg:
                    return 'EXC: ' + json.dumps(msg['exceptionDetails'])[:300]
                res = msg.get('result', {}).get('result', {})
                if 'value' in res:
                    return res['value']
                if res.get('type') == 'undefined':
                    return '(undefined)'
                return '(no-value)'
    finally:
        ws.close()

if __name__ == '__main__':
    print(run_js(sys.argv[1]))
