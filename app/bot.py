from telegram import Update, BotCommand, ReplyKeyboardMarkup
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from app.database import SessionLocal
import logging
from app.utils.bot_commands import set_bot_commands_async, get_token_from_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app.bot")

from app.models.models import Work, Technician, WorkEvent
from datetime import datetime
from app.utils.help_text import HELP_TEXT

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger.info("🤖 Telegram Bot FTTH - Inizializzazione...")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([['/miei_lavori', '/accetta', '/rifiuta'], ['/chiudi', '/help']], one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text("Benvenuto nel bot FTTH!", reply_markup=kb)

async def miei_lavori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        works = db.query(Work).filter(Work.tecnico_assegnato_id == tech.id).all()
        text = "\n".join([f"WR {w.numero_wr} - {w.stato} - {w.indirizzo}" for w in works])
    await update.message.reply_text(text or "Nessun lavoro assegnato")

async def accetta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /accetta <WR>")
        return
    wr = context.args[0]
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if work:
            work.stato = "in_corso"
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="accepted", description="Accepted by tech", user_id=tech.id)
            db.add(event)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                await update.message.reply_text(f"Errore aggiornamento: {e}")
                return
            await update.message.reply_text("Lavoro accettato")
        else:
            await update.message.reply_text("Lavoro non trovato")

async def rifiuta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /rifiuta <WR>")
        return
    wr = context.args[0]
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if work:
            work.stato = "aperto"
            work.tecnico_assegnato_id = None
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="rejected", description="Rejected by tech", user_id=tech.id)
            db.add(event)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                await update.message.reply_text(f"Errore aggiornamento: {e}")
                return
            await update.message.reply_text("Lavoro rifiutato")
        else:
            await update.message.reply_text("Lavoro non trovato")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with a short help text listing available commands."""
    kb = ReplyKeyboardMarkup([['/miei_lavori', '/accetta', '/rifiuta'], ['/chiudi', '/help']], one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(HELP_TEXT, reply_markup=kb)


async def chiudi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /chiudi <WR>")
        return
    wr = context.args[0]
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if not work:
            await update.message.reply_text("Lavoro non trovato")
            return
        work.stato = "chiuso"
        work.data_chiusura = datetime.now()
        event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="closed", description="Closed by tech", user_id=tech.id)
        db.add(event)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            await update.message.reply_text(f"Errore aggiornamento: {e}")
            return
        await update.message.reply_text("Lavoro chiuso")

# Add more handlers for chiudi, problema, etc.

def main():
    logger.info("🚀 Avvio Bot Telegram FTTH...")
    if not TOKEN:
        logger.error('❌ TELEGRAM_BOT_TOKEN is not set; bot will not start')
        return
    logger.info("✅ Token Telegram caricato correttamente")
    
    webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
    polling_env = os.getenv('TELEGRAM_POLLING', 'true').lower()
    polling_enabled = polling_env in ('1', 'true', 'yes')
    if webhook_url and not polling_enabled:
        logger.info('TELEGRAM_WEBHOOK_URL is set and TELEGRAM_POLLING=false; not starting polling to avoid conflicts')
        return
    
    logger.info("🔧 Costruzione applicazione bot...")
    application = Application.builder().token(TOKEN).build()
    logger.info("📝 Registrazione handlers comandi...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("miei_lavori", miei_lavori))
    application.add_handler(CommandHandler("accetta", accetta))
    application.add_handler(CommandHandler("rifiuta", rifiuta))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chiudi", chiudi))
    logger.info("✅ Handlers registrati: /start /miei_lavori /accetta /rifiuta /chiudi /help")

    # Ensure bot commands are set before polling (compatibility: some library versions don't support post_init)
    async def _set_commands_async():
        commands = [
            BotCommand("start", "Benvenuto"),
            BotCommand("help", "Mostra comandi"),
            BotCommand("miei_lavori", "I tuoi lavori"),
            BotCommand("accetta", "Accetta un lavoro"),
            BotCommand("rifiuta", "Rifiuta un lavoro"),
            BotCommand("chiudi", "Chiudi un lavoro"),
        ]
    # Try using the library method if possible, otherwise fallback to HTTP API.
    try:
        # Try to set using the library synchronously if bot is already available
        # Note: `application.bot` might not be available here; we attempt an asyncio run to set via HTTP fallback.
        token = get_token_from_env()
        commands_payload = [
            {"command": "start", "description": "Benvenuto"},
            {"command": "help", "description": "Mostra comandi"},
            {"command": "miei_lavori", "description": "I tuoi lavori"},
            {"command": "accetta", "description": "Accetta un lavoro"},
            {"command": "rifiuta", "description": "Rifiuta un lavoro"},
            {"command": "chiudi", "description": "Chiudi un lavoro"},
        ]
        ok = asyncio.run(set_bot_commands_async(token, commands_payload))
        if ok:
            logger.info("Telegram bot commands set via HTTP fallback before polling")
    except Exception as e:
        logger.exception("Failed to set bot commands before polling: %s", e)

    # Now run polling without post_init for compatibility
    try:
        logger.info('🔄 Starting bot polling...')
        logger.info('✅ Bot FTTH attivo e in ascolto! 🎉')
        application.run_polling()
    except Exception as e:
        # If the polling is terminated because the webhook or another getUpdates is running, log and exit gracefully
        logger.exception("❌ Bot polling error; check that no webhook or other getUpdates poller is running: %s", e)

if __name__ == '__main__':
    main()