# Reverse Engineering Claude Code

> **How Claude Code actually works — the agent loop, tools, prompts, permissions, memory, and context engine — explained from the inside out, so you can understand it, extend it, or build your own.**

Official docs tell you *what* Claude Code does. This project explains *how* — the machinery under the hood — for developers, researchers, and anyone building AI coding agents.

## Why this exists

Claude Code ships as an obfuscated bundle, but its behavior, its open-source foundation (the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-typescript)), and its API traffic are all observable. By studying these, we can reconstruct a complete picture of how a production-grade coding agent is engineered — and people need that picture, because the agent loop pattern is becoming the foundation of modern dev tooling.

## The Guide

| # | Chapter | What you'll learn |
|---|---------|-------------------|
| 1 | [The Big Picture](docs/01-architecture.md) | Overall architecture: CLI → agent loop → API → tools |
| 2 | [The Agent Loop](docs/02-agent-loop.md) | The core while-loop that makes an LLM into an agent |
| 3 | [The Tool System](docs/03-tools.md) | Every built-in tool, its schema, and why it's designed that way |
| 4 | [System Prompts & Context](docs/04-prompts-and-context.md) | How the context window is assembled, CLAUDE.md, compaction |
| 5 | [Permissions & Hooks](docs/05-permissions-and-hooks.md) | The security model: permission modes, allowlists, hook lifecycle |
| 6 | [Subagents & Skills](docs/06-subagents-and-skills.md) | Task delegation, skills, slash commands, MCP |
| 7 | [Build Your Own](docs/07-build-your-own.md) | A minimal Claude-Code-style agent in ~200 lines |

## How to observe Claude Code yourself

- **Read the SDK**: `npm i @anthropic-ai/claude-agent-sdk` — the agent engine is right there.
- **Intercept traffic**: `ANTHROPIC_BASE_URL` pointed at a local proxy (e.g. mitmproxy) shows every request: system prompt, tool schemas, messages.
- **Inspect state on disk**: `~/.claude/` — settings, session transcripts (`projects/*/`), todos, shell snapshots.
- **Verbose mode**: `claude --verbose` and `--debug` expose internal decisions.

## Research sources & credits

- [anthropics/claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) — the open-source engine
- [bgauryy/open-docs](https://github.com/bgauryy/open-docs) — excellent independent deep-dive docs on AI CLI internals (kept locally as research material; not reproduced here)
- Official [Claude Code docs](https://code.claude.com/docs)

## Disclaimer

Educational and research purposes. All content here is original analysis based on public source code, public documentation, and observable behavior. "Claude" and "Claude Code" are trademarks of Anthropic; this is an unofficial, independent project.
