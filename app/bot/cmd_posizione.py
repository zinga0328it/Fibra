"""
app/bot/cmd_posizione.py - Comando /posizione.

Il tecnico invia la sua posizione GPS via Telegram.
Due modalità:
1. /posizione (poi invia location Telegram → il bot lo cattura)
2. Il tecnico può inviare direttamente una posizione Telegram (location message)

Salva lat/lng nel DB, attiva tracking, aggiorna timestamp.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, KEYBOARD, logger
from app.models.models import Work
from datetime import datetime


async def posizione(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /posizione - chiede al tecnico di inviare la posizione."""
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

    await update.message.reply_text(
        "📍 Invia la tua posizione usando il pulsante 📎 → Posizione di Telegram.\n\n"
        "La tua posizione verrà aggiornata sulla mappa della centrale operativa.",
        reply_markup=KEYBOARD,
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler per i messaggi di tipo Location.
    Si attiva quando un tecnico invia la sua posizione GPS da Telegram.
    """
    location = update.message.location
    if not location:
        return

    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato nel sistema.")
            return

        tech.lat = location.latitude
        tech.lng = location.longitude
        tech.last_position_update = datetime.now()
        tech.tracking_attivo = True

        # Mantiene aggiornata anche la posizione dei lavori in corso assegnati al tecnico
        in_corso_works = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).all()
        for work in in_corso_works:
            work.lat = location.latitude
            work.lng = location.longitude

        # Se era offline, diventa disponibile
        if tech.stato_posizione == "offline":
            tech.stato_posizione = "disponibile"

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore salvataggio posizione tech %d: %s", tech.id, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        await update.message.reply_text(
            f"✅ Posizione aggiornata!\n"
            f"📍 Lat: {location.latitude:.6f}, Lng: {location.longitude:.6f}\n"
            f"🟢 Stato: {tech.stato_posizione}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            reply_markup=KEYBOARD,
        )
