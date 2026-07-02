# 1. The Big Picture

Claude Code looks like magic from the outside, but architecturally it's four layers:

```
┌─────────────────────────────────────────────┐
│  Terminal UI (React/Ink TUI)                │  input, rendering, permission prompts
├─────────────────────────────────────────────┤
│  Agent Loop (Claude Agent SDK)              │  the while-loop: model ⇄ tools
├─────────────────────────────────────────────┤
│  Tool Layer                                 │  Read, Edit, Bash, Grep, Task, MCP…
├─────────────────────────────────────────────┤
│  Anthropic Messages API                     │  the actual model (streaming)
└─────────────────────────────────────────────┘
```

## Key insight: the model is stateless

Claude Code holds **all state client-side**. Every turn, it sends the *entire* conversation (system prompt + all prior messages + tool results) to the Messages API. The "agent" is just:

1. A carefully engineered system prompt
2. A set of tool JSON schemas
3. A loop that executes the model's tool calls and feeds results back

Nothing agentic runs server-side. This is why context management (chapter 4) is the hardest engineering problem in the whole system.

## The components

- **CLI entrypoint** (`claude`): a Node.js bundle. Parses args, loads settings from `~/.claude/settings.json` and project `.claude/`, starts the TUI.
- **Agent SDK**: the reusable core. Claude Code is essentially `query()` from the SDK plus a terminal UI. If you want to "read Claude Code's source," read the SDK — it's the same loop.
- **Session storage**: every conversation is persisted as JSONL transcripts under `~/.claude/projects/<encoded-cwd>/`. `--resume` and `--continue` just replay these.
- **Settings cascade**: enterprise policy → CLI flags → `.claude/settings.local.json` → `.claude/settings.json` (project) → `~/.claude/settings.json` (user).

## Data flow for one user message

```
user text
  → assemble context (system prompt, CLAUDE.md, settings, history)
  → POST /v1/messages (streaming, with tool schemas)
  → model streams text and/or tool_use blocks
  → for each tool_use: permission check → execute → tool_result
  → POST again with results appended
  → repeat until the model responds with no tool calls
  → render final text
```

That loop is chapter 2.
