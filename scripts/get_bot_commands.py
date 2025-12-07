#!/usr/bin/env python3
"""Small utility to fetch Telegram bot commands using the Bot API.
Usage: python scripts/get_bot_commands.py
Requires TELEGRAM_BOT_TOKEN in environment or .env file in repo root.
"""
import os
import logging
from dotenv import load_dotenv
try:
    import httpx
except Exception:
    httpx = None

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("get_bot_commands")

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN not set. Export it or use a .env file.")
    raise SystemExit(1)
if not httpx:
    logger.error("httpx not available")
    raise SystemExit(1)

url = f"https://api.telegram.org/bot{token}/getMyCommands"
try:
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    if data.get("ok"):
        logger.info("Commands: %s", data.get("result"))
    else:
        logger.error("Error: %s", data)
except Exception as e:
    logger.exception("Error getting commands: %s", e)
