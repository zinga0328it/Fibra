"""
app/bot/cmd_modem.py - Comando /modem <WR> <seriale>.

Il tecnico registra il seriale del modem installato per un lavoro.
Semplice: basta il numero WR e il seriale scritto sul modem.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, WorkEvent
from datetime import datetime


async def modem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📶 Come si usa:\n"
            "/modem <WR> <seriale modem>\n\n"
            "Esempio:\n"
            "/modem 95005055 ZTEGC4B1A2C3\n\n"
            "Scrivi il seriale che trovi sull'etichetta del modem."
        )
        return

    wr = context.args[0]
    modem_sn = " ".join(context.args[1:])
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
            await update.message.reply_text(
                f"❌ Lavoro {wr} non trovato o non assegnato a te."
            )
            return

        if work.stato == "chiuso":
            await update.message.reply_text("❌ Il lavoro è già chiuso.")
            return

        old_sn = work.modem_sn
        work.modem_sn = modem_sn

        event = WorkEvent(
            work_id=work.id,
            timestamp=datetime.now(),
            event_type="modem_registered",
            description=f"Modem SN: {modem_sn} registrato da {tech.nome} {tech.cognome}",
            user_id=tech.id,
        )
        db.add(event)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore modem WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        if old_sn:
            await update.message.reply_text(
                f"✅ Modem aggiornato per WR {wr}\n"
                f"📶 Vecchio: {old_sn}\n"
                f"📶 Nuovo: {modem_sn}"
            )
        else:
            await update.message.reply_text(
                f"✅ Modem registrato per WR {wr}\n"
                f"📶 Seriale: {modem_sn}"
            )
