"""
app/bot/cmd_sync.py - Comando /sync_status <WR>.

Mostra stato sincronizzazione ONT-Modem per un lavoro.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, ONT, Modem, ONTModemSync


async def sync_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /sync_status <WR>")
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

        syncs = db.query(ONTModemSync).filter(ONTModemSync.work_id == work.id).all()

        if not syncs:
            await update.message.reply_text("Nessuna sincronizzazione per questo lavoro.")
            return

        text = f"🔗 Sincronizzazione WR {wr}\n\n"
        for s in syncs:
            ont = db.query(ONT).filter(ONT.id == s.ont_id).first()
            modem = db.query(Modem).filter(Modem.id == s.modem_id).first()

            text += f"📡 ONT: {ont.serial_number if ont else 'N/A'}\n"
            text += f"📶 Modem: {modem.serial_number if modem else 'N/A'}\n"
            text += f"🔗 Metodo: {s.sync_method}\n"
            text += f"📊 Stato: {s.sync_status}\n"
            if s.synced_at:
                text += f"✅ Sincronizzato: {s.synced_at.strftime('%d/%m/%Y %H:%M')}\n"
            if s.technician_notes:
                text += f"📝 {s.technician_notes[:100]}\n"
            text += "\n"

        await update.message.reply_text(text)
