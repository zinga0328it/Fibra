"""
app/bot/cmd_modems.py - Comandi /modems, /configura_modem, /installa_modem.

Gestione modem assegnati al tecnico.
TODO: Sarà riscritto nella prossima iterazione con supporto avanzato.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, Modem
from datetime import datetime


async def modems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra modem assegnati ai lavori del tecnico."""
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        works_with_modems = (
            db.query(Work)
            .filter(
                Work.tecnico_assegnato_id == tech.id,
                Work.modem != None,
            )
            .all()
        )

        if not works_with_modems:
            await update.message.reply_text("Nessun modem assegnato ai tuoi lavori.")
            return

        text = "📶 Modem assegnati:\n\n"
        for work in works_with_modems:
            if work.modem:
                text += f"🔢 WR: {work.numero_wr}\n"
                text += f"📍 {work.indirizzo or 'N/D'}\n"
                text += f"📶 {work.modem.model} (SN: {work.modem.serial_number})\n"
                text += f"📊 Stato: {work.modem.status}\n"
                if work.modem.wifi_ssid:
                    text += f"📶 WiFi: {work.modem.wifi_ssid}\n"
                text += "\n"

        await update.message.reply_text(text)


async def configura_modem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra configurazione modem per un lavoro."""
    if not context.args:
        await update.message.reply_text("Uso: /configura_modem <WR>")
        return

    wr = context.args[0]
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        work = db.query(Work).filter(
            Work.numero_wr == wr,
            Work.tecnico_assegnato_id == tech.id,
        ).first()

        if not work:
            await update.message.reply_text("❌ Lavoro non trovato o non assegnato a te.")
            return

        if not work.modem:
            await update.message.reply_text("Nessun modem assegnato a questo lavoro.")
            return

        m = work.modem
        text = f"⚙️ Configurazione Modem WR {wr}\n\n"
        text += f"📶 Modello: {m.model}\n"
        text += f"🔢 SN: {m.serial_number}\n\n"

        if m.wifi_ssid and m.wifi_password:
            text += f"📶 WiFi SSID: {m.wifi_ssid}\n"
            text += f"🔑 Password: {m.wifi_password}\n\n"

        if m.admin_username and m.admin_password:
            text += f"👤 Admin: {m.admin_username}\n"
            text += f"🔑 Pass: {m.admin_password}\n\n"

        if m.sync_method:
            text += f"🔗 Sync: {m.sync_method}\n"

        if m.configuration_notes:
            text += f"📝 Note:\n{m.configuration_notes}\n"

        await update.message.reply_text(text)


async def installa_modem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Segna modem come installato."""
    if not context.args:
        await update.message.reply_text("Uso: /installa_modem <WR>")
        return

    wr = context.args[0]
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        work = db.query(Work).filter(
            Work.numero_wr == wr,
            Work.tecnico_assegnato_id == tech.id,
        ).first()

        if not work:
            await update.message.reply_text("❌ Lavoro non trovato o non assegnato a te.")
            return

        if not work.modem:
            await update.message.reply_text("Nessun modem assegnato a questo lavoro.")
            return

        if work.modem.status != "assigned":
            await update.message.reply_text(
                "Il modem deve essere in stato 'assigned' per essere installato."
            )
            return

        work.modem.status = "installed"
        work.modem.installed_at = datetime.utcnow()

        try:
            db.commit()
            await update.message.reply_text("✅ Modem segnato come installato.")
        except Exception as e:
            db.rollback()
            logger.error("Errore installa_modem WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
