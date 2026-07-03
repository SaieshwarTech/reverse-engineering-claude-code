# Container for the always-on channels (recc-bridge / recc-mail / recc-whatsapp).
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY recc_cli ./recc_cli
RUN pip install --no-cache-dir .

# Webhook channels listen on $PORT (WhatsApp). Poll channels ignore it.
ENV PORT=8000
EXPOSE 8000

# Override CMD to pick a channel, e.g.:
#   docker run -e ANTHROPIC_API_KEY=... -e TELEGRAM_BOT_TOKEN=... IMAGE recc-bridge
#   docker run -p 8000:8000 -e ... IMAGE recc-whatsapp --allow-from 15551234567
CMD ["recc-bridge"]
