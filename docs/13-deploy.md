# 13. Hosting It Online

The terminal agent runs on demand, but the chat channels (`recc-bridge`, `recc-mail`,
`recc-whatsapp`) are long-running services — to use them from your phone anytime, host them.

> **Security first.** A hosted agent with `--allow-writes` runs code on the host on anyone's
> message. Always `--allow-from` / `--allow-chat` to lock it to you, keep secrets in env vars
> (never in git), and prefer read-only mode unless you fully trust the setup.

## Install targets

| Method | Command |
|--------|---------|
| pip, from source | `pip install "git+https://github.com/SaieshwarTech/reverse-engineering-claude-code"` |
| pip, once published | `pip install recc-cli` |
| npm, once published | `npm i -g recc-cli` (shells out to the PyPI package; needs Python 3.9+) |
| Docker | `docker build -t recc . && docker run ... recc recc-bridge` |

## 1. systemd (your own Linux box / VPS)

`/etc/systemd/system/recc-bridge.service`:

```ini
[Unit]
Description=recc-bridge (Telegram)
After=network-online.target

[Service]
Environment=ANTHROPIC_API_KEY=sk-ant-...
Environment=TELEGRAM_BOT_TOKEN=123:ABC...
ExecStart=/usr/local/bin/recc-bridge --allow-chat 123456789
Restart=always
User=recc

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now recc-bridge
journalctl -u recc-bridge -f
```

## 2. Docker / Docker Compose

```yaml
# docker-compose.yml
services:
  telegram:
    build: .
    command: recc-bridge --allow-chat 123456789
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
    restart: unless-stopped

  whatsapp:                       # needs a public HTTPS URL (see below)
    build: .
    command: recc-whatsapp --allow-from 15551234567
    ports: ["8000:8000"]
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      WHATSAPP_TOKEN: ${WHATSAPP_TOKEN}
      WHATSAPP_PHONE_ID: ${WHATSAPP_PHONE_ID}
      WHATSAPP_VERIFY_TOKEN: ${WHATSAPP_VERIFY_TOKEN}
    restart: unless-stopped
```

## 3. PaaS (Railway / Fly.io / Render)

The repo's `Dockerfile` works as-is. Two shapes:

- **Poll channels** (`recc-bridge`, `recc-mail`) need no inbound port — deploy as a *worker*.
- **Webhook channel** (`recc-whatsapp`) needs a public HTTPS URL — deploy as a *web service*
  that exposes `$PORT`, then set the Meta webhook to `https://<your-app>/webhook`.

Set the secrets (`ANTHROPIC_API_KEY`, channel tokens) as service env vars, and put the
channel command (e.g. `recc-whatsapp --allow-from 15551234567`) as the start command.

## 4. Local + a tunnel (fastest for WhatsApp dev)

WhatsApp requires a public HTTPS webhook. In development, tunnel your local server:

```bash
recc-whatsapp --allow-from 15551234567          # listens on :8000
cloudflared tunnel --url http://localhost:8000  # or: ngrok http 8000
# put the printed https URL + /webhook into the Meta console
```

Telegram and email need no tunnel — they poll outbound, so they run anywhere with
internet access, including behind NAT.

## Cost & operations

- Watch spend: each channel prints a running `cost≈$…`; `recc cost` audits sessions (ch. 9).
- Use a cheaper model for a personal assistant: `--model claude-haiku-4-5`.
- One process per channel; run several side by side. They don't share state unless you add
  a shared memory store (a good next contribution — see [`CONTRIBUTING.md`](../CONTRIBUTING.md)).
