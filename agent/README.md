# `recc-agent` — an open-source Claude Code clone

A real, runnable terminal coding agent in a single file (~350 lines). It's the guide's
chapter 7 mini-agent grown into something you can actually use — and a reference for
*how the real thing is built*.

> Uses the official Anthropic API with **your own key**. It does not bypass billing.

## What it has

| Feature | Where in the guide |
|---------|--------------------|
| The agent loop (model ⇄ tools until done) | ch. 2 |
| Tools: `read_file`, `write_file`, `edit_file`, `bash`, `grep`, `glob` | ch. 3 |
| Read-before-edit + unique-string edits with diffs | ch. 3 |
| Permission system: allow / always / deny, hard-blocked dangerous commands | ch. 5 |
| Streaming output (text renders as it arrives) | ch. 2, 8 |
| `CLAUDE.md` context (user + project) | ch. 4 |
| Live token + cost meter | ch. 8 |
| Session save + `--resume` | ch. 9 |

## Install & run

```bash
cd agent
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...     # your own key

python3 recc_agent.py "add a --version flag to cli.py"   # one-shot
python3 recc_agent.py                    # interactive REPL
python3 recc_agent.py --resume           # continue the last session
python3 recc_agent.py --model claude-haiku-4-5   # cheaper model
python3 recc_agent.py --yolo             # auto-approve everything (careful!)
```

## What a run looks like

```
recc-agent · model=claude-sonnet-5 · session=8f2a1c9d4e01
type a task, or 'exit'. ctrl-c to quit.

› fix the failing test
I'll run the tests first to see what's failing.
  ⚙ bash {"command": "npm test 2>&1 | tail -30"}
  ⧗ tokens in≈18,204 out≈96  cost≈$0.0021
The assertion expects 42 but gets 41 — an off-by-one in sum(). Let me look.
  ⚙ read_file {"path": "src/sum.js"}
  ⚙ edit_file {"path": "src/sum.js"}
  Edited src/sum.js
  ⚠ bash wants to: npm test
    allow? [y]es / [a]lways / [N]o: a
  ⚙ bash {"command": "npm test"}
All tests pass now. The bug was `i < n` should have been `i <= n` in sum().
```

## How it maps to the real Claude Code

This is the honest skeleton. The production tool adds: a rich TUI, sandboxed Bash,
subagents, MCP, skills/slash-commands, hooks, prompt caching, and context compaction —
each of which is a chapter in [`../docs`](../docs). Read a chapter, then add that feature
here; that's the fastest way to truly understand the architecture.

## Safety & scope

- Mutating actions (`write_file`, `edit_file`, `bash`) prompt for permission unless `--yolo`.
- A few catastrophic commands (`rm -rf /`, fork bombs, `mkfs`, `dd` to devices) are hard-blocked.
- It still runs real commands on your machine — review what it does, especially with `--yolo`.
- It is **not** a way to use Claude without paying; it calls the official API with your key.
