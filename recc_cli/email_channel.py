#!/usr/bin/env python3
"""
recc-mail — drive recc-agent by email (Gmail/any IMAP+SMTP), OpenClaw-style.

Polls an inbox for unread mail, runs each message through the agent loop, and
replies to the sender. Pure stdlib (imaplib + smtplib + email). Works with
Gmail using an App Password (Google Account → Security → App passwords).

Setup:
    export ANTHROPIC_API_KEY=sk-ant-...
    export EMAIL_USER=you@gmail.com
    export EMAIL_PASS=your-app-password          # NOT your login password
    # optional (defaults shown):
    export IMAP_HOST=imap.gmail.com
    export SMTP_HOST=smtp.gmail.com
    export SMTP_PORT=587

    recc-mail --allow-from you@gmail.com          # only act on mail from you
    recc-mail --allow-writes --allow-from you@gmail.com   # full access, locked down

Safety: same as the other channels — read-only by default, writes require
--allow-writes, catastrophic shell commands always blocked. ALWAYS set
--allow-from so strangers can't email your agent into running commands.
"""
import argparse, email, imaplib, os, smtplib, sys, time
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

from . import agent as A
from . import core


def _decode(s):
    try:
        return str(make_header(decode_header(s or "")))
    except Exception:
        return s or ""


def _body_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and \
               "attachment" not in str(part.get("Content-Disposition", "")):
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", "replace")
                except Exception:
                    continue
        return ""
    try:
        return msg.get_payload(decode=True).decode(
            msg.get_content_charset() or "utf-8", "replace")
    except Exception:
        return msg.get_payload() or ""


def send_reply(cfg, to_addr, subject, body, in_reply_to=None):
    out = EmailMessage()
    out["From"] = cfg["user"]
    out["To"] = to_addr
    out["Subject"] = subject
    if in_reply_to:
        out["In-Reply-To"] = in_reply_to
        out["References"] = in_reply_to
    out.set_content(body)
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as s:
        s.starttls()
        s.login(cfg["user"], cfg["pass"])
        s.send_message(out)


def poll_once(cfg, client, model, permission, running, allow_from):
    box = imaplib.IMAP4_SSL(cfg["imap_host"])
    box.login(cfg["user"], cfg["pass"])
    box.select("INBOX")
    typ, data = box.search(None, "UNSEEN")
    ids = data[0].split() if data and data[0] else []
    for num in ids:
        typ, raw = box.fetch(num, "(RFC822)")
        if typ != "OK":
            continue
        msg = email.message_from_bytes(raw[0][1])
        sender = parseaddr(msg.get("From", ""))[1].lower()
        subject = _decode(msg.get("Subject", "(no subject)"))
        mid = msg.get("Message-ID")
        body = _body_text(msg).strip()

        if allow_from and sender not in allow_from:
            print(f"  ignored mail from {sender} (not in allow-from)")
            continue  # left unread-marked as read below to avoid reprocessing
        if not body:
            continue

        task = f"{subject}\n\n{body}" if subject not in ("", "(no subject)") else body
        print(f"  → {sender}: {subject!r}")
        messages = [{"role": "user", "content": task}]
        try:
            reply = core.run_turn(client, model, messages, permission, running)
        except Exception as e:
            reply = f"error: {type(e).__name__}: {e}"
        re_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        send_reply(cfg, sender, re_subject, reply, in_reply_to=mid)
        print(f"    replied · total cost≈${running['cost']:.4f}")
    box.close(); box.logout()


def main():
    ap = argparse.ArgumentParser(description="recc-mail — email bridge for recc-agent")
    ap.add_argument("--model", default=A.DEFAULT_MODEL)
    ap.add_argument("--allow-writes", action="store_true",
                    help="permit file edits and shell commands (off by default)")
    ap.add_argument("--allow-from", action="append", default=[],
                    help="only act on mail from these address(es); repeatable. STRONGLY advised.")
    ap.add_argument("--interval", type=int, default=30, help="seconds between inbox polls")
    args = ap.parse_args()

    user, pw = os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS")
    if not user or not pw:
        print("Set EMAIL_USER and EMAIL_PASS (use an App Password for Gmail).",
              file=sys.stderr); sys.exit(1)
    cfg = {"user": user, "pass": pw,
           "imap_host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
           "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
           "smtp_port": int(os.environ.get("SMTP_PORT", "587"))}
    client = core.get_client()
    permission = core.make_permission(args.allow_writes)
    allow_from = set(a.lower() for a in args.allow_from)
    running = {"cost": 0.0}

    mode = "read+write" if args.allow_writes else "read-only (safe)"
    print(f"recc-mail polling {cfg['imap_host']} as {user} · model={args.model} · mode={mode}")
    if not allow_from:
        print("⚠  no --allow-from set: anyone who emails you can drive the agent. "
              "Add --allow-from your@address.")
    while True:
        try:
            poll_once(cfg, client, args.model, permission, running, allow_from)
        except Exception as e:
            print("poll error:", e)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
