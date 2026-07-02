# `recc` — Reverse-Engineer Claude Code CLI

A small, dependency-light inspector for the internals this guide describes. It runs
against **your own account with your own API key** and only *observes* usage — it
never bypasses billing or authentication.

## Install

```bash
cd tool
pip install -r requirements.txt          # only needs `anthropic` (for exact token counts)
python3 recc.py --help
# optional: make it a command
chmod +x recc.py && ln -s "$PWD/recc.py" ~/.local/bin/recc
```

## Commands

### `recc tokens <text|file>`
Count tokens in a string or file — a local `chars/4` estimate, plus the exact count
from the API's `count_tokens` endpoint if `ANTHROPIC_API_KEY` is set.

```bash
recc tokens "explain quicksort"
recc tokens ./big_prompt.md
```

### `recc cost <session.jsonl ...>`
Reconstruct what a session cost by summing the `usage` fields in its transcript, priced
per-model. Shows input / cache-write / cache-read / output breakdown and cache hit rate.

```bash
recc cost ~/.claude/projects/*/*.jsonl
```
> Prices live in the `PRICING` dict at the top of `recc.py` — update them from
> [anthropic.com/pricing](https://www.anthropic.com/pricing) so numbers stay accurate.

### `recc sessions [--limit N]`
List local Claude Code sessions (project, session id, line count, size), newest first.

### `recc inspect <session.jsonl>`
Pretty-print a transcript: user/assistant turns, tool calls, tool results, and per-message
token usage — a readable view of the JSONL format described in chapter 9.

### `recc proxy [--port 8080]`
Run a logging reverse-proxy in front of the Anthropic API. Point Claude Code at it and
watch each request's shape (model, tool count, message count, system size):

```bash
python3 recc.py proxy --port 8080
# in another shell:
export ANTHROPIC_BASE_URL=http://127.0.0.1:8080
claude
```
For full streaming/SSE body inspection use [mitmproxy](https://mitmproxy.org) as described
in chapter 8; `recc proxy` is the zero-dependency quick look.

## Ethics

This tool exists to help you **understand and optimize your own usage** — see where tokens
and money go, learn the transcript format, watch the agent loop on the wire. It will not,
and is not intended to, help anyone use Claude without paying for it.
