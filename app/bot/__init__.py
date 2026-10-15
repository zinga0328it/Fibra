"""
app/bot/__init__.py - Entry point del bot Telegram FTTH modulare.

Registra tutti i CommandHandler e avvia il polling.
Ogni comando vive nel suo file cmd_*.py per scalabilità.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import comandi modulari
from app.bot.menu import start, help_command
from app.bot.cmd_miei_lavori import miei_lavori
from app.bot.cmd_accetta import accetta
from app.bot.cmd_rifiuta import rifiuta
from app.bot.cmd_sospendi import sospendi
from app.bot.cmd_chiudi import chiudi
from app.bot.cmd_modem import modem
from app.bot.cmd_istruzioni import istruzioni
from app.bot.cmd_sync import sync_status
from app.bot.cmd_aggiorna_note import aggiorna_note
from app.bot.cmd_modems import modems, configura_modem, installa_modem
from app.bot.cmd_posizione import posizione, handle_location
from app.bot.cmd_sos import sos
from app.bot.cmd_fine_sos import fine_sos

load_dotenv()
logger = logging.getLogger("app.bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ── Registry dei comandi ──────────────────────────────────────────
# Per aggiungere un nuovo comando:
# 1. Crea app/bot/cmd_nome.py con la funzione async
# 2. Aggiungi la entry qui sotto
# 3. Riavvia il servizio
COMMANDS = [
    # (nome_comando, handler_function, descrizione_per_menu_telegram)
    ("start",           start,           "Benvenuto"),
    ("help",            help_command,    "Mostra comandi"),
    ("miei_lavori",     miei_lavori,     "I tuoi lavori attivi"),
    ("accetta",         accetta,         "Accetta un lavoro"),
    ("rifiuta",         rifiuta,         "Rifiuta un lavoro"),
    ("sospendi",        sospendi,        "Sospendi lavoro con motivo"),
    ("modem",           modem,           "Registra seriale modem"),
    ("chiudi",          chiudi,          "Chiudi lavoro con note"),
    ("istruzioni",      istruzioni,      "Istruzioni installazione"),
    ("sync_status",     sync_status,     "Stato sincronizzazione"),
    ("aggiorna_note",   aggiorna_note,   "Aggiorna note modem"),
    ("modems",          modems,          "Lista modem assegnati"),
    ("configura_modem", configura_modem, "Config modem"),
    ("installa_modem",  installa_modem,  "Segna modem installato"),
    ("posizione",       posizione,       "Invia la tua posizione GPS"),
    ("sos",             sos,             "SOS - Chiedi aiuto"),
    ("fine_sos",        fine_sos,        "Disattiva SOS"),
]


def main():
    """Avvia il bot Telegram FTTH in modalità polling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("🤖 Telegram Bot FTTH modulare - Avvio...")

    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN non configurato; bot non avviato.")
        return

    # Se webhook attivo e polling disabilitato, non avviare
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    polling_env = os.getenv("TELEGRAM_POLLING", "true").lower()
    polling_enabled = polling_env in ("1", "true", "yes")
    if webhook_url and not polling_enabled:
        logger.info("Webhook attivo + TELEGRAM_POLLING=false → polling non avviato.")
        return

    # Costruisci applicazione
    application = Application.builder().token(TOKEN).build()

    # Registra handlers dal registry
    for name, handler_fn, _desc in COMMANDS:
        application.add_handler(CommandHandler(name, handler_fn))
        logger.info("  ✅ /%s registrato", name)

    # Handler speciale per messaggi di tipo Location (GPS da Telegram)
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    logger.info("  ✅ Location handler registrato")

    logger.info("📝 %d comandi registrati.", len(COMMANDS))

    # Imposta menu comandi Telegram
    try:
        bot_commands = [BotCommand(name, desc) for name, _, desc in COMMANDS]
        asyncio.run(_set_commands(bot_commands))
    except Exception as e:
        logger.warning("Non riuscito a impostare menu comandi: %s", e)

    # Avvia polling
    try:
        logger.info("🔄 Avvio polling...")
        logger.info("✅ Bot FTTH modulare attivo! 🎉")
        application.run_polling()
    except Exception as e:
        logger.exception("Polling terminato: %s", e)


async def _set_commands(commands):
    """Imposta i comandi del bot via HTTP API."""
    from app.utils.bot_commands import set_bot_commands_async, get_token_from_env
    token = get_token_from_env()
    if token:
        await set_bot_commands_async(
            token,
            [{"command": c.command, "description": c.description} for c in commands],
        )
