"""
app/bot/cmd_rifiuta.py - Comando /rifiuta <WR>.

Il tecnico rifiuta un lavoro: stato → aperto, tecnico_assegnato → None.
Il lavoro torna disponibile per essere riassegnato.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, WorkEvent
from datetime import datetime


async def rifiuta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /rifiuta <WR>")
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
            await update.message.reply_text(
                f"❌ Lavoro {wr} non trovato o non assegnato a te."
            )
            return

        if work.stato == "chiuso":
            await update.message.reply_text("❌ Il lavoro è già chiuso, non puoi rifiutarlo.")
            return

        old_stato = work.stato
        work.stato = "aperto"
        work.tecnico_assegnato_id = None

        event = WorkEvent(
            work_id=work.id,
            timestamp=datetime.now(),
            event_type="rejected",
            description=f"Rifiutato da {tech.nome} {tech.cognome} via Telegram",
            user_id=tech.id,
        )
        db.add(event)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore rifiuta WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        await update.message.reply_text(
            f"⏸️ Lavoro {wr} rifiutato.\n"
            f"Il lavoro torna disponibile per riassegnazione."
        )
