# Contributing

Thanks for wanting to help. This project maps how AI coding agents work and ships a small open-source clone. Contributions of all sizes are welcome.

## Ways to contribute

- **Docs** — new chapters, corrections, clearer explanations, diagrams.
- **The agent** (`recc_cli/agent.py`) — features that mirror real Claude Code: subagents, prompt caching, context compaction, a richer TUI, MCP client, hooks.
- **The inspector** (`recc_cli/inspector.py`) — better cost analytics, session viewers, full SSE decoding in the proxy.
- **Other agents** — apply the [methodology](docs/10-methodology.md) to Codex CLI, Gemini CLI, OpenCode, etc.

## Ground rules

1. **Ethics first.** This is about understanding and interoperability, never bypassing billing or authentication. PRs that do the latter will be closed.
2. **Cite sources.** Link official docs, SDK source, or your own observations. Don't republish unlicensed content — link to it.
3. **Verify claims.** Agent behavior changes often. Say what you checked and how (proxy capture, transcript, version). Date findings where useful.
4. **Match the style.** Plain, precise prose. Keep code dependency-light and readable.

## Dev setup

```bash
git clone https://github.com/SaieshwarTech/reverse-engineering-claude-code
cd reverse-engineering-claude-code
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...   # your own key, for running the agent
python3 -m py_compile recc_cli/*.py   # quick sanity check
```

## Pull requests

1. Fork, then branch: `git checkout -b feature/my-thing`.
2. Make focused commits with clear messages.
3. Open a PR describing **what changed** and **what you verified**.

## Good first issues

- Add an `asciinema`/GIF demo to the README.
- Implement `--print`/JSON output mode for `recc-agent` (scriptable, non-interactive).
- Add a `recc export` command that turns a session `.jsonl` into readable Markdown.
- Write chapter 12: the session/transcript format as a formal spec.

New contributors are credited automatically in the README's contributors section.
