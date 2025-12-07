#!/usr/bin/env bash
# Simple check script for Telegram bot status and webhook
set -eu

# Optional: read env vars from .env if present
if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs)
fi

if [[ -z "${TELEGRAM_BOT_TOKEN+set}" ]]; then
  echo "TELEGRAM_BOT_TOKEN is not set; set it in your environment or .env"
  exit 1
fi

API_BASE=${1:-http://127.0.0.1:6030}

echo "Checking local Telegram status @ ${API_BASE}/telegram/status"
if command -v curl &>/dev/null; then
  curl -sSf "${API_BASE}/telegram/status" | jq '.' || true
  echo "\nChecking Telegram Bot API directly (getMe, getWebhookInfo)"
  curl -sSf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | jq '.' || true
  curl -sSf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq '.' || true
else
  echo "curl is not installed; please install curl to run this script"
  exit 2
fi

exit 0
