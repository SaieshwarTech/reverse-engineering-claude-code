#!/usr/bin/env python3
"""
recc-agent — a minimal but real open-source Claude Code clone.

Everything the guide describes, in one runnable file:
  • the agent loop (ch. 2)          • a tool layer: Read/Write/Edit/Bash/Grep/Glob (ch. 3)
  • a permission system (ch. 5)     • streaming output (ch. 2/8)
  • CLAUDE.md context (ch. 4)       • session save + resume (ch. 9)
  • a live token/cost meter

Uses the official Anthropic API with YOUR OWN key. It does not bypass billing.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 recc_agent.py                     # interactive REPL
    python3 recc_agent.py "fix the failing test"   # one-shot
    python3 recc_agent.py --resume            # continue last session
    python3 recc_agent.py --model claude-haiku-4-5   # cheaper model
    python3 recc_agent.py --yolo              # auto-approve everything (careful)
"""
import argparse, difflib, fnmatch, json, os, re, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------- config ---
DEFAULT_MODEL = "claude-sonnet-5"
SESSION_DIR = Path(os.path.expanduser("~/.recc/sessions"))
MAX_TOKENS = 8000
# USD per 1M tokens (input, cache_write, cache_read, output) — verify at anthropic.com/pricing
PRICING = {
    "claude-opus-4": (15.0, 18.75, 1.50, 75.0),
    "claude-sonnet": (3.0, 3.75, 0.30, 15.0),
    "claude-haiku":  (0.80, 1.0, 0.08, 4.0),
}
DENY_ALWAYS = [r"rm\s+-rf\s+/", r":\(\)\s*\{", r"mkfs", r"dd\s+if=.*of=/dev/"]

A = {k: (f"\033[{v}m" if sys.stdout.isatty() else "")
     for k, v in {"b": "1", "d": "2", "g": "32", "c": "36", "y": "33",
                  "r": "31", "m": "35", "x": "0"}.items()}
def col(s, k): return f"{A[k]}{s}{A['x']}"


# --------------------------------------------------------------- context ---
def load_claude_md():
    """CLAUDE.md hierarchy: user then project (ch. 4)."""
    parts = []
    for p in (Path(os.path.expanduser("~/.claude/CLAUDE.md")),
              Path.cwd() / "CLAUDE.md", Path.cwd() / ".claude" / "CLAUDE.md"):
        if p.exists():
            parts.append(f"# From {p}\n{p.read_text(errors='replace')}")
    return "\n\n".join(parts)


def system_prompt():
    env = (f"Working directory: {os.getcwd()}\n"
           f"Platform: {sys.platform}\n"
           f"Date: {datetime.now().date()}")
    memory = load_claude_md()
    base = f"""You are recc-agent, an open-source terminal coding assistant.

You help with software tasks by using tools to read, search, edit, and run code.
Rules:
- Read a file before editing it. Use Edit with a unique old_string.
- Prefer Grep/Glob over `find`/`grep` in Bash.
- Explain briefly what you're doing; cite paths as file:line.
- When the task is complete, reply with a short summary and NO tool calls.

<env>
{env}
</env>"""
    if memory:
        base += f"\n\n<user-instructions>\n{memory}\n</user-instructions>"
    return base


# ----------------------------------------------------------------- tools ---
TOOLS = [
    {"name": "read_file", "description": "Read a file. Returns line-numbered content.",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Create or overwrite a file.",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string"}, "content": {"type": "string"}},
      "required": ["path", "content"]}},
    {"name": "edit_file",
     "description": "Replace an exact, unique string in a file. old_string must occur exactly once.",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string"}, "old_string": {"type": "string"},
         "new_string": {"type": "string"}}, "required": ["path", "old_string", "new_string"]}},
    {"name": "bash", "description": "Run a shell command in the working directory.",
     "input_schema": {"type": "object", "properties": {
         "command": {"type": "string"}}, "required": ["command"]}},
    {"name": "grep", "description": "Search file contents with a regex. Returns matching lines.",
     "input_schema": {"type": "object", "properties": {
         "pattern": {"type": "string"}, "path": {"type": "string", "default": "."}},
      "required": ["pattern"]}},
    {"name": "glob", "description": "Find files by glob pattern, e.g. **/*.py.",
     "input_schema": {"type": "object", "properties": {
         "pattern": {"type": "string"}}, "required": ["pattern"]}},
]

MUTATING = {"write_file", "edit_file", "bash"}


def _line_numbered(text, start=1):
    return "\n".join(f"{i}\t{l}" for i, l in enumerate(text.splitlines(), start))


def run_tool(name, args, perms):
    try:
        if name == "read_file":
            p = Path(args["path"])
            if not p.exists():
                return f"ERROR: no such file: {p}"
            data = p.read_text(errors="replace").splitlines()
            perms["_read"].add(str(p.resolve()))
            body = "\n".join(f"{i}\t{l}" for i, l in enumerate(data[:2000], 1))
            more = "" if len(data) <= 2000 else f"\n... ({len(data)-2000} more lines)"
            return body + more or "(empty file)"

        if name == "write_file":
            p = Path(args["path"]); p.parent.mkdir(parents=True, exist_ok=True)
            existed = p.exists()
            p.write_text(args["content"])
            return f"{'Overwrote' if existed else 'Created'} {p} "\
                   f"({len(args['content'].splitlines())} lines)"

        if name == "edit_file":
            p = Path(args["path"])
            if not p.exists():
                return f"ERROR: no such file: {p}"
            src = p.read_text(errors="replace")
            n = src.count(args["old_string"])
            if n == 0:
                return "ERROR: old_string not found."
            if n > 1:
                return f"ERROR: old_string found {n} times; make it unique."
            new = src.replace(args["old_string"], args["new_string"])
            p.write_text(new)
            diff = "\n".join(difflib.unified_diff(
                args["old_string"].splitlines(), args["new_string"].splitlines(),
                lineterm="", n=1))
            return f"Edited {p}\n{diff}"

        if name == "bash":
            r = subprocess.run(args["command"], shell=True, capture_output=True,
                               text=True, timeout=180, cwd=os.getcwd())
            out = (r.stdout + r.stderr).strip()
            tag = "" if r.returncode == 0 else f"[exit {r.returncode}] "
            return tag + (out[-8000:] if out else "(no output)")

        if name == "grep":
            pat = re.compile(args["pattern"])
            root = Path(args.get("path", "."))
            hits, files = [], [root] if root.is_file() else root.rglob("*")
            for f in files:
                if not f.is_file() or f.stat().st_size > 2_000_000:
                    continue
                if any(seg in f.parts for seg in (".git", "node_modules", "__pycache__")):
                    continue
                try:
                    for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                        if pat.search(line):
                            hits.append(f"{f}:{i}: {line.strip()[:200]}")
                            if len(hits) >= 200:
                                return "\n".join(hits) + "\n... (truncated at 200)"
                except Exception:
                    pass
            return "\n".join(hits) if hits else "(no matches)"

        if name == "glob":
            matches = [str(p) for p in Path(".").rglob("*")
                       if fnmatch.fnmatch(str(p), args["pattern"])
                       and ".git" not in p.parts]
            matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return "\n".join(matches[:200]) if matches else "(no files)"

        return f"ERROR: unknown tool {name}"
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out (180s)"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


# ------------------------------------------------------------ permissions ---
def check_permission(name, args, perms):
    """Return (allowed, reason). Implements ch. 5 in miniature."""
    if name not in MUTATING:
        return True, "read-only"
    if name == "bash":
        cmd = args.get("command", "")
        for pat in DENY_ALWAYS:
            if re.search(pat, cmd):
                return False, f"blocked by safety rule: {pat}"
    if perms["yolo"]:
        return True, "yolo"
    sig = f"{name}:{args.get('command') or args.get('path')}"
    if sig in perms["approved"]:
        return True, "remembered"
    # interactive prompt
    desc = args.get("command") or args.get("path")
    print(col(f"\n  ⚠ {name} wants to: {desc}", "y"))
    ans = input(col("    allow? [y]es / [a]lways / [N]o: ", "y")).strip().lower()
    if ans == "a":
        perms["approved"].add(sig); return True, "approved+remember"
    if ans == "y":
        return True, "approved once"
    return False, "user denied"


# ------------------------------------------------------------- the loop ----
def price(model):
    for k, p in PRICING.items():
        if k in model:
            return p
    return PRICING["claude-sonnet"]


def meter(usage, model, running):
    pi, pcw, pcr, po = price(model)
    running["cost"] += (usage.input_tokens * pi
                        + getattr(usage, "cache_creation_input_tokens", 0) * pcw
                        + getattr(usage, "cache_read_input_tokens", 0) * pcr
                        + usage.output_tokens * po) / 1_000_000
    running["in"] += usage.input_tokens + getattr(usage, "cache_read_input_tokens", 0)
    running["out"] += usage.output_tokens
    print(col(f"  ⧗ tokens in≈{running['in']:,} out≈{running['out']:,}  "
              f"cost≈${running['cost']:.4f}", "d"))


def agent_turn(client, model, messages, perms, running):
    while True:  # THE agent loop (ch. 2)
        text_buf, tool_uses, cur = [], [], None
        with client.messages.stream(model=model, max_tokens=MAX_TOKENS,
                                     system=system_prompt(), tools=TOOLS,
                                     messages=messages) as stream:
            for event in stream:
                if event.type == "content_block_start" and event.content_block.type == "tool_use":
                    cur = {"id": event.content_block.id, "name": event.content_block.name, "json": ""}
                elif event.type == "content_block_delta":
                    d = event.delta
                    if d.type == "text_delta":
                        sys.stdout.write(d.text); sys.stdout.flush(); text_buf.append(d.text)
                    elif d.type == "input_json_delta" and cur:
                        cur["json"] += d.partial_json
                elif event.type == "content_block_stop" and cur:
                    tool_uses.append(cur); cur = None
            final = stream.get_final_message()
        print()
        meter(final.usage, model, running)

        messages.append({"role": "assistant", "content": final.content})
        calls = [b for b in final.content if b.type == "tool_use"]
        if not calls:
            return  # model finished the turn

        results = []
        for c in calls:
            args = c.input if isinstance(c.input, dict) else json.loads(c.input or "{}")
            ok, reason = check_permission(c.name, args, perms)
            if not ok:
                print(col(f"  ✗ {c.name} denied ({reason})", "r"))
                results.append({"type": "tool_result", "tool_use_id": c.id,
                                "content": f"ERROR: {reason}", "is_error": True})
                continue
            print(col(f"  ⚙ {c.name} ", "m")
                  + col(json.dumps(args)[:140], "d"))
            out = run_tool(c.name, args, perms)
            results.append({"type": "tool_result", "tool_use_id": c.id, "content": out})
        messages.append({"role": "user", "content": results})


# ------------------------------------------------------------- sessions ----
def save_session(sid, messages):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSION_DIR / f"{sid}.json"
    path.write_text(json.dumps({
        "id": sid, "cwd": os.getcwd(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "messages": _serialize(messages)}, indent=1))
    return path


def _serialize(messages):
    out = []
    for m in messages:
        c = m["content"]
        if isinstance(c, list):
            c = [b if isinstance(b, dict) else b.model_dump() for b in c]
        out.append({"role": m["role"], "content": c})
    return out


def latest_session():
    if not SESSION_DIR.exists():
        return None
    files = sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


# ---------------------------------------------------------------- main -----
def main():
    ap = argparse.ArgumentParser(description="recc-agent — open-source Claude Code clone")
    ap.add_argument("task", nargs="?", help="one-shot task; omit for interactive REPL")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--resume", action="store_true", help="continue the latest session")
    ap.add_argument("--yolo", action="store_true", help="auto-approve all actions (careful)")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(col("Set ANTHROPIC_API_KEY first (use your own key).", "r")); sys.exit(1)
    try:
        from anthropic import Anthropic
    except ImportError:
        print(col("pip install anthropic", "r")); sys.exit(1)

    client = Anthropic()
    perms = {"approved": set(), "yolo": args.yolo, "_read": set()}
    running = {"cost": 0.0, "in": 0, "out": 0}

    messages, sid = [], uuid.uuid4().hex[:12]
    if args.resume and latest_session():
        data = json.loads(latest_session().read_text())
        messages, sid = data["messages"], data["id"]
        print(col(f"resumed session {sid} ({len(messages)} messages)", "g"))

    print(col(f"recc-agent · model={args.model} · session={sid}"
              + (" · YOLO" if args.yolo else ""), "b"))
    print(col("type a task, or 'exit'. ctrl-c to quit.\n", "d"))

    def do(task):
        messages.append({"role": "user", "content": task})
        try:
            agent_turn(client, args.model, messages, perms, running)
        finally:
            save_session(sid, messages)

    if args.task:
        do(args.task)
        print(col(f"\nsession saved: {SESSION_DIR / (sid + '.json')}", "d"))
        return
    while True:
        try:
            task = input(col("› ", "c")).strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if task in ("exit", "quit"):
            break
        if task:
            do(task)
    print(col(f"session saved: {SESSION_DIR / (sid + '.json')}", "d"))


if __name__ == "__main__":
    main()
