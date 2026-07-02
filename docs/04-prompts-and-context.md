# 4. System Prompts & Context Engineering

The context window is Claude Code's scarcest resource (~200k tokens). Everything about the product is shaped by how it fills and preserves that window.

## What's in the context, top to bottom

1. **System prompt** — identity ("You are Claude Code…"), safety policy, tone/output rules, tool-usage doctrine (prefer dedicated tools over shell, parallel calls, cite `file:line`), git/PR conventions, environment info (cwd, OS, git status, model id, date).
2. **Tool schemas** — every tool's JSON schema (thousands of tokens; a big reason for deferred tool loading).
3. **CLAUDE.md files** — user-level (`~/.claude/CLAUDE.md`) then project-level, injected as instructions that *override defaults*. This is the product's "memory you control."
4. **Conversation history** — messages, tool calls, tool results.
5. **System reminders** — `<system-reminder>` blocks injected by the harness mid-conversation (file-change notices, task-list nudges, skill lists). Cheap way to steer without editing the system prompt.

You can verify all of this yourself by proxying the API (`ANTHROPIC_BASE_URL` → mitmproxy).

## Compaction: surviving long sessions

When history approaches the window limit, Claude Code **compacts**: it asks the model to write a detailed summary of the conversation (state, decisions, open work, key file paths), then starts a fresh window seeded with that summary plus the most recent messages. Manual trigger: `/compact`. The transcript on disk keeps everything; only the *live window* shrinks.

Related tricks:
- **Micro-compaction** of old large tool results (a 5,000-line Read from an hour ago becomes a stub).
- **Subagents** (ch. 6) as *pre-emptive* compaction: burn tokens in a child window, return one message.

## CLAUDE.md and the memory hierarchy

```
~/.claude/CLAUDE.md          # user: applies everywhere
<repo>/CLAUDE.md             # project: committed, shared with team
<repo>/.claude/CLAUDE.local.md  # personal, gitignored
<subdir>/CLAUDE.md           # loaded when working in that subtree
```

These are plain markdown, loaded fresh each session. Newer builds add **auto-memory**: a directory of small fact-files plus a `MEMORY.md` index that's loaded each session — persistent memory implemented as nothing more than files plus conventions.

## The lesson

There is no hidden vector database, no server-side state, no magic. Claude Code's "intelligence" beyond the raw model comes from disciplined *context engineering*: what to put in, what to keep out, what to summarize, and when.
