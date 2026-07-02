# 10. Methodology — How to Reverse Engineer an AI Agent (Legally)

This chapter generalizes the techniques used throughout the guide, so you can apply them to *any* coding agent (Codex CLI, Gemini CLI, Cursor, …).

## The five techniques, cheapest first

### 1. Read the open parts
Most "closed" agents sit on open foundations. Claude Code's engine is the published Claude Agent SDK; its docs, changelogs, and `--help` output are official disclosures. Always exhaust these first — half of what people call "hidden" is just under-documented.

### 2. Inspect state on disk
Config dirs, session logs, caches (`~/.claude/`, `~/.codex/`, `~/.gemini/`). File formats reveal data models, and data models reveal architecture. (Chapter 9.)

### 3. Intercept the API traffic
A proxy shows the complete prompt, tool schemas, and loop mechanics — the agent's entire "mind" travels in each request. (Chapter 8.) For agents that pin certificates, `ANTHROPIC_BASE_URL`-style env overrides usually bypass the need.

### 4. Probe behaviorally
Treat the agent as a black box and run experiments:
- Ask it to describe its tools and instructions (compare against wire capture for honesty).
- Feed edge cases: huge files, binary files, denied permissions, network failures — error messages leak implementation details.
- Diff behavior across versions and flags (`--verbose`, `--debug`).

### 5. Read the bundle (last resort)
The shipped JS bundle is minified but not encrypted. Pretty-print it and search for string literals — system prompt fragments, tool names, error messages are all findable. Tedious and version-fragile; techniques 1–4 usually answer the question first.

## Ground rules

- **Stay legal & ethical**: observe your own client on your own machine; don't probe Anthropic's servers, evade rate limits, or violate the ToS provisions on misuse. Interoperability research on software you legitimately run is the classic protected case, but read the terms yourself.
- **Respect other people's work**: cite sources; don't republish unlicensed content wholesale (this repo links to research material instead of copying it).
- **Verify, don't assume**: agent behavior changes weekly. Every claim in this guide is checkable with techniques 1–4 — recheck before relying on it.
- **Date your findings**: "as of v2.x" beats timeless-sounding claims that rot silently.

## Suggested first lab session (1 evening)

1. `mitmweb` + `ANTHROPIC_BASE_URL`, run one small task, read the full request. (30 min)
2. Open the session `.jsonl`, match each line to the traffic you saw. (30 min)
3. Add a `PreToolUse` hook that logs every tool call to a file; compare with both. (30 min)
4. Build the ch. 7 mini-agent and run the same task on it. (60 min)

After that evening you will understand coding agents better than 99% of their users.
