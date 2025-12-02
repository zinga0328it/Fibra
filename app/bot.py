from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto nel bot FTTH!")

async def miei_lavori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        works = db.query(Work).filter(Work.tecnico_assegnato_id == tech.id).all()
        text = "\n".join([f"WR {w.numero_wr} - {w.stato} - {w.indirizzo}" for w in works])
    await update.message.reply_text(text or "Nessun lavoro assegnato")

async def accetta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /accetta <WR>")
        return
    wr = context.args[0]
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if work:
            work.stato = "in_corso"
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="accepted", description="Accepted by tech", user_id=tech.id)
            db.add(event)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                await update.message.reply_text(f"Errore aggiornamento: {e}")
                return
            await update.message.reply_text("Lavoro accettato")
        else:
            await update.message.reply_text("Lavoro non trovato")

async def rifiuta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /rifiuta <WR>")
        return
    wr = context.args[0]
    telegram_id = str(update.effective_user.id)
    with SessionLocal() as db:
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            await update.message.reply_text("Tecnico non trovato. Contatta l'admin.")
            return
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if work:
            work.stato = "aperto"
            work.tecnico_assegnato_id = None
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="rejected", description="Rejected by tech", user_id=tech.id)
            db.add(event)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                await update.message.reply_text(f"Errore aggiornamento: {e}")
                return
            await update.message.reply_text("Lavoro rifiutato")
        else:
            await update.message.reply_text("Lavoro non trovato")

# Add more handlers for chiudi, problema, etc.

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("miei_lavori", miei_lavori))
    application.add_handler(CommandHandler("accetta", accetta))
    application.add_handler(CommandHandler("rifiuta", rifiuta))
    application.run_polling()

if __name__ == '__main__':
    main()