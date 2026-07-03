#!/usr/bin/env python3
"""
recc-whatsapp — drive recc-agent from WhatsApp via the Meta Cloud API.

Runs a small webhook server (stdlib http.server). Meta delivers inbound
messages to it; it runs the agent loop and replies through the Cloud API.
You need a Meta WhatsApp Business app (free tier) with a phone number id and
token, and a public HTTPS URL to your webhook (use a tunnel like ngrok/cloudflared
in development, or host it — see the repo README's hosting notes).

Setup:
    export ANTHROPIC_API_KEY=sk-ant-...
    export WHATSAPP_TOKEN=EAAG...            # Cloud API access token
    export WHATSAPP_PHONE_ID=1234567890      # phone number id
    export WHATSAPP_VERIFY_TOKEN=some-secret # you choose; put same value in Meta console

    recc-whatsapp --allow-from 15551234567   # your number, digits only
    recc-whatsapp --allow-writes --allow-from 15551234567

Then point your Meta webhook at  https://<your-host>/webhook  with the verify token.
Safety identical to the other channels; ALWAYS set --allow-from.
"""
import argparse, json, os, sys, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import agent as A
from . import core

GRAPH = "https://graph.facebook.com/v20.0"


def wa_send(token, phone_id, to, text):
    url = f"{GRAPH}/{phone_id}/messages"
    payload = json.dumps({"messaging_product": "whatsapp", "to": to,
                          "type": "text", "text": {"body": text[:4000]}}).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        print("send error:", e)


def make_handler(cfg, client, model, permission, running, allow_from):
    convos = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("hub.verify_token", [""])[0] == cfg["verify"]:
                self.send_response(200); self.end_headers()
                self.wfile.write(q.get("hub.challenge", [""])[0].encode())
            else:
                self.send_response(403); self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            self.send_response(200); self.end_headers()  # ack fast
            try:
                data = json.loads(body)
                for entry in data.get("entry", []):
                    for ch in entry.get("changes", []):
                        for m in ch.get("value", {}).get("messages", []):
                            if m.get("type") != "text":
                                continue
                            frm = m.get("from", "")
                            text = m.get("text", {}).get("body", "").strip()
                            self._handle(frm, text)
            except Exception as e:
                print("webhook error:", e)

        def _handle(self, frm, text):
            if not text:
                return
            if allow_from and frm not in allow_from:
                wa_send(cfg["token"], cfg["phone_id"], frm,
                        "This assistant is restricted to its owner.")
                return
            if text.lower() in ("/new", "/reset"):
                convos.pop(frm, None)
                wa_send(cfg["token"], cfg["phone_id"], frm, "Context cleared.")
                return
            messages = convos.setdefault(frm, [])
            messages.append({"role": "user", "content": text})
            print(f"  → {frm}: {text[:60]!r}")
            try:
                reply = core.run_turn(client, model, messages, permission, running)
            except Exception as e:
                reply = f"error: {type(e).__name__}: {e}"
            wa_send(cfg["token"], cfg["phone_id"], frm, reply)
            print(f"    replied · total cost≈${running['cost']:.4f}")

    return H


def main():
    ap = argparse.ArgumentParser(description="recc-whatsapp — WhatsApp bridge for recc-agent")
    ap.add_argument("--model", default=A.DEFAULT_MODEL)
    ap.add_argument("--allow-writes", action="store_true")
    ap.add_argument("--allow-from", action="append", default=[],
                    help="WhatsApp number(s), digits only; repeatable. STRONGLY advised.")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = ap.parse_args()

    cfg = {"token": os.environ.get("WHATSAPP_TOKEN"),
           "phone_id": os.environ.get("WHATSAPP_PHONE_ID"),
           "verify": os.environ.get("WHATSAPP_VERIFY_TOKEN")}
    if not all(cfg.values()):
        print("Set WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_VERIFY_TOKEN.",
              file=sys.stderr); sys.exit(1)
    client = core.get_client()
    permission = core.make_permission(args.allow_writes)
    allow_from = set(str(a) for a in args.allow_from)
    running = {"cost": 0.0}

    mode = "read+write" if args.allow_writes else "read-only (safe)"
    H = make_handler(cfg, client, args.model, permission, running, allow_from)
    print(f"recc-whatsapp webhook on :{args.port}/webhook · model={args.model} · mode={mode}")
    if not allow_from:
        print("⚠  no --allow-from set: anyone who messages your number can drive the agent.")
    HTTPServer(("0.0.0.0", args.port), H).serve_forever()


if __name__ == "__main__":
    main()
