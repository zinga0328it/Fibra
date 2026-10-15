"""
app/bot/cmd_istruzioni.py - Comando /istruzioni <WR>.

Mostra istruzioni di installazione dispositivi per un lavoro.
TODO: Sarà riscritto nella prossima iterazione con supporto modem avanzato.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, ONTModemSync


async def istruzioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /istruzioni <WR>")
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

        ont = work.ont
        modem = work.modem
        sync = db.query(ONTModemSync).filter(ONTModemSync.work_id == work.id).first()

        text = f"📋 Istruzioni per WR {wr}\n"
        text += f"📍 {work.indirizzo or 'N/D'}\n\n"

        if ont:
            text += f"📡 ONT: {ont.model} (SN: {ont.serial_number})\n"
        if modem:
            text += f"📶 Modem: {modem.model} (SN: {modem.serial_number})\n"
        if sync:
            text += f"🔗 Sync: {sync.sync_method}\n"
            if sync.wifi_ssid:
                text += f"📶 WiFi: {sync.wifi_ssid}\n"

        text += "\n🔧 Procedura:\n"
        text += "1. Collega ONT alla fibra ottica\n"
        text += "2. Configura PPPoE sul modem\n"
        text += "3. Sincronizza ONT-Modem\n"
        text += "4. Verifica connessione internet\n"
        text += "5. Usa /aggiorna_note per salvare configurazione"

        await update.message.reply_text(text)
