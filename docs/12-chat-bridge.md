# 12. The Chat Bridge — an OpenClaw-style Assistant

[OpenClaw](https://openclaw.ai/) popularized a pattern: a Claude-powered agent that
lives on your machine but you talk to it from a **chat app** (Telegram, WhatsApp, Discord…),
with system access and memory. Architecturally that's not a new agent — it's the *same
agent loop* (ch. 2) with a different front door.

`recc-bridge` implements that front door for Telegram, in stdlib only.

## The idea

```
Telegram message ──► getUpdates (long poll) ──► agent loop (ch. 2) ──► sendMessage reply
                                                     │
                                          same tools as recc-agent (ch. 3)
```

The terminal REPL and the chat bridge are two UIs over one engine. Swap Telegram's
`getUpdates`/`sendMessage` for Discord's gateway or a WhatsApp provider and nothing else
changes — that interchangeability is the whole point of keeping the loop UI-agnostic.

## Run it

```bash
# 1. Create a bot with @BotFather, copy the token.
export TELEGRAM_BOT_TOKEN=123456:ABC...
export ANTHROPIC_API_KEY=sk-ant-...

recc-bridge                      # read-only assistant (safe default)
recc-bridge --allow-writes       # let it edit files / run shell (careful!)
recc-bridge --allow-chat 12345   # restrict to your chat id(s)
recc-bridge --verbose            # stream tool activity into the chat
```

Message the bot; it runs the loop and replies. `/new` resets context, `/start` shows your
chat id (use it with `--allow-chat`).

## Safety model (why headless changes the rules)

In the terminal, risky actions pause for a `[y/a/N]` prompt (ch. 5). Over chat there's no
one at the keyboard, so recc-bridge is **safe by default**:

| Action | Default | With `--allow-writes` |
|--------|---------|-----------------------|
| Read / Grep / Glob | ✅ runs | ✅ runs |
| Write / Edit / Bash | ❌ denied | ✅ runs |
| `rm -rf /`, fork bombs, `mkfs`, `dd` to device | ❌ always blocked | ❌ always blocked |

Plus `--allow-chat` allowlists specific chat ids so a leaked bot link can't let strangers
drive your machine. Treat `--allow-writes` on a public-reachable bot the way you'd treat
handing someone an SSH session — because that's what it is.

## What OpenClaw adds on top

The real product goes further, and each piece is a natural extension of this bridge:

- **More channels** — WhatsApp, Discord, Slack, Signal, iMessage (same loop, new adapter).
- **Persistent memory** — a fact store the agent reads/writes across sessions (ch. 4's
  memory hierarchy, made durable).
- **Skills/plugins** — on-demand capabilities (ch. 6), including ones the agent writes itself.
- **Native companions** — desktop/mobile apps for OS-level control.

Build them by adding adapters and tools to the engine you already have — not by starting over.
