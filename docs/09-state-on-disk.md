# 9. State on Disk — Dissecting `~/.claude/`

Claude Code keeps all of its state in plain files. Reading them is the second great reverse-engineering technique (after proxying, ch. 8).

## The directory map

```
~/.claude/
├── settings.json            # user-level settings (permissions, env, hooks, model)
├── CLAUDE.md                # user-level instructions, injected every session
├── projects/
│   └── -home-you-myproj/    # one dir per project (cwd, slashes → dashes)
│       ├── <session-uuid>.jsonl    # full transcript of one session
│       └── memory/          # auto-memory: MEMORY.md index + fact files
├── todos/                   # task-list state per session (JSON)
├── shell-snapshots/         # captured shell env so Bash inherits your rc files
├── skills/                  # user-installed skills
├── agents/                  # user-defined subagents
├── plugins/                 # installed plugins (skills+agents+hooks bundles)
└── statsig / telemetry caches, update state, etc.

<project>/.claude/
├── settings.json            # shared project settings (commit this)
├── settings.local.json      # personal overrides + learned "don't ask again" rules
├── agents/  skills/  hooks/
└── CLAUDE.md lives at the repo root (or .claude/)
```

## The transcript format (JSONL)

Each session file is one JSON object per line — an append-only event log:

```jsonc
{"type":"user","uuid":"…","parentUuid":null,"sessionId":"…","cwd":"/home/you/myproj",
 "message":{"role":"user","content":"fix the bug"},"timestamp":"2026-07-03T10:12:01.000Z"}

{"type":"assistant","uuid":"…","parentUuid":"…",
 "message":{"role":"assistant","model":"claude-sonnet-5",
   "content":[{"type":"tool_use","id":"toolu_…","name":"Read","input":{"file_path":"src/app.ts"}}],
   "usage":{"input_tokens":4,"cache_read_input_tokens":18210,"output_tokens":92}}}

{"type":"user","uuid":"…","parentUuid":"…","toolUseResult":{…},
 "message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_…","content":"…"}]}}
```

Key observations:

- **`parentUuid` chains** make the transcript a tree, not a list — this is how "rewind / edit an earlier message" branches the conversation without losing the old path.
- **`usage` per assistant message** lets you reconstruct exactly what every step cost.
- `--resume` shows sessions by reading these files; `--continue` picks the latest. Replaying a transcript = rebuilding the `messages` array and continuing the loop.
- Compaction appears in the log as a summary entry; the pre-compaction history remains on disk.

## Practical uses

- **Cost auditing**: sum `usage` across a session file.
- **Prompt archaeology**: grep transcripts for `system-reminder` to see everything the harness injected.
- **Building tooling**: session viewers, analytics, exporters — the format is stable enough to script against (several open-source viewers already do).
- **Debugging weird behavior**: when the agent "remembered" something odd, the transcript shows exactly which injected context caused it.
