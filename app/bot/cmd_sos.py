"""
app/bot/cmd_sos.py - Comando /sos.

Il tecnico invia SOS quando è in difficoltà.
Il sistema:
1. Marca il tecnico come stato 'sos'
2. Trova i 3 tecnici disponibili più vicini (Haversine)
3. Notifica il tecnico più vicino via Telegram
4. Notifica la segretaria (se configurata)
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, KEYBOARD, logger
from app.models.models import Technician
from app.utils.geo import find_nearest_technicians
import app.utils.telegram as telegram_utils


async def sos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /sos - attiva emergenza e cerca il tecnico più vicino."""
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text("❌ Tecnico non trovato.")
            return

        if not tech.lat or not tech.lng:
            await update.message.reply_text(
                "❌ Non hai una posizione GPS salvata!\n\n"
                "Invia prima la tua posizione con il pulsante 📎 → Posizione,\n"
                "poi riprova /sos.",
                reply_markup=KEYBOARD,
            )
            return

        # Marca come SOS
        tech.stato_posizione = "sos"
        db.commit()

        # Trova tecnici più vicini
        nearest = find_nearest_technicians(
            db,
            target_lat=tech.lat,
            target_lng=tech.lng,
            limit=3,
            exclude_id=tech.id,
        )

        tech_name = f"{tech.nome} {tech.cognome}"

        if not nearest:
            await update.message.reply_text(
                f"🚨 SOS attivato!\n\n"
                f"⚠️ Nessun tecnico disponibile trovato nelle vicinanze.\n"
                f"📞 Contatta la segretaria.",
                reply_markup=KEYBOARD,
            )
            return

        # Costruisci messaggio risposta
        text = f"🚨 *SOS ATTIVATO!*\n\n"
        text += f"📍 La tua posizione è stata segnalata.\n\n"
        text += f"*Tecnici più vicini:*\n"
        for i, item in enumerate(nearest, 1):
            t = item["technician"]
            dist = item["distance_km"]
            text += f"{i}. {t.nome} {t.cognome} - {dist} km - 📞 {t.telefono}\n"

        text += f"\n✅ Notifica inviata a {nearest[0]['technician'].nome} {nearest[0]['technician'].cognome}"

        await update.message.reply_text(text, reply_markup=KEYBOARD)

        # Notifica il tecnico più vicino
        closest = nearest[0]["technician"]
        _notify_closest(closest, tech, nearest[0]["distance_km"], db)


def _notify_closest(closest: Technician, sos_tech: Technician, distance_km: float, db):
    """Invia notifica Telegram al tecnico più vicino."""
    try:
        if closest.telegram_id:
            msg = (
                f"🚨 SOS da {sos_tech.nome} {sos_tech.cognome}!\n\n"
                f"📍 È a {distance_km} km da te.\n"
                f"📞 Telefono: {sos_tech.telefono}\n\n"
                f"Sei il tecnico disponibile più vicino.\n"
                f"Contattalo o recati da lui."
            )
            telegram_utils.send_message_to_telegram(closest.telegram_id, msg)
            logger.info("SOS notification sent to tech %d from tech %d", closest.id, sos_tech.id)
    except Exception as e:
        logger.error("Failed to send SOS notification: %s", e)
