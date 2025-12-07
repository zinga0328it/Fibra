import os
import logging
from typing import Any
try:
    import httpx
except Exception:
    httpx = None

logger = logging.getLogger("app.utils.telegram")


def send_message_to_telegram(chat_id: Any, text: str, reply_markup: dict | None = None) -> bool:
    """Send a text message to a Telegram chat using Bot API.

    Returns True on success, False on failure.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping telegram notification")
        return False
    if not httpx:
        logger.warning("httpx not available, cannot send telegram message")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": int(chat_id), "text": text}
    if reply_markup is not None:
        # the Bot API expects a JSON object for reply_markup; httpx will encode this dict automatically
        payload["reply_markup"] = reply_markup
    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
        logger.info("Sent telegram message to %s", chat_id)
        return True
    except Exception as e:
        logger.exception("Error sending telegram message: %s", e)
        return False
