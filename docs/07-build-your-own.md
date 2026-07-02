# 7. Build Your Own (a Claude-Code-style agent in ~200 lines)

The best way to prove you understand the machine is to build a small one. `mini-agent.py` below implements the real loop with four tools. Requires `pip install anthropic` and `ANTHROPIC_API_KEY`.

```python
#!/usr/bin/env python3
"""mini-claude: a minimal Claude-Code-style coding agent."""
import json, os, subprocess, sys
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-5"

SYSTEM = """You are a coding agent working in {cwd}.
Use the tools to inspect and modify files and run commands.
Read a file before editing it. Cite paths as file:line.
When the task is complete, reply with a short summary and no tool calls.""".format(cwd=os.getcwd())

TOOLS = [
    {"name": "read_file", "description": "Read a file with line numbers",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Create or overwrite a file",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace an exact, unique string in a file",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}},
    {"name": "bash", "description": "Run a shell command",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
]

def run_tool(name, args):
    try:
        if name == "read_file":
            lines = open(args["path"]).read().splitlines()
            return "\n".join(f"{i+1}\t{l}" for i, l in enumerate(lines[:2000]))
        if name == "write_file":
            open(args["path"], "w").write(args["content"]); return "written"
        if name == "edit_file":
            src = open(args["path"]).read()
            if src.count(args["old"]) != 1:
                return f"ERROR: old string found {src.count(args['old'])} times; must be exactly 1"
            open(args["path"], "w").write(src.replace(args["old"], args["new"])); return "edited"
        if name == "bash":
            if input(f"  run `{args['command']}`? [y/N] ").lower() != "y":   # the permission system
                return "ERROR: user denied permission"
            r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=120)
            return (r.stdout + r.stderr)[-8000:] or "(no output)"
    except Exception as e:
        return f"ERROR: {e}"

def agent(user_input, messages):
    messages.append({"role": "user", "content": user_input})
    while True:                                             # THE agent loop
        resp = client.messages.create(model=MODEL, max_tokens=8000,
                                      system=SYSTEM, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        calls = [b for b in resp.content if b.type == "tool_use"]
        for b in resp.content:
            if b.type == "text" and b.text.strip(): print(b.text)
        if not calls:
            return
        results = []
        for c in calls:
            print(f"⚙ {c.name} {json.dumps(c.input)[:120]}")
            results.append({"type": "tool_result", "tool_use_id": c.id,
                            "content": str(run_tool(c.name, c.input))})
        messages.append({"role": "user", "content": results})

if __name__ == "__main__":
    history = []
    print("mini-claude — type a task, ctrl-c to quit")
    while True:
        try: agent(input("\n> "), history)
        except KeyboardInterrupt: sys.exit(0)
```

## What you just built vs. the real thing

| Feature | mini-claude | Claude Code |
|---------|-------------|-------------|
| Agent loop | ✅ identical shape | ✅ |
| Read-before-edit safety | partial (unique-match edit) | enforced read tracking |
| Permissions | y/N prompt on bash | rule engine + modes + sandbox (ch. 5) |
| Context management | none — history grows forever | caching, compaction, subagents (ch. 4/6) |
| Streaming, TUI, sessions, hooks, MCP, skills | ❌ | ✅ |

Each ❌ row maps to a chapter of this guide — implement them one by one and you'll have rebuilt the product. That's the whole point: **there is no secret**. A production coding agent is a great model + a tight loop + years of context-engineering and safety polish.
