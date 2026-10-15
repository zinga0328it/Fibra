"""
app/bot/cmd_fine_sos.py - Comando /fine_sos.

Il tecnico disattiva manualmente lo stato SOS.
Il sistema:
1. Verifica che il tecnico sia in stato 'sos'
2. Controlla se ha lavori in_corso
3. Aggiorna lo stato a 'disponibile', 'occupato' o 'offline'
4. NON tocca la tabella works (solo technicians.stato_posizione)
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, KEYBOARD, logger
from app.models.models import Work


async def fine_sos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /fine_sos - disattiva manualmente lo stato SOS."""
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        old_status = tech.stato_posizione

        # Verifica se è effettivamente in SOS
        if old_status != "sos":
            await update.message.reply_text(
                f"ℹ️ Non sei in stato SOS.\n"
                f"Stato attuale: *{old_status}*",
                reply_markup=KEYBOARD,
            )
            return

        # Controlla se ha lavori in corso
        has_in_corso = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).first()

        # Calcola nuovo stato
        if not tech.tracking_attivo:
            new_status = "offline"
        else:
            new_status = "occupato" if has_in_corso else "disponibile"

        # Aggiorna SOLO stato tecnico
        tech.stato_posizione = new_status
        db.commit()

        logger.info(
            "Tech %d (%s) cleared SOS: %s → %s",
            tech.id,
            tech.telegram_id,
            old_status,
            new_status,
        )

        # Emoji per stato
        emoji_map = {
            "disponibile": "🟢",
            "occupato": "🟠",
            "offline": "⚫",
        }
        emoji = emoji_map.get(new_status, "🔵")

        await update.message.reply_text(
            f"✅ *SOS DISATTIVATO*\n\n"
            f"{emoji} Nuovo stato: *{new_status}*",
            reply_markup=KEYBOARD,
            parse_mode="Markdown",
        )
