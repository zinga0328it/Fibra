"""
app/bot/cmd_aggiorna_note.py - Comando /aggiorna_note <modello_modem> <note>.

Aggiorna le note di configurazione su TUTTI i modem dello stesso modello.
Così ogni tecnico vede le stesse istruzioni con /configura_modem.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Modem


async def aggiorna_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        with get_db_session() as db:
            modelli = db.query(Modem.model).distinct().all()
            lista = "\n".join(f"  • {m[0]}" for m in modelli) if modelli else "Nessun modello"

        await update.message.reply_text(
            "Uso: /aggiorna_note <modello_modem> <note>\n\n"
            f"📶 Modelli disponibili:\n{lista}\n\n"
            "Esempio:\n"
            "/aggiorna_note TIM HUB+ PPPoE auto, WiFi canale 36"
        )
        return

    telegram_id = str(update.effective_user.id)
    all_args = " ".join(context.args)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        modelli = [m[0] for m in db.query(Modem.model).distinct().all()]

        # Match modello più lungo possibile
        modello_trovato = None
        note = None
        for modello in sorted(modelli, key=len, reverse=True):
            if all_args.lower().startswith(modello.lower()):
                modello_trovato = modello
                note = all_args[len(modello):].strip()
                break

        if not modello_trovato or not note:
            await update.message.reply_text(
                "❌ Modello non trovato o note mancanti.\n"
                "Uso: /aggiorna_note <modello_modem> <note>"
            )
            return

        modem_aggiornati = db.query(Modem).filter(Modem.model == modello_trovato).all()
        count = 0
        for m in modem_aggiornati:
            m.configuration_notes = note
            count += 1

        try:
            db.commit()
            await update.message.reply_text(
                f"✅ Note aggiornate per: {modello_trovato}\n"
                f"📊 Modem aggiornati: {count}\n"
                f"📝 Note: {note}"
            )
        except Exception as e:
            db.rollback()
            logger.error("Errore aggiorna_note %s: %s", modello_trovato, e)
            await update.message.reply_text(f"❌ Errore: {e}")
