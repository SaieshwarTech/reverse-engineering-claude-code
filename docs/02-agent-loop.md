# 2. The Agent Loop

Strip away the TUI and Claude Code's core is ~30 lines of logic:

```python
messages = [user_message]

while True:
    response = api.messages.create(
        model="claude-sonnet-5",
        system=SYSTEM_PROMPT,          # chapter 4
        tools=TOOL_SCHEMAS,            # chapter 3
        messages=messages,
        stream=True,
    )
    messages.append(assistant_message(response))

    tool_calls = [b for b in response.content if b.type == "tool_use"]
    if not tool_calls:
        break                          # model is done — final answer

    results = []
    for call in tool_calls:
        if not permitted(call):        # chapter 5
            results.append(denial(call))
            continue
        results.append(execute(call))  # run Bash, read file, etc.

    messages.append(user_message_with(results))   # tool results go back as a *user* message
```

Everything else — permissions, hooks, compaction, subagents — is elaboration on this loop.

## Details that matter in production

**Streaming.** Responses stream via SSE. Text renders as it arrives; tool calls execute only once their JSON block is complete. This is why Claude Code feels responsive despite multi-second model latency.

**Parallel tool calls.** The model can emit several `tool_use` blocks in one response. Read-only tools (Read, Grep, Glob) run concurrently; mutating tools run serially.

**Interruption.** Esc aborts the in-flight request and injects a synthetic "user interrupted" result so the transcript stays consistent — the API requires every `tool_use` to have a matching `tool_result`, even for cancelled or denied calls (the denial/cancellation *is* the result, flagged `is_error: true`).

**Error feeding.** Failed tools aren't retried by the harness. The error text goes back to the model, which decides how to recover. This "let the model see its own errors" principle is the single biggest difference from classic RPA-style automation.

**Turn boundaries.** A "turn" ends when the model replies without tool calls. One user message can trigger dozens of loop iterations — that's what makes it an agent rather than a chatbot.

## Cost & caching

Because the whole conversation is resent every iteration, Claude Code leans hard on **prompt caching**: the system prompt, tool schemas, and stable message prefix are marked as cache breakpoints, cutting cost and latency ~90% on cache hits. Cache TTL is ~5 minutes — one reason long idle pauses feel slower on resume.
