"""
app/bot/cmd_miei_lavori.py - Comando /miei_lavori.

Mostra TUTTI i lavori attivi (assegnato, in_corso, sospeso)
non archiviati, assegnati al tecnico identificato tramite telegram_id.
Raggruppa per stato e ordina per data appuntamento.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.core import get_db_session, find_technician, logger
from app.models.models import Work
from datetime import datetime

STATO_EMOJI = {
    "assegnato": "🆕",
    "in_corso": "🔧",
    "sospeso": "⏸️",
}


async def miei_lavori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    with get_db_session() as db:
        tech = find_technician(db, telegram_id)
        if not tech:
            await update.message.reply_text(
                "❌ Non sei registrato come tecnico. Contatta l'admin."
            )
            return

        # Tutti i lavori ATTIVI (assegnato, in_corso, sospeso), NON archiviati
        works = (
            db.query(Work)
            .filter(
                Work.tecnico_assegnato_id == tech.id,
                Work.stato.in_(["assegnato", "in_corso", "sospeso"]),
                Work.archived == False,
            )
            .order_by(Work.data_appuntamento.asc().nullslast())
            .all()
        )

        if not works:
            await update.message.reply_text(
                "✅ Non hai lavori attivi al momento."
            )
            return

        today = datetime.now().date()

        # Raggruppa per stato
        by_stato = {}
        for w in works:
            by_stato.setdefault(w.stato, []).append(w)

        parts = []
        for stato in ["in_corso", "assegnato", "sospeso"]:
            gruppo = by_stato.get(stato, [])
            if not gruppo:
                continue

            emoji = STATO_EMOJI.get(stato, "📋")
            header = f"{emoji} {stato.upper().replace('_', ' ')} ({len(gruppo)}):"
            lines = []
            for w in gruppo:
                line = f"📋 WR {w.numero_wr}\n📍 {w.indirizzo or 'N/D'}"
                if w.nome_cliente:
                    line += f"\n👤 {w.nome_cliente}"
                if w.tipo_lavoro:
                    line += f"\n🔧 {w.tipo_lavoro}"
                if w.modem_sn:
                    line += f"\n📦 Modem: {w.modem_sn}"
                if w.motivo_rinvio:
                    line += f"\n⚠️ Motivo: {w.motivo_rinvio}"
                if w.note_appuntamento:
                    line += f"\n📝 {w.note_appuntamento}"

                if w.data_appuntamento:
                    data_str = w.data_appuntamento.strftime("%d/%m/%Y %H:%M")
                    if w.data_appuntamento.date() == today:
                        line += f"\n📅 OGGI {data_str}"
                    elif w.data_appuntamento.date() < today:
                        line += f"\n📅 ⚠️ SCADUTO {data_str}"
                    else:
                        line += f"\n📅 {data_str}"
                lines.append(line)

            parts.append(header + "\n\n" + "\n\n".join(lines))

        text = (
            f"📊 I tuoi lavori attivi: {len(works)}\n\n"
            + "\n\n---\n\n".join(parts)
        )

    await update.message.reply_text(text)
