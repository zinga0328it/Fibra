"""
Telegram bot module for Gestionale Fibra.

Provides webhook-ready Telegram bot for field technicians.
"""

from app.telegram.bot import TelegramBot, telegram_bot
from app.telegram.handlers import (
    handle_start,
    handle_accept_job,
    handle_refuse_job,
    handle_close_job,
    handle_photo,
)

__all__ = [
    "TelegramBot",
    "telegram_bot",
    "handle_start",
    "handle_accept_job",
    "handle_refuse_job",
    "handle_close_job",
    "handle_photo",
]
