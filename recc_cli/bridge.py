#!/usr/bin/env python3
"""
recc-bridge — drive recc-agent from a chat app (OpenClaw-style).

Connects your local coding agent to Telegram so you can message it from your
phone. Same agent loop and tools as recc-agent (ch. 2/3), but headless: no
interactive permission prompts, so it is SAFE BY DEFAULT — read-only tools run
freely; anything that writes files or runs shell commands is denied unless you
opt in with --allow-writes, and catastrophic commands are always hard-blocked.

Stdlib only (urllib) — no extra dependencies beyond `anthropic`.

Setup:
    1. Create a bot with @BotFather on Telegram, copy its token.
    2. export TELEGRAM_BOT_TOKEN=123456:ABC...
       export ANTHROPIC_API_KEY=sk-ant-...
    3. recc-bridge                     # read-only assistant (safe)
       recc-bridge --allow-writes      # let it edit files / run shell (careful!)
       recc-bridge --allow-chat 12345  # restrict to specific chat id(s)

Message your bot; it replies with the agent's answer. Send /new to reset context.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

from . import agent as A       # tools, prompts, pricing, defaults
from . import core             # shared headless engine


def tg(token, method, **params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.loads(r.read())


def send(token, chat_id, text):
    # Telegram caps messages at 4096 chars; chunk if needed.
    for i in range(0, len(text) or 1, 3900):
        tg(token, "sendMessage", chat_id=chat_id, text=text[i:i + 3900] or "…")


def main():
    ap = argparse.ArgumentParser(description="recc-bridge — chat-app bridge for recc-agent")
    ap.add_argument("--model", default=A.DEFAULT_MODEL)
    ap.add_argument("--allow-writes", action="store_true",
                    help="permit file edits and shell commands (off by default)")
    ap.add_argument("--allow-chat", action="append", default=[],
                    help="restrict to these Telegram chat id(s); repeatable")
    ap.add_argument("--verbose", action="store_true", help="stream tool activity to the chat")
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN (create a bot via @BotFather).", file=sys.stderr); sys.exit(1)
    client = core.get_client()
    permission = core.make_permission(args.allow_writes)
    allow = set(str(c) for c in args.allow_chat)
    me = tg(token, "getMe").get("result", {}).get("username", "bot")
    mode = "read+write" if args.allow_writes else "read-only (safe)"
    print(f"recc-bridge live as @{me} · model={args.model} · mode={mode}"
          + (f" · chats={sorted(allow)}" if allow else " · all chats"))
    if args.allow_writes:
        print("⚠  --allow-writes is ON: the agent can edit files and run shell commands.")

    convos, running, offset = {}, {"cost": 0.0}, None
    while True:
        try:
            upd = tg(token, "getUpdates", timeout=60, **({"offset": offset} if offset else {}))
        except Exception as e:
            print("poll error:", e); time.sleep(3); continue
        for u in upd.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            text = (msg.get("text") or "").strip()
            chat_id = str((msg.get("chat") or {}).get("id", ""))
            if not text or not chat_id:
                continue
            if allow and chat_id not in allow:
                send(token, chat_id, "This bot is restricted. Your chat id is not allowed.")
                continue
            if text in ("/new", "/reset"):
                convos.pop(chat_id, None)
                send(token, chat_id, "Context cleared. Fresh start.")
                continue
            if text == "/start":
                send(token, chat_id, f"recc-bridge here (mode: {mode}). "
                                     f"Send me a task. /new resets context.\n"
                                     f"Your chat id: {chat_id}")
                continue

            messages = convos.setdefault(chat_id, [])
            messages.append({"role": "user", "content": text})
            tg(token, "sendChatAction", chat_id=chat_id, action="typing")
            notify = (lambda t: send(token, chat_id, t)) if args.verbose else None
            try:
                reply = core.run_turn(client, args.model, messages,
                                      permission, running, notify)
            except Exception as e:
                reply = f"error: {type(e).__name__}: {e}"
            send(token, chat_id, reply or "(done)")
            print(f"[{datetime.now(timezone.utc):%H:%M:%S}] chat {chat_id} · "
                  f"total cost≈${running['cost']:.4f}")


if __name__ == "__main__":
    main()
