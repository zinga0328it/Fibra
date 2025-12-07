#!/usr/bin/env python3
"""Small utility to set Telegram bot menu commands using the Bot API.
Usage: python scripts/set_bot_commands.py
Requires TELEGRAM_BOT_TOKEN in environment or .env file in repo root.
"""
import os
import logging
from dotenv import load_dotenv
from app.utils.bot_commands import set_bot_commands, get_token_from_env, BOT_COMMANDS

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("set_bot_commands")

token = get_token_from_env()
if not token:
    logger.error("TELEGRAM_BOT_TOKEN not set. Export it or use a .env file.")
    raise SystemExit(1)

ok = set_bot_commands(token, [c for c in BOT_COMMANDS])
if ok:
    logger.info("Bot commands set OK")
else:
    logger.error("Failed setting bot commands")
