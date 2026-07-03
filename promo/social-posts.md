# Social copy for reverse-engineering-claude-code

Repo: https://github.com/SaieshwarTech/reverse-engineering-claude-code

Copy-paste and post yourself — these are drafts, not auto-published anywhere.
Swap in a screenshot of the README's Mermaid diagram or the `recc-agent` terminal
mockup wherever "[image]" is noted; visual posts get meaningfully more reach.

---

## LinkedIn

[image: the architecture diagram or the recc-agent terminal screenshot]

I spent the last few days doing something I'd been curious about for a while:
figuring out exactly how Claude Code (and coding agents like it) actually work
under the hood — then building an open-source clone to prove I understood it.

The result is "Reverse Engineering Claude Code" — a 13-chapter guide plus working
code, covering:

→ The agent loop — the surprisingly simple while-loop that turns an LLM into an agent
→ The tool system — how Read/Edit/Bash/Grep are designed so the model can't blindly clobber files
→ Context engineering — system prompts, CLAUDE.md, compaction, prompt caching
→ The permission model — how an agent with shell access stays safe
→ How to observe any of this yourself — proxy the API, read the session logs on disk

And then I built recc-agent: an open-source terminal coding agent implementing all
of it — plus recc-bridge/recc-mail/recc-whatsapp, so you can message your own
coding agent from Telegram, Gmail, or WhatsApp (the same pattern popularized by
tools like OpenClaw), all running against your own API key.

If you're building with LLM agents, or just curious how the "magic" works, this
is the deep dive I wish I'd had starting out.

Repo: https://github.com/SaieshwarTech/reverse-engineering-claude-code

#AI #ClaudeCode #LLM #OpenSource #AIAgents #DeveloperTools

---

## X / Twitter (thread)

**1/**
How does Claude Code actually work?

I reverse-engineered it — the agent loop, tool design, context engineering,
permission model — and built an open-source clone to prove it.

13 chapters + working code. 🧵

**2/**
The core insight: there's no magic. The model is stateless. Every single turn,
the *entire* conversation gets resent — system prompt, tool schemas, full history.

The "agent" is just a loop:
assemble context → call model → run tool calls → feed results back → repeat

**3/**
The tool design is the clever part. Edit requires the model to match an EXACT,
UNIQUE string before it can change a file. That one constraint eliminates most
hallucinated-edit failures — no fuzzy matching needed.

**4/**
You can verify all of this yourself in an afternoon:
- proxy the API and read the raw request/response JSON
- read the session transcripts in ~/.claude/ (plain JSONL)
- add a hook that logs every tool call

No leaked internals required. It's observable.

**5/**
So I built recc-agent — an open source clone with the real agent loop, a full
tool layer, a permission system, streaming, and session resume, in one file.

Then recc-bridge/recc-mail/recc-whatsapp: message your own coding agent from
Telegram, Gmail, or WhatsApp. Same pattern as OpenClaw, your own API key.

**6/**
Repo (guide + code): https://github.com/SaieshwarTech/reverse-engineering-claude-code

If you build with LLM agents or just want to understand how they're actually
engineered, this is the whole map.

---

## Reddit — r/ClaudeAI or r/LocalLLaMA (self post)

**Title:** I reverse-engineered how Claude Code works and built an open-source clone (with Telegram/WhatsApp/email bridges)

Body:

I got curious about what's actually happening under the hood of Claude Code —
not the marketing description, the actual mechanics — so I spent a few days
digging in via three techniques: proxying the API traffic, reading the session
transcripts it leaves on disk, and reading the (published) Claude Agent SDK
that it's built on.

Wrote it all up as a 13-chapter guide, then built an open-source clone
(`recc-agent`) to prove the understanding holds up:

- the agent loop (the while-loop that turns an LLM into an agent)
- the tool system (Read/Write/Edit/Bash/Grep/Glob, and *why* Edit requires an
  exact unique string match)
- context engineering — CLAUDE.md, compaction, prompt caching
- the permission model — how it's safe(ish) to give a model shell access
- the actual JSONL transcript format claude code writes to ~/.claude/

Then, since a few people asked "can I message it from my phone" — added
recc-bridge / recc-mail / recc-whatsapp, so you can talk to your own coding
agent over Telegram, Gmail, or WhatsApp. Same idea as OpenClaw, but here it's
the fully open, from-scratch version, using your own Anthropic API key (it's
explicitly *not* a way to use Claude without paying — that's a different,
much less interesting problem).

Repo: https://github.com/SaieshwarTech/reverse-engineering-claude-code

Happy to answer questions about any of the internals — proxying setup, the
transcript format, the permission design, whatever.

---

## Hacker News (Show HN)

**Title:** Show HN: Reverse-engineering Claude Code, with a working open-source clone

Body:

I wanted to understand exactly how Claude Code (and agentic coding CLIs in
general) work — not at a marketing level, at a "what's in the actual API
request" level. Three techniques got me there: proxying the Anthropic API
traffic, reading the session transcripts Claude Code writes to disk
(~/.claude/, plain JSONL), and reading the published Claude Agent SDK source.

Wrote up 13 chapters covering the agent loop, tool design (the Edit tool's
"exact unique string" constraint is a small design choice that eliminates a
whole class of failures), context engineering (CLAUDE.md, compaction, prompt
caching), and the permission/hook model that makes it reasonably safe to give
a model shell access.

Then built `recc-agent`, an open-source terminal coding agent implementing
the same architecture, plus three chat bridges (Telegram, Gmail/IMAP,
WhatsApp Cloud API) so you can talk to your own agent from a phone — same
pattern as OpenClaw. Runs against your own Anthropic key; explicitly not a
way to bypass billing.

Repo: https://github.com/SaieshwarTech/reverse-engineering-claude-code

Would appreciate feedback, especially from anyone who's built similar agent
loops or has corrections on the internals.

---

## Dev.to / Hashnode (article intro — expand into a full post if wanted)

**Title:** How Claude Code Actually Works: A Reverse-Engineering Deep Dive

Official docs tell you what an AI coding agent does. They rarely tell you how
it's built. So I spent a few days finding out — proxying API traffic, reading
on-disk session logs, and studying the open-source Agent SDK Claude Code sits
on — then wrote up everything as a 13-chapter guide and built a working
open-source clone to validate it.

[continue with chapter 1 content or a summary + link to the repo]

Full guide + code: https://github.com/SaieshwarTech/reverse-engineering-claude-code
