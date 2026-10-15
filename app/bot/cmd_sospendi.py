"""
app/bot/cmd_sospendi.py - Comando /sospendi <WR> <motivo> [data GG/MM/AAAA HH:MM].

Sospende un lavoro con un motivo obbligatorio e una data di riprogrammazione opzionale.
Motivi validi: pioggia, cavo_finito, scala_insufficiente, cliente_assente, problema_logistico, altro.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work, WorkEvent
from datetime import datetime

MOTIVI_VALIDI = [
    "pioggia",
    "cavo_finito",
    "scala_insufficiente",
    "cliente_assente",
    "problema_logistico",
    "altro",
]


async def sospendi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        motivi_str = "\n".join(f"  • {m}" for m in MOTIVI_VALIDI)
        await update.message.reply_text(
            "Uso: /sospendi <WR> <motivo> [data GG/MM/AAAA HH:MM]\n\n"
            f"Motivi disponibili:\n{motivi_str}\n\n"
            "Esempi:\n"
            "/sospendi 95005055 pioggia\n"
            "/sospendi 95005055 cliente_assente 25/03/2026 09:00"
        )
        return

    wr = context.args[0]
    motivo = context.args[1].lower()

    if motivo not in MOTIVI_VALIDI:
        await update.message.reply_text(
            f"❌ Motivo '{motivo}' non valido.\n"
            f"Validi: {', '.join(MOTIVI_VALIDI)}"
        )
        return

    # Parse data opzionale
    nuova_data = None
    if len(context.args) >= 4:
        data_str = f"{context.args[2]} {context.args[3]}"
        try:
            nuova_data = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
        except ValueError:
            await update.message.reply_text(
                "❌ Formato data non valido. Usa: GG/MM/AAAA HH:MM"
            )
            return
    elif len(context.args) == 3:
        try:
            nuova_data = datetime.strptime(context.args[2], "%d/%m/%Y")
            nuova_data = nuova_data.replace(hour=9, minute=0)
        except ValueError:
            await update.message.reply_text(
                "❌ Formato data non valido. Usa: GG/MM/AAAA [HH:MM]"
            )
            return

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

        if work.stato == "chiuso":
            await update.message.reply_text("❌ Il lavoro è già chiuso.")
            return

        work.stato = "sospeso"
        work.motivo_rinvio = motivo
        if nuova_data:
            work.data_appuntamento = nuova_data

        db.flush()
        has_in_corso = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).first()
        tech.stato_posizione = "occupato" if has_in_corso else "disponibile"

        desc = f"Sospeso per {motivo}"
        if nuova_data:
            desc += f", riprogrammato {nuova_data.strftime('%d/%m/%Y %H:%M')}"

        event = WorkEvent(
            work_id=work.id,
            timestamp=datetime.now(),
            event_type="suspended",
            description=desc,
            user_id=tech.id,
        )
        db.add(event)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore sospendi WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        text = f"⏸️ Lavoro {wr} sospeso\n"
        text += f"📋 Motivo: {motivo}\n"
        if nuova_data:
            text += f"📅 Riprogrammato: {nuova_data.strftime('%d/%m/%Y %H:%M')}\n"
        else:
            text += "📅 Nessuna data di riprogrammazione\n"
        text += f"📍 {work.indirizzo or 'N/D'}"
        await update.message.reply_text(text)
