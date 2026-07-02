#!/usr/bin/env python3
"""
recc — Reverse-Engineer Claude Code CLI.

A small, honest inspector for the things the guide describes, run against
YOUR OWN account with YOUR OWN key. It observes usage; it never bypasses
billing or authentication.

Commands:
    recc tokens <text|file>       count tokens (local estimate + API count)
    recc cost <session.jsonl...>  reconstruct cost from transcript usage
    recc sessions                 list local Claude Code sessions
    recc inspect <session.jsonl>  pretty-print a transcript
    recc proxy [--port 8080]      logging reverse-proxy to the Anthropic API

Env:
    ANTHROPIC_API_KEY   required for `tokens` (API count) and `proxy`
"""
import argparse, glob, json, os, sys, textwrap
from pathlib import Path

# ---- pricing (USD per 1M tokens); update from anthropic.com/pricing --------
PRICING = {
    # model substring : (input, cache_write, cache_read, output)
    "claude-opus-4":   (15.0, 18.75, 1.50, 75.0),
    "claude-sonnet":   (3.0,  3.75,  0.30, 15.0),
    "claude-haiku":    (0.80, 1.0,   0.08, 4.0),
    "claude-fable":    (3.0,  3.75,  0.30, 15.0),  # placeholder; verify
}
DEFAULT_PRICE = PRICING["claude-sonnet"]
CLAUDE_DIR = Path(os.path.expanduser("~/.claude"))

C = {"b": "\033[1m", "d": "\033[2m", "g": "\033[32m", "c": "\033[36m",
     "y": "\033[33m", "r": "\033[31m", "x": "\033[0m"}
def color(s, k): return f"{C[k]}{s}{C['x']}" if sys.stdout.isatty() else str(s)


def price_for(model: str):
    for key, p in PRICING.items():
        if key in (model or ""):
            return p
    return DEFAULT_PRICE


def usd(cents):
    return f"${cents:,.4f}"


# --------------------------------------------------------------------------- #
def cmd_tokens(args):
    text = args.text
    p = Path(text)
    if p.exists() and p.is_file():
        text = p.read_text(errors="replace")
        print(color(f"read {len(text)} chars from {p}", "d"))
    est = max(1, round(len(text) / 4))  # ~4 chars/token rule of thumb
    print(f"{color('local estimate', 'c')}: ~{est:,} tokens (chars/4)")

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(color("set ANTHROPIC_API_KEY for an exact API count", "y"))
        return
    try:
        from anthropic import Anthropic
        client = Anthropic()
        r = client.messages.count_tokens(
            model="claude-sonnet-5",
            messages=[{"role": "user", "content": text}],
        )
        print(f"{color('API count', 'g')}: {r.input_tokens:,} tokens "
              f"(model=claude-sonnet-5)")
    except Exception as e:
        print(color(f"API count failed: {e}", "r"))


# --------------------------------------------------------------------------- #
def _iter_usage(path):
    for line in Path(path).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = obj.get("message", {})
        u = msg.get("usage")
        if u:
            yield msg.get("model", ""), u


def cmd_cost(args):
    paths = []
    for pat in args.paths:
        paths.extend(glob.glob(os.path.expanduser(pat)))
    if not paths:
        print(color("no files matched", "r")); return

    grand = 0.0
    tot = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for path in paths:
        sub = 0.0
        sc = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
        for model, u in _iter_usage(path):
            pi, pcw, pcr, po = price_for(model)
            i = u.get("input_tokens", 0)
            cw = u.get("cache_creation_input_tokens", 0)
            cr = u.get("cache_read_input_tokens", 0)
            o = u.get("output_tokens", 0)
            sub += (i*pi + cw*pcw + cr*pcr + o*po) / 1_000_000
            sc["input"] += i; sc["cache_write"] += cw
            sc["cache_read"] += cr; sc["output"] += o
        for k in tot: tot[k] += sc[k]
        grand += sub
        detail = "in={:,} cw={:,} cr={:,} out={:,}".format(
            sc["input"], sc["cache_write"], sc["cache_read"], sc["output"])
        print(f"{color(Path(path).name, 'c')}  {usd(sub)}  {color(detail, 'd')}")
    print(color("─" * 60, "d"))
    print(f"{color('TOTAL', 'b')}  {color(usd(grand), 'g')}   "
          f"input={tot['input']:,}  cache_write={tot['cache_write']:,}  "
          f"cache_read={tot['cache_read']:,}  output={tot['output']:,}")
    served = tot['cache_read']
    billed = tot['input'] + tot['cache_write'] + tot['cache_read']
    if billed:
        print(color(f"cache hit rate: {served/billed*100:.1f}% of input tokens "
                    f"served from cache", "d"))


# --------------------------------------------------------------------------- #
def cmd_sessions(args):
    root = CLAUDE_DIR / "projects"
    if not root.exists():
        print(color(f"no sessions dir at {root}", "y")); return
    files = sorted(root.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(color("no sessions found", "y")); return
    print(color(f"{'PROJECT':<28} {'SESSION':<14} {'LINES':>7} {'SIZE':>8}", "b"))
    for f in files[:args.limit]:
        proj = f.parent.name.replace("-home-" + os.environ.get("USER", ""), "~")[:27]
        n = sum(1 for _ in f.open())
        kb = f.stat().st_size / 1024
        print(f"{proj:<28} {f.stem[:13]:<14} {n:>7} {kb:>7.1f}K")


# --------------------------------------------------------------------------- #
def cmd_inspect(args):
    path = Path(os.path.expanduser(args.path))
    for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = o.get("type", "?")
        msg = o.get("message", {})
        content = msg.get("content", "")
        if isinstance(content, str):
            blocks = [{"type": "text", "text": content}]
        else:
            blocks = content or []
        head = {"user": "c", "assistant": "g"}.get(t, "y")
        u = msg.get("usage")
        usage = ""
        if u:
            usage = color(f"  [in={u.get('input_tokens',0)} "
                          f"cr={u.get('cache_read_input_tokens',0)} "
                          f"out={u.get('output_tokens',0)}]", "d")
        print(color(f"#{i} {t.upper()}", head) + usage)
        for b in blocks:
            bt = b.get("type")
            if bt == "text" and b.get("text", "").strip():
                print(textwrap.indent(textwrap.fill(b["text"].strip(), 90)[:600], "  "))
            elif bt == "tool_use":
                print("  " + color(f"⚙ {b.get('name')}", "y")
                      + " " + json.dumps(b.get("input", {}))[:120])
            elif bt == "tool_result":
                c = b.get("content", "")
                c = c if isinstance(c, str) else json.dumps(c)
                print("  " + color("↩ result", "d") + " " + c.replace("\n", " ")[:120])
        print()


# --------------------------------------------------------------------------- #
def cmd_proxy(args):
    """Minimal logging reverse-proxy. Point ANTHROPIC_BASE_URL at it."""
    try:
        import http.server, urllib.request, urllib.error
    except Exception as e:
        print(color(f"stdlib missing: {e}", "r")); return
    UPSTREAM = "https://api.anthropic.com"

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _proxy(self, method):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            if body and "/v1/messages" in self.path:
                try:
                    d = json.loads(body)
                    sys_len = len(json.dumps(d.get("system", "")))
                    print(color(f"\n▶ {method} {self.path}", "c"))
                    print(f"  model={d.get('model')} "
                          f"tools={len(d.get('tools', []))} "
                          f"messages={len(d.get('messages', []))} "
                          f"system~{sys_len}chars stream={d.get('stream')}")
                except Exception:
                    pass
            req = urllib.request.Request(UPSTREAM + self.path, data=body or None,
                                         method=method)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "content-length"):
                    req.add_header(k, v)
            try:
                with urllib.request.urlopen(req) as up:
                    data = up.read()
                    self.send_response(up.status)
                    for k, v in up.getheaders():
                        if k.lower() not in ("transfer-encoding", "content-encoding",
                                             "content-length", "connection"):
                            self.send_header(k, v)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except urllib.error.HTTPError as e:
                data = e.read()
                self.send_response(e.code); self.end_headers(); self.wfile.write(data)
        def do_GET(self):  self._proxy("GET")
        def do_POST(self): self._proxy("POST")

    port = args.port
    print(color(f"recc proxy on http://127.0.0.1:{port}  → {UPSTREAM}", "g"))
    print(color(f"run:  export ANTHROPIC_BASE_URL=http://127.0.0.1:{port}", "y"))
    print(color("note: streaming bodies are relayed but not decoded here; "
                "use mitmproxy for full SSE inspection.", "d"))
    http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(prog="recc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("tokens", help="count tokens in text or a file")
    p.add_argument("text"); p.set_defaults(func=cmd_tokens)

    p = sub.add_parser("cost", help="reconstruct cost from session transcripts")
    p.add_argument("paths", nargs="+"); p.set_defaults(func=cmd_cost)

    p = sub.add_parser("sessions", help="list local Claude Code sessions")
    p.add_argument("--limit", type=int, default=30); p.set_defaults(func=cmd_sessions)

    p = sub.add_parser("inspect", help="pretty-print a transcript")
    p.add_argument("path"); p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("proxy", help="logging reverse-proxy to the API")
    p.add_argument("--port", type=int, default=8080); p.set_defaults(func=cmd_proxy)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
