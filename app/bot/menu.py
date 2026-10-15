"""
app/bot/menu.py - Comandi /start e /help.

Mostra messaggio di benvenuto e lista comandi con tastiera.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import KEYBOARD
from app.utils.help_text import HELP_TEXT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Messaggio di benvenuto con tastiera comandi."""
    await update.message.reply_text(
        "🤖 Benvenuto nel bot FTTH!\n\nUsa /help per vedere i comandi.",
        reply_markup=KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra la lista di tutti i comandi disponibili."""
    await update.message.reply_text(HELP_TEXT, reply_markup=KEYBOARD)
