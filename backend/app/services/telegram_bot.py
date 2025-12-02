"""
Telegram Bot for Gestionale Fibra

This bot allows technicians to:
- Receive notifications about new jobs
- View their assigned jobs
- Update job status
- Close jobs
- Upload photos
"""

import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from sqlalchemy.orm import Session
import os
import uuid

from app.config import settings
from app.database import SessionLocal
from app.models import Job, Technician, Photo, JobStatus

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        technician = db.query(Technician).filter(
            Technician.telegram_chat_id == chat_id
        ).first()
        
        if technician:
            await update.message.reply_text(
                f"Ciao {technician.name}! Bentornato nel Gestionale Fibra.\n\n"
                "Comandi disponibili:\n"
                "/jobs - Visualizza i tuoi lavori\n"
                "/help - Mostra aiuto"
            )
        else:
            await update.message.reply_text(
                f"Benvenuto nel Gestionale Fibra!\n\n"
                f"Il tuo Chat ID è: {chat_id}\n\n"
                "Comunica questo ID all'amministratore per associare "
                "il tuo account Telegram al sistema."
            )
    finally:
        db.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    help_text = (
        "📋 Comandi disponibili:\n\n"
        "/start - Avvia il bot\n"
        "/jobs - Visualizza i tuoi lavori assegnati\n"
        "/job <id> - Dettagli di un lavoro specifico\n"
        "/close <id> - Chiudi un lavoro\n"
        "/help - Mostra questo messaggio\n\n"
        "📷 Puoi inviare foto direttamente in chat, "
        "poi selezionare il lavoro a cui associarle."
    )
    await update.message.reply_text(help_text)


async def list_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all jobs assigned to the technician."""
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        technician = db.query(Technician).filter(
            Technician.telegram_chat_id == chat_id
        ).first()
        
        if not technician:
            await update.message.reply_text(
                "⚠️ Il tuo account Telegram non è associato al sistema.\n"
                "Contatta l'amministratore."
            )
            return
        
        jobs = db.query(Job).filter(
            Job.technician_id == technician.id,
            Job.status.in_([JobStatus.OPEN, JobStatus.IN_PROGRESS, JobStatus.PAUSED])
        ).order_by(Job.created_at.desc()).all()
        
        if not jobs:
            await update.message.reply_text(
                "Non hai lavori assegnati al momento."
            )
            return
        
        keyboard = []
        for job in jobs:
            status_emoji = {
                JobStatus.OPEN: "🟢",
                JobStatus.IN_PROGRESS: "🟡",
                JobStatus.PAUSED: "⏸️"
            }.get(job.status, "⚪")
            
            text = f"{status_emoji} #{job.id} - {job.customer_name or 'N/A'}"
            keyboard.append([InlineKeyboardButton(
                text,
                callback_data=f"job_{job.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📋 I tuoi lavori ({len(jobs)}):",
            reply_markup=reply_markup
        )
    finally:
        db.close()


async def job_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show details of a specific job."""
    if not context.args:
        await update.message.reply_text("Uso: /job <id>")
        return
    
    try:
        job_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID lavoro non valido.")
        return
    
    await show_job_detail(update, job_id)


async def show_job_detail(update: Update, job_id: int, is_callback: bool = False):
    """Helper to show job details."""
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        technician = db.query(Technician).filter(
            Technician.telegram_chat_id == chat_id
        ).first()
        
        if not technician:
            msg = "⚠️ Account non associato."
            if is_callback:
                await update.callback_query.answer(msg)
            else:
                await update.message.reply_text(msg)
            return
        
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.technician_id == technician.id
        ).first()
        
        if not job:
            msg = "Lavoro non trovato o non assegnato a te."
            if is_callback:
                await update.callback_query.answer(msg)
            else:
                await update.message.reply_text(msg)
            return
        
        status_text = {
            JobStatus.OPEN: "🟢 Aperto",
            JobStatus.IN_PROGRESS: "🟡 In Corso",
            JobStatus.PAUSED: "⏸️ In Pausa",
            JobStatus.CLOSED: "✅ Chiuso"
        }.get(job.status, "⚪ Sconosciuto")
        
        detail_text = (
            f"📋 Lavoro #{job.id}\n\n"
            f"📦 Ordine: {job.work_order_number or 'N/A'}\n"
            f"👤 Cliente: {job.customer_name or 'N/A'}\n"
            f"📍 Indirizzo: {job.customer_address or 'N/A'}\n"
            f"📞 Telefono: {job.customer_phone or 'N/A'}\n"
            f"📝 Descrizione: {job.description or 'N/A'}\n"
            f"📊 Stato: {status_text}\n"
            f"📅 Creato: {job.created_at.strftime('%d/%m/%Y %H:%M')}"
        )
        
        keyboard = []
        if job.status != JobStatus.CLOSED:
            if job.status == JobStatus.OPEN:
                keyboard.append([InlineKeyboardButton(
                    "▶️ Inizia Lavoro",
                    callback_data=f"status_{job.id}_in_progress"
                )])
            elif job.status == JobStatus.IN_PROGRESS:
                keyboard.append([
                    InlineKeyboardButton(
                        "⏸️ Pausa",
                        callback_data=f"status_{job.id}_paused"
                    ),
                    InlineKeyboardButton(
                        "✅ Chiudi",
                        callback_data=f"status_{job.id}_closed"
                    )
                ])
            elif job.status == JobStatus.PAUSED:
                keyboard.append([
                    InlineKeyboardButton(
                        "▶️ Riprendi",
                        callback_data=f"status_{job.id}_in_progress"
                    ),
                    InlineKeyboardButton(
                        "✅ Chiudi",
                        callback_data=f"status_{job.id}_closed"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton(
                "📷 Carica Foto",
                callback_data=f"photo_{job.id}"
            )])
        
        keyboard.append([InlineKeyboardButton(
            "◀️ Torna alla lista",
            callback_data="list_jobs"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            await update.callback_query.edit_message_text(
                detail_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                detail_text,
                reply_markup=reply_markup
            )
    finally:
        db.close()


async def close_job_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close a job via command."""
    if not context.args:
        await update.message.reply_text("Uso: /close <id>")
        return
    
    try:
        job_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID lavoro non valido.")
        return
    
    await update_job_status(update, job_id, "closed", is_callback=False)


async def update_job_status(update: Update, job_id: int, new_status: str, is_callback: bool = True):
    """Update job status."""
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        technician = db.query(Technician).filter(
            Technician.telegram_chat_id == chat_id
        ).first()
        
        if not technician:
            msg = "⚠️ Account non associato."
            if is_callback:
                await update.callback_query.answer(msg)
            else:
                await update.message.reply_text(msg)
            return
        
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.technician_id == technician.id
        ).first()
        
        if not job:
            msg = "Lavoro non trovato o non assegnato a te."
            if is_callback:
                await update.callback_query.answer(msg)
            else:
                await update.message.reply_text(msg)
            return
        
        # Update status
        status_map = {
            "open": JobStatus.OPEN,
            "in_progress": JobStatus.IN_PROGRESS,
            "paused": JobStatus.PAUSED,
            "closed": JobStatus.CLOSED
        }
        
        job.status = status_map.get(new_status, JobStatus.OPEN)
        
        if new_status == "closed":
            from datetime import datetime
            job.closed_at = datetime.utcnow()
        
        db.commit()
        
        status_text = {
            "open": "🟢 Aperto",
            "in_progress": "🟡 In Corso",
            "paused": "⏸️ In Pausa",
            "closed": "✅ Chiuso"
        }.get(new_status, "Sconosciuto")
        
        msg = f"Lavoro #{job_id} aggiornato: {status_text}"
        
        if is_callback:
            await update.callback_query.answer(msg)
            # Refresh job detail view
            await show_job_detail(update, job_id, is_callback=True)
        else:
            await update.message.reply_text(msg)
    finally:
        db.close()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("job_"):
        job_id = int(data.split("_")[1])
        await show_job_detail(update, job_id, is_callback=True)
    
    elif data.startswith("status_"):
        parts = data.split("_")
        job_id = int(parts[1])
        new_status = "_".join(parts[2:])
        await update_job_status(update, job_id, new_status)
    
    elif data.startswith("photo_"):
        job_id = int(data.split("_")[1])
        context.user_data["awaiting_photo_for_job"] = job_id
        await query.edit_message_text(
            f"📷 Invia una foto per il lavoro #{job_id}.\n\n"
            "La foto verrà automaticamente associata al lavoro.\n"
            "Premi /cancel per annullare."
        )
    
    elif data == "list_jobs":
        # Need to create a fake update for list_jobs
        await list_jobs(update, context)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads."""
    chat_id = str(update.effective_chat.id)
    
    # Check if we're waiting for a photo for a specific job
    job_id = context.user_data.get("awaiting_photo_for_job")
    
    if not job_id:
        # Show job selection
        db = SessionLocal()
        try:
            technician = db.query(Technician).filter(
                Technician.telegram_chat_id == chat_id
            ).first()
            
            if not technician:
                await update.message.reply_text(
                    "⚠️ Account non associato al sistema."
                )
                return
            
            jobs = db.query(Job).filter(
                Job.technician_id == technician.id,
                Job.status.in_([JobStatus.OPEN, JobStatus.IN_PROGRESS, JobStatus.PAUSED])
            ).all()
            
            if not jobs:
                await update.message.reply_text(
                    "Non hai lavori attivi a cui associare la foto."
                )
                return
            
            keyboard = [[InlineKeyboardButton(
                f"#{job.id} - {job.customer_name or 'N/A'}",
                callback_data=f"assign_photo_{job.id}"
            )] for job in jobs]
            
            # Store the photo file_id temporarily
            photo = update.message.photo[-1]  # Get highest resolution
            context.user_data["pending_photo"] = photo.file_id
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📷 A quale lavoro vuoi associare questa foto?",
                reply_markup=reply_markup
            )
        finally:
            db.close()
        return
    
    # Clear the awaiting flag
    context.user_data.pop("awaiting_photo_for_job", None)
    
    # Save the photo
    await save_photo(update, context, job_id)


async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: int):
    """Save a photo for a job."""
    chat_id = str(update.effective_chat.id)
    
    db = SessionLocal()
    try:
        technician = db.query(Technician).filter(
            Technician.telegram_chat_id == chat_id
        ).first()
        
        if not technician:
            await update.message.reply_text("⚠️ Account non associato.")
            return
        
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.technician_id == technician.id
        ).first()
        
        if not job:
            await update.message.reply_text("Lavoro non trovato.")
            return
        
        # Get the photo
        photo = update.message.photo[-1]  # Highest resolution
        file = await context.bot.get_file(photo.file_id)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(settings.upload_dir, filename)
        
        # Ensure directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Download the photo
        await file.download_to_drive(file_path)
        
        # Create database record
        db_photo = Photo(
            job_id=job_id,
            filename=filename,
            original_filename=f"telegram_{photo.file_id}.jpg",
            uploaded_via="telegram"
        )
        db.add(db_photo)
        db.commit()
        
        await update.message.reply_text(
            f"✅ Foto caricata con successo per il lavoro #{job_id}!"
        )
    finally:
        db.close()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation."""
    context.user_data.clear()
    await update.message.reply_text("Operazione annullata.")


async def send_job_notification(chat_id: str, job: Job):
    """Send a notification about a new job to a technician."""
    if not settings.telegram_bot_token:
        return
    
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    message = (
        f"🆕 Nuovo lavoro assegnato!\n\n"
        f"📋 Lavoro #{job.id}\n"
        f"📦 Ordine: {job.work_order_number or 'N/A'}\n"
        f"👤 Cliente: {job.customer_name or 'N/A'}\n"
        f"📍 Indirizzo: {job.customer_address or 'N/A'}\n"
        f"📞 Telefono: {job.customer_phone or 'N/A'}\n"
        f"📝 Descrizione: {job.description or 'N/A'}"
    )
    
    keyboard = [[InlineKeyboardButton(
        "👁️ Visualizza Dettagli",
        callback_data=f"job_{job.id}"
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending notification: {e}")


def create_telegram_app() -> Optional[Application]:
    """Create the Telegram bot application."""
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured")
        return None
    
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("jobs", list_jobs))
    app.add_handler(CommandHandler("job", job_detail))
    app.add_handler(CommandHandler("close", close_job_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    return app


async def run_telegram_bot():
    """Run the Telegram bot."""
    app = create_telegram_app()
    if app:
        logger.info("Starting Telegram bot...")
        await app.run_polling()
