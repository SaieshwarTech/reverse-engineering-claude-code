# 6. Subagents, Skills, Slash Commands, MCP

## Subagents (the Task tool)

A subagent is simply **the same agent loop run again** with:
- a fresh, empty context window,
- its own system prompt (from `.claude/agents/<name>.md` frontmatter),
- a possibly restricted tool set and different model,
- one input (the task prompt) and one output (its final message).

Why it matters: a search across 200 files might consume 80k tokens of intermediate reads. Run it in a subagent and the parent pays only for the final answer. Subagents are **context firewalls**. They can also run in parallel and in isolated git worktrees.

Definition file:

```markdown
---
name: code-reviewer
description: Reviews diffs for bugs
tools: Read, Grep, Glob, Bash
model: sonnet
---
You are a meticulous code reviewer…
```

## Skills

A skill is a markdown instruction file (`SKILL.md` + optional resources) loaded into context *on demand* — either when the user types `/name` or when the model decides the skill's description matches the task. This is **progressive disclosure**: instead of a 500k-token system prompt covering everything, capabilities live in files and cost tokens only when used. Slash commands and skills are the same mechanism.

Locations: `~/.claude/skills/` (user), `.claude/skills/` (project), plus plugins.

## MCP (Model Context Protocol)

MCP servers are external processes (stdio or HTTP) that expose tools, resources, and prompts. Claude Code:
1. Reads `.mcp.json` / settings for server configs,
2. Starts/handshakes each server, lists its tools,
3. Registers them as `mcp__server__tool` — identical to built-ins in the loop.

Auth for remote servers uses OAuth. Large tool catalogs are handled by deferring schemas and loading them via ToolSearch only when needed.

## The composition story

These three features are one idea at different scales:

| Mechanism | Adds | Costs context when… |
|-----------|------|---------------------|
| Skill | instructions | invoked |
| MCP | tools | listed (or deferred until searched) |
| Subagent | a whole worker | never (only its final message) |

Understanding this table is understanding how Claude Code scales beyond its context window.
