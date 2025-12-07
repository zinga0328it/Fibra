import os
import logging
from typing import List
try:
    import httpx
except Exception:
    httpx = None

logger = logging.getLogger("app.utils.bot_commands")

BOT_COMMANDS = [
    {"command": "start", "description": "Benvenuto"},
    {"command": "help", "description": "Mostra comandi"},
    {"command": "miei_lavori", "description": "I tuoi lavori"},
    {"command": "accetta", "description": "Accetta un lavoro"},
    {"command": "rifiuta", "description": "Rifiuta un lavoro"},
    {"command": "chiudi", "description": "Chiudi un lavoro"},
]


def _build_url(token: str) -> str:
    return f"https://api.telegram.org/bot{token}/setMyCommands"


def set_bot_commands(token: str, commands: List[dict] = None) -> bool:
    """Sync helper to set bot commands via HTTP API. Returns True on success."""
    if not token:
        logger.info("No TELEGRAM_BOT_TOKEN set; skipping setting bot commands")
        return False
    if not httpx:
        logger.warning("httpx not available; cannot set bot commands via HTTP")
        return False
    if commands is None:
        commands = BOT_COMMANDS
    url = _build_url(token)
    try:
        resp = httpx.post(url, json={"commands": commands}, timeout=10.0)
        resp.raise_for_status()
        logger.info("Set bot commands via HTTP")
        return True
    except Exception as e:
        logger.exception("Failed to set bot commands via HTTP: %s", e)
        return False


async def set_bot_commands_async(token: str, commands: List[dict] = None) -> bool:
    """Async helper to set bot commands via HTTP API. Returns True on success."""
    if not token:
        logger.info("No TELEGRAM_BOT_TOKEN set; skipping setting bot commands")
        return False
    if not httpx:
        logger.warning("httpx not available; cannot set bot commands via HTTP")
        return False
    if commands is None:
        commands = BOT_COMMANDS
    url = _build_url(token)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"commands": commands}, timeout=10.0)
            resp.raise_for_status()
        logger.info("Set bot commands via HTTP (async)")
        return True
    except Exception as e:
        logger.exception("Failed to set bot commands via HTTP (async): %s", e)
        return False


def get_token_from_env() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")
