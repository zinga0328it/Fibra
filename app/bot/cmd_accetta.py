"""
app/bot/cmd_accetta.py - Comando /accetta <WR>.

Il tecnico accetta un lavoro assegnato a lui: stato → in_corso.
Se il lavoro ha ONT e Modem, crea automaticamente la sincronizzazione.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, KEYBOARD, logger
from app.models.models import Work, WorkEvent, ONTModemSync
from datetime import datetime


async def accetta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /accetta <WR>")
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
            await update.message.reply_text("❌ Il lavoro è già chiuso.")
            return

        work.stato = "in_corso"

        # Auto-stato tecnico: occupato + tracking attivo
        tech.stato_posizione = "occupato"
        tech.tracking_attivo = True

        event = WorkEvent(
            work_id=work.id,
            timestamp=datetime.now(),
            event_type="accepted",
            description=f"Accettato da {tech.nome} {tech.cognome} via Telegram",
            user_id=tech.id,
        )
        db.add(event)

        # Testo risposta
        text = f"▶️ Lavoro {wr} accettato!\n"
        text += f"📍 {work.indirizzo or 'N/D'}\n"

        if work.ont or work.modem:
            text += "\n📡 Equipaggiamento:\n"
            if work.ont:
                text += f"  • ONT: {work.ont.model} (SN: {work.ont.serial_number})\n"
            if work.modem:
                text += f"  • Modem: {work.modem.model} (SN: {work.modem.serial_number})\n"
                if work.modem.wifi_ssid:
                    text += f"  • WiFi: {work.modem.wifi_ssid}\n"

        # Mostra note tecniche (splitter, porta, ecc.)
        # Controlla prima il campo 'note' principale, poi 'extra_fields.note' se vuoto
        note_tecniche = work.note
        if not note_tecniche and work.extra_fields and work.extra_fields.get('note'):
            note_tecniche = work.extra_fields.get('note')

        if note_tecniche:
            text += f"\n📝 Note tecniche:\n{note_tecniche}\n"

        # Auto-crea sincronizzazione ONT-Modem
        if work.ont and work.modem:
            existing = db.query(ONTModemSync).filter(
                ONTModemSync.work_id == work.id
            ).first()
            if not existing:
                sync = ONTModemSync(
                    work_id=work.id,
                    ont_id=work.ont.id,
                    modem_id=work.modem.id,
                    sync_method=work.modem.sync_method or "auto",
                    sync_status="pending",
                    wifi_ssid=work.modem.wifi_ssid,
                )
                db.add(sync)
                text += "\n✅ Sincronizzazione ONT-Modem creata"

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Errore accetta WR %s: %s", wr, e)
            await update.message.reply_text(f"❌ Errore: {e}")
            return

        text += "\n\nUsa /istruzioni per le istruzioni di installazione"
        await update.message.reply_text(text)

        if tech.lat is None or tech.lng is None:
            await update.message.reply_text(
                "⚠️ Posizione GPS non disponibile. Invia ora la posizione con /posizione "
                "(📎 → Posizione) per aggiornare la centrale operativa.",
                reply_markup=KEYBOARD,
            )
