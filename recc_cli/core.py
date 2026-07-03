#!/usr/bin/env python3
"""
recc_cli.core — the shared, channel-agnostic engine.

Every channel adapter (Telegram, email, WhatsApp, …) is a thin front door over
this: turn an inbound message into an agent turn, get back text to send. The
agent loop and tools live in recc_cli.agent; this module makes them headless
and safe for unattended (chat/email) use.
"""
import json, re
from . import agent as A


def make_permission(allow_writes):
    """Non-interactive permission for unattended channels (headless ch. 5).

    Read-only tools always run. Mutating tools (write/edit/bash) run only when
    allow_writes is True. Catastrophic commands are ALWAYS blocked.
    """
    def check(name, args):
        if name not in A.MUTATING:
            return True, "read-only"
        if name == "bash":
            for pat in A.DENY_ALWAYS:
                if re.search(pat, args.get("command", "")):
                    return False, f"blocked by safety rule: {pat}"
        if not allow_writes:
            return False, "writes disabled (enable with --allow-writes)"
        return True, "allowed"
    return check


def run_turn(client, model, messages, permission, running, notify=None):
    """Run one agent turn to completion (non-streaming). Returns final text.

    messages : the running conversation (mutated in place)
    permission : callable(name, args) -> (allowed, reason)
    running : dict with a "cost" float, updated as we go
    notify : optional callable(str) for streaming tool activity to the channel
    """
    final_text = []
    while True:
        resp = client.messages.create(model=model, max_tokens=A.MAX_TOKENS,
                                      system=A.system_prompt(), tools=A.TOOLS,
                                      messages=messages)
        u = resp.usage
        pi, pcw, pcr, po = A.price(model)
        running["cost"] = running.get("cost", 0.0) + (
            u.input_tokens * pi
            + getattr(u, "cache_creation_input_tokens", 0) * pcw
            + getattr(u, "cache_read_input_tokens", 0) * pcr
            + u.output_tokens * po) / 1_000_000

        messages.append({"role": "assistant", "content": resp.content})
        calls = [b for b in resp.content if b.type == "tool_use"]
        for b in resp.content:
            if b.type == "text" and b.text.strip():
                final_text.append(b.text.strip())
        if not calls:
            return "\n\n".join(final_text) or "(done)"

        results = []
        for c in calls:
            args = c.input if isinstance(c.input, dict) else json.loads(c.input or "{}")
            ok, reason = permission(c.name, args)
            if notify:
                notify(f"⚙ {c.name} {json.dumps(args)[:120]}"
                       + ("" if ok else f"  ✗ {reason}"))
            if not ok:
                results.append({"type": "tool_result", "tool_use_id": c.id,
                                "content": f"ERROR: {reason}", "is_error": True})
                continue
            out = A.run_tool(c.name, args, {"_read": set()})
            results.append({"type": "tool_result", "tool_use_id": c.id, "content": out})
        messages.append({"role": "user", "content": results})


def get_client():
    """Return an Anthropic client or raise a friendly error."""
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY (your own key).")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise SystemExit("pip install anthropic")
    return Anthropic()
