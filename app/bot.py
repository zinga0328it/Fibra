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

from app.models.models import Work, Technician, WorkEvent, ONT, Modem, ONTModemSync
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
            
            # Prepara messaggio con dettagli lavoro e dispositivi
            text = f"📋 Lavoro accettato!\n"
            text += f"🔢 WR: {work.numero_wr}\n"
            text += f"📍 Indirizzo: {work.indirizzo}\n\n"
            
            if work.ont or work.modem:
                text += "📡 Equipaggiamento:\n"
                if work.ont:
                    text += f"• ONT: {work.ont.model} (SN: {work.ont.serial_number})\n"
                if work.modem:
                    text += f"• Modem: {work.modem.model} (SN: {work.modem.serial_number})\n"
                    if work.modem.wifi_ssid:
                        text += f"• WiFi: {work.modem.wifi_ssid}\n"
                    if work.modem.sync_method:
                        text += f"• Sync: {work.modem.sync_method}\n"
                text += "\n"
            
            text += "Usa /istruzioni per vedere le istruzioni dettagliate"
            
            await update.message.reply_text(text)
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

async def istruzioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra istruzioni installazione dispositivi per un lavoro"""
    if not context.args:
        await update.message.reply_text("Uso: /istruzioni <WR>")
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
            await update.message.reply_text("Lavoro non trovato o non assegnato a te")
            return

        # Trova dispositivi assegnati al lavoro
        ont = work.ont if work.ont else None
        modem = work.modem if work.modem else None
        sync = db.query(ONTModemSync).filter(ONTModemSync.work_id == work.id).first()

        text = f"📋 Istruzioni per WR {wr}\n"
        text += f"📍 {work.indirizzo}\n\n"

        if ont:
            text += f"📡 ONT: {ont.model} (SN: {ont.serial_number})\n"
        if modem:
            text += f"📶 Modem: {modem.model} (SN: {modem.serial_number})\n"
        if sync:
            text += f"🔗 Sync: {sync.sync_method}\n"
            if sync.wifi_ssid:
                text += f"📶 WiFi: {sync.wifi_ssid}\n"

        text += "\n🔧 Istruzioni installazione:\n"
        text += "1. Collega ONT alla fibra ottica\n"
        text += "2. Configura PPPoE sul modem\n"
        text += "3. Sincronizza ONT-Modem\n"
        text += "4. Verifica connessione internet\n"
        text += "5. Usa /aggiorna_note per salvare configurazione"

        await update.message.reply_text(text)

async def sync_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra stato sincronizzazione per un lavoro"""
    if not context.args:
        await update.message.reply_text("Uso: /sync_status <WR>")
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
            await update.message.reply_text("Lavoro non trovato o non assegnato a te")
            return

        syncs = db.query(ONTModemSync).filter(ONTModemSync.work_id == work.id).all()

        if not syncs:
            await update.message.reply_text("Nessuna sincronizzazione registrata per questo lavoro")
            return

        text = f"🔗 Stato sincronizzazione WR {wr}\n\n"
        for sync in syncs:
            ont = db.query(ONT).filter(ONT.id == sync.ont_id).first()
            modem = db.query(Modem).filter(Modem.id == sync.modem_id).first()

            text += f"📡 ONT: {ont.serial_number if ont else 'N/A'}\n"
            text += f"📶 Modem: {modem.serial_number if modem else 'N/A'}\n"
            text += f"🔗 Metodo: {sync.sync_method}\n"
            text += f"📊 Stato: {sync.sync_status}\n"
            if sync.synced_at:
                text += f"✅ Sincronizzato: {sync.synced_at.strftime('%d/%m/%Y %H:%M')}\n"
            if sync.technician_notes:
                text += f"📝 Note: {sync.technician_notes[:100]}...\n"
            text += "\n"

        await update.message.reply_text(text)

async def aggiorna_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aggiorna note tecniche per un lavoro"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Uso: /aggiorna_note <WR> <note>")
        return
    wr = context.args[0]
    note = " ".join(context.args[1:])
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if not work:
            await update.message.reply_text("Lavoro non trovato o non assegnato a te")
            return

        sync = db.query(ONTModemSync).filter(ONTModemSync.work_id == work.id).first()
        if not sync:
            await update.message.reply_text("Nessuna sincronizzazione trovata per questo lavoro")
            return

        sync.technician_notes = note
        try:
            db.commit()
            await update.message.reply_text("✅ Note aggiornate con successo")
        except Exception as e:
            db.rollback()
            await update.message.reply_text(f"❌ Errore aggiornamento note: {e}")

async def modems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra modem assegnati al tecnico"""
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        
        # Trova tutti i lavori del tecnico con modem assegnati
        works_with_modems = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.modem != None
        ).all()
        
        if not works_with_modems:
            await update.message.reply_text("Nessun modem assegnato ai tuoi lavori")
            return
        
        text = "📶 Modem assegnati:\n\n"
        for work in works_with_modems:
            if work.modem:
                text += f"🔢 WR: {work.numero_wr}\n"
                text += f"📍 {work.indirizzo}\n"
                text += f"📶 Modem: {work.modem.model} (SN: {work.modem.serial_number})\n"
                text += f"📊 Stato: {work.modem.status}\n"
                if work.modem.wifi_ssid:
                    text += f"📶 WiFi: {work.modem.wifi_ssid}\n"
                text += "\n"
        
        await update.message.reply_text(text)

async def configura_modem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra configurazione modem per un lavoro"""
    if not context.args:
        await update.message.reply_text("Uso: /configura_modem <WR>")
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
            await update.message.reply_text("Lavoro non trovato o non assegnato a te")
            return
        
        if not work.modem:
            await update.message.reply_text("Nessun modem assegnato a questo lavoro")
            return
        
        modem = work.modem
        text = f"⚙️ Configurazione Modem WR {wr}\n\n"
        text += f"📶 Modello: {modem.model}\n"
        text += f"🔢 SN: {modem.serial_number}\n\n"
        
        if modem.wifi_ssid and modem.wifi_password:
            text += f"📶 WiFi SSID: {modem.wifi_ssid}\n"
            text += f"🔑 Password: {modem.wifi_password}\n\n"
        
        if modem.admin_username and modem.admin_password:
            text += f"👤 Admin User: {modem.admin_username}\n"
            text += f"🔑 Admin Pass: {modem.admin_password}\n\n"
        
        if modem.sync_method:
            text += f"🔗 Metodo Sync: {modem.sync_method}\n"
        
        if modem.configuration_notes:
            text += f"📝 Note configurazione:\n{modem.configuration_notes}\n"
        
        await update.message.reply_text(text)

async def installa_modem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Segna modem come installato"""
    if not context.args:
        await update.message.reply_text("Uso: /installa_modem <WR>")
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
            await update.message.reply_text("Lavoro non trovato o non assegnato a te")
            return
        
        if not work.modem:
            await update.message.reply_text("Nessun modem assegnato a questo lavoro")
            return
        
        if work.modem.status != "assigned":
            await update.message.reply_text("Il modem deve essere assegnato prima di poter essere installato")
            return
        
        work.modem.status = "installed"
        work.modem.installed_at = datetime.utcnow()
        
        try:
            db.commit()
            await update.message.reply_text("✅ Modem segnato come installato")
        except Exception as e:
            db.rollback()
            await update.message.reply_text(f"❌ Errore: {e}")

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
    application.add_handler(CommandHandler("istruzioni", istruzioni))
    application.add_handler(CommandHandler("sync_status", sync_status))
    application.add_handler(CommandHandler("aggiorna_note", aggiorna_note))
    application.add_handler(CommandHandler("modems", modems))
    application.add_handler(CommandHandler("configura_modem", configura_modem))
    application.add_handler(CommandHandler("installa_modem", installa_modem))
    logger.info("✅ Handlers registrati: /start /miei_lavori /accetta /rifiuta /chiudi /help /istruzioni /sync_status /aggiorna_note /modems /configura_modem /installa_modem")

    # Ensure bot commands are set before polling (compatibility: some library versions don't support post_init)
    async def _set_commands_async():
        commands = [
            BotCommand("start", "Benvenuto"),
            BotCommand("help", "Mostra comandi"),
            BotCommand("miei_lavori", "I tuoi lavori"),
            BotCommand("accetta", "Accetta un lavoro"),
            BotCommand("rifiuta", "Rifiuta un lavoro"),
            BotCommand("chiudi", "Chiudi un lavoro"),
            BotCommand("istruzioni", "Istruzioni installazione dispositivi"),
            BotCommand("sync_status", "Stato sincronizzazione"),
            BotCommand("aggiorna_note", "Aggiorna note tecniche"),
            BotCommand("modems", "Lista modem assegnati"),
            BotCommand("configura_modem", "Mostra configurazione modem"),
            BotCommand("installa_modem", "Segna modem come installato"),
        ]
    # Try using the library method if possible, otherwise fallback to HTTP API.
    try:
        # Try to set using the library synchronously if bot is already available
        # Note: `application.bot` might not be available here; we attempt an asyncio run to set via HTTP fallback.
        asyncio.run(_set_commands_async())
    except Exception as e:
        logger.exception("Failed to set bot commands before polling: %s", e)

    # Now run polling without post_init for compatibility
    try:
        logger.info('🔄 Starting bot polling...')
        logger.info('✅ Bot FTTH attivo e in ascolto! 🎉')
        application.run_polling()
    except Exception as e:
        # If the polling is terminated because the webhook or another getUpdates is running, log and exit gracefully
        logger.exception("Polling terminated unexpectedly: %s", e)
        logger.info("🔄 Riprovo a partire...")
        try:
            application.run_polling()
        except Exception as e:
            logger.exception("Polling failed again: %s", e)
            logger.info("❌ Impossibile avviare il bot. Controlla la configurazione.")
            return

if __name__ == "__main__":
    main()