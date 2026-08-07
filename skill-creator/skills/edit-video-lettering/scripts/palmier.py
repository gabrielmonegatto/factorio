"""Minimal MCP-over-HTTP client for palmier-pro (JSON-RPC + SSE responses)."""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:19789/mcp"
SESSION_FILE = "/Volumes/KINGSTON/claude/tools/video-use/remake3/.palmier_session"


def _post(payload, session=None):
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream"})
    if session:
        req.add_header("MCP-Session-Id", session)
    resp = urllib.request.urlopen(req, timeout=120)
    sid = resp.headers.get("MCP-Session-Id")
    want = payload.get("id")
    msgs = []
    buf = b""
    while True:
        line = resp.readline()
        if not line:
            break
        buf += line
        s = line.decode(errors="replace").strip()
        if s.startswith("data: ") and s[6:].strip():
            try:
                m = json.loads(s[6:])
                msgs.append(m)
                if want is not None and m.get("id") == want:
                    resp.close()
                    return sid, msgs
            except Exception:
                pass
        if want is None and s == "":
            # notification: one empty flush is enough
            resp.close()
            return sid, msgs
    return sid, msgs


def session():
    try:
        return open(SESSION_FILE).read().strip()
    except Exception:
        sid, _ = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                   "clientInfo": {"name": "claude-code", "version": "1.0"}}})
        _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
        open(SESSION_FILE, "w").write(sid)
        return sid


def call(name, arguments=None, _id=99):
    sid = session()
    _, msgs = _post({"jsonrpc": "2.0", "id": _id, "method": "tools/call",
                     "params": {"name": name, "arguments": arguments or {}}}, sid)
    for m in msgs:
        if m.get("id") == _id:
            r = m.get("result", m.get("error"))
            if isinstance(r, dict) and "content" in r:
                out = []
                for c in r["content"]:
                    if c.get("type") == "text":
                        out.append(c["text"])
                return "\n".join(out)
            return json.dumps(r)
    return json.dumps(msgs)


def list_tools():
    sid = session()
    _, msgs = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)
    for m in msgs:
        if m.get("id") == 2:
            return m["result"]["tools"]
    return []


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "tools":
        for t in list_tools():
            print(t["name"], "—", (t.get("description") or "")[:110].replace("\n", " "))
    elif cmd == "schema":
        for t in list_tools():
            if t["name"] == sys.argv[2]:
                print(json.dumps(t.get("inputSchema"), indent=1)[:4000])
    elif cmd == "call":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(call(sys.argv[2], args))
