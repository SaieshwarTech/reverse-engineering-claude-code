# 11. Glossary & Quick Reference

## Glossary

**Agent loop** — the while-loop that sends context to the model, executes returned tool calls, feeds results back, and repeats until the model stops calling tools. The thing that turns an LLM into an agent. (Ch. 2)

**Compaction** — summarizing the conversation into a shorter form when it nears the context limit, then continuing in a fresh window. (Ch. 4)

**Context window** — the token budget (~200k) holding the system prompt, tools, memory, and history for a single request. The scarcest resource.

**CLAUDE.md** — markdown instruction files (user/project/local) injected into context to override default behavior. (Ch. 4)

**Hook** — a shell command the harness runs at a lifecycle event (PreToolUse, PostToolUse, Stop, …) to intercept or react to agent actions deterministically. (Ch. 5)

**Harness** — the client program (Claude Code) wrapping the model: UI, loop, tools, permissions. As opposed to the model itself, which is stateless.

**MCP (Model Context Protocol)** — a standard for external servers to expose tools/resources/prompts to the agent. Tools appear as `mcp__server__tool`. (Ch. 6)

**Permission mode** — default / acceptEdits / plan / bypassPermissions: how aggressively actions are auto-approved. (Ch. 5)

**Prompt caching** — marking stable prefixes so the API charges ~10% for cache hits; why resending full history each turn is affordable. (Ch. 2, 8)

**Skill** — an on-demand markdown instruction file loaded when invoked or matched, implementing progressive disclosure. (Ch. 6)

**Subagent** — a nested agent loop with its own fresh context, returning only a final message; used as a context firewall. (Ch. 6)

**System prompt** — the top-of-context instructions defining the agent's identity, rules, and tool doctrine. (Ch. 4)

**System reminder** — a `<system-reminder>` block injected into a user message by the harness to steer the model mid-session. (Ch. 4, 8)

**tool_use / tool_result** — the API content blocks representing a model's call and the client's returned output (results carry `role: user`). (Ch. 8)

**Transcript** — the append-only JSONL log of a session under `~/.claude/projects/`; a UUID tree enabling resume and rewind. (Ch. 9)

## Cheat sheet: verify any claim in this guide

| Question | How to check |
|----------|--------------|
| What's in the system prompt? | Proxy the API (ch. 8), read `system[]` |
| What tools exist + schemas? | Proxy, read `tools[]`; or `/help` |
| How much did a session cost? | Sum `usage` in the `.jsonl` (ch. 9) |
| What did the harness inject? | grep transcript for `system-reminder` |
| Does a hook fire when I think? | Add a logging `PreToolUse` hook (ch. 5) |
| Is context being cached? | Watch `cache_read_input_tokens` in responses |
| How does resume work? | Read the session `.jsonl`, note `parentUuid` chains |

## Further reading

- Anthropic — [Claude Code docs](https://code.claude.com/docs) and [Agent SDK](https://github.com/anthropics/claude-agent-sdk-typescript)
- Anthropic engineering blog — "Building effective agents", context-engineering and prompt-caching posts
- [bgauryy/open-docs](https://github.com/bgauryy/open-docs) — independent deep-dive docs on AI CLI internals
- Model Context Protocol — [modelcontextprotocol.io](https://modelcontextprotocol.io)
