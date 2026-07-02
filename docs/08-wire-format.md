# 8. On the Wire — What Claude Code Actually Sends

The single most instructive reverse-engineering exercise: put a proxy between Claude Code and the API and read the traffic yourself.

## Setup (10 minutes)

```bash
pip install mitmproxy
mitmweb --listen-port 8080          # opens a web UI at 127.0.0.1:8081

# in another terminal:
export ANTHROPIC_BASE_URL=http://127.0.0.1:8080
claude
```

(If TLS gets in the way, use mitmproxy in reverse-proxy mode: `mitmweb --mode reverse:https://api.anthropic.com --listen-port 8080`.)

Every request Claude Code makes now appears in the UI, fully readable.

## Anatomy of a request

`POST /v1/messages` with a body shaped like:

```jsonc
{
  "model": "claude-sonnet-5",
  "max_tokens": 32000,
  "stream": true,
  "system": [
    { "type": "text", "text": "You are Claude Code, Anthropic's official CLI…",
      "cache_control": { "type": "ephemeral" } },     // ← cache breakpoint
    { "type": "text", "text": "<env>Working directory: /home/you/proj…</env>" }
  ],
  "tools": [
    { "name": "Bash",  "description": "Executes a bash command…", "input_schema": { /* JSON Schema */ } },
    { "name": "Read",  "…": "…" }
    // …one entry per tool, thousands of tokens total
  ],
  "messages": [
    { "role": "user", "content": "fix the failing test" },
    { "role": "assistant", "content": [
        { "type": "text", "text": "Let me look at the test first." },
        { "type": "tool_use", "id": "toolu_01A…", "name": "Bash",
          "input": { "command": "npm test 2>&1 | tail -30" } }
    ]},
    { "role": "user", "content": [
        { "type": "tool_result", "tool_use_id": "toolu_01A…",
          "content": "FAIL src/auth.test.ts …" }
    ]}
    // …the ENTIRE conversation, every iteration, every time
  ]
}
```

Things to notice while reading real traffic:

- **The full history is resent on every loop iteration.** Statelessness made visible.
- **`cache_control` breakpoints** sit after the system prompt, after tools, and near the end of the message list. Responses report `cache_read_input_tokens` — watch it: on a warm loop, 95%+ of input tokens are cache hits.
- **`<system-reminder>` blocks** appear inside user messages — that's how the harness injects notices (file changed on disk, CLAUDE.md contents, task-list nudges) without a separate role.
- **Tool results are `role: "user"`.** The API has no "tool" role; results are user-content blocks with a `tool_use_id` linking them back.
- **Interleaved thinking**: with extended thinking enabled you'll see `thinking` blocks in responses that are re-sent (signed) on subsequent requests.
- **Streaming** responses are SSE: `message_start`, `content_block_delta` (text or `input_json_delta` for tool args), `message_delta` with `stop_reason: "tool_use"` or `"end_turn"` — the loop's exit condition, on the wire.

## Other endpoints you'll spot

- `/v1/messages/count_tokens` — pre-flight sizing before compaction decisions.
- Small/fast-model calls (Haiku) for cheap side tasks: conversation title, bash-command description, web-page summarization.

## The takeaway

Everything in chapters 1–6 is verifiable in an afternoon with a proxy. No leaked internals required — the "secret sauce" travels in plaintext JSON on every request you make.
