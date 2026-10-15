"""
app/bot/cmd_chiudi.py - Comando /chiudi <WR> <note tecniche>.

Chiude un lavoro e registra:
- stato → chiuso
- data_chiusura → now
- tecnico_chiusura_id → id del tecnico che ha chiuso (tracciabilità)
- note_chiusura → campo libero scritto dal tecnico (obbligatorio)
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, WorkEvent
import app.utils.telegram as telegram_utils
from datetime import datetime


SECRETARY_TELEGRAM_ID = os.getenv("SECRETARY_TELEGRAM_ID", "7586394272")


async def chiudi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 Come si usa:\n"
            "/chiudi <WR> <note tecniche>\n\n"
            "Esempio:\n"
            "/chiudi 95005055 Installato ONT e modem, tutto ok, "
            "cliente soddisfatto\n\n"
            "⚠️ Le note sono obbligatorie!"
        )
        return

    wr = context.args[0]
    # Tutto ciò che viene dopo il WR è la nota libera del tecnico
    note_chiusura = " ".join(context.args[1:])
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

        work.stato = "chiuso"
        work.data_chiusura = datetime.now()
        work.tecnico_chiusura_id = tech.id
        work.note_chiusura = note_chiusura

        # Auto-stato tecnico: occupato solo se rimangono lavori in corso
        db.flush()
        has_in_corso = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).first()
        tech.stato_posizione = "occupato" if has_in_corso else "disponibile"

        event = WorkEvent(
            work_id=work.id,
            timestamp=datetime.now(),
            event_type="closed",
            description=f"Chiuso da {tech.nome} {tech.cognome} | Note: {note_chiusura}",
            user_id=tech.id,
        )
        db.add(event)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore chiudi WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        modem_info = ""
        if work.modem_sn:
            modem_info = f"📶 Modem: {work.modem_sn}\n"

        await update.message.reply_text(
            f"✅ Lavoro {wr} chiuso!\n"
            f"👷 Completato da: {tech.nome} {tech.cognome}\n"
            f"📍 {work.indirizzo or 'N/D'}\n"
            f"{modem_info}"
            f"📝 Note: {note_chiusura}"
        )

        if SECRETARY_TELEGRAM_ID:
            secretary_msg = (
                f"📥 Chiusura da registrare\n\n"
                f"WR: {wr}\n"
                f"Tecnico: {tech.nome} {tech.cognome}\n"
                f"Operatore: {work.operatore or 'N/D'}\n"
                f"Cliente: {work.nome_cliente or 'N/D'}\n"
                f"Indirizzo: {work.indirizzo or 'N/D'}\n"
                f"Data chiusura: {work.data_chiusura}\n"
                f"Note tecnico:\n{note_chiusura}"
            )
            sent = telegram_utils.send_message_to_telegram(
                SECRETARY_TELEGRAM_ID,
                secretary_msg,
            )
            if not sent:
                logger.warning(
                    "Notifica chiusura non inviata alla segreteria per WR %s",
                    wr,
                )
