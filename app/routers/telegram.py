"""
Telegram webhook router for Gestionale Fibra.

Handles incoming Telegram webhook updates.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.telegram.bot import telegram_bot
from app.telegram.handlers import (
    handle_accept_job,
    handle_close_job,
    handle_photo,
    handle_refuse_job,
)
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
)


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Handle incoming Telegram webhook updates.
    
    Processes callback queries and messages from the Telegram bot.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        dict: Response status
    """
    try:
        data = await request.json()
        logger.info("Received Telegram webhook", data=data)
        
        # Handle callback queries (button presses)
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback.get("data", "")
            chat_id = str(callback["message"]["chat"]["id"])
            
            # Parse callback action and job ID
            if "_" in callback_data:
                action, job_id_str = callback_data.split("_", 1)
                job_id = int(job_id_str)
                
                if action == "accept":
                    success, message = await handle_accept_job(job_id, chat_id, db)
                elif action == "refuse":
                    success, message = await handle_refuse_job(job_id, chat_id, db)
                elif action == "close":
                    success, message = await handle_close_job(job_id, chat_id, db)
                else:
                    message = "Azione non riconosciuta."
                    success = False
                
                # Send response
                await telegram_bot.send_message(chat_id, message)
                
                if success and action == "accept":
                    await telegram_bot.send_job_in_progress_options(chat_id, job_id)
        
        # Handle photo messages
        elif "message" in data and "photo" in data["message"]:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            
            # Get the largest photo
            photos = message["photo"]
            photo = photos[-1] if photos else None
            
            if photo:
                photo_file_id = photo["file_id"]
                
                # Check if there's an active job for this technician
                # (In production, you'd look up the active job for this chat_id)
                # For now, we'll just log the photo
                logger.info(
                    "Photo received",
                    chat_id=chat_id,
                    file_id=photo_file_id,
                )
                
                await telegram_bot.send_message(
                    chat_id,
                    "📸 Foto ricevuta. Per associarla a un lavoro, usa il pulsante 'Invia Foto' dal menu del lavoro.",
                )
        
        # Handle text messages
        elif "message" in data and "text" in data["message"]:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            text = message["text"]
            
            if text.startswith("/start"):
                welcome = (
                    "👋 <b>Benvenuto a Gestionale Fibra!</b>\n\n"
                    f"Il tuo ID Telegram: <code>{chat_id}</code>\n\n"
                    "Comunica questo ID all'amministratore per collegare il tuo account."
                )
                await telegram_bot.send_message(chat_id, welcome)
            
            elif text.startswith("/aiuto") or text.startswith("/help"):
                help_text = (
                    "📚 <b>Guida Comandi</b>\n\n"
                    "/start - Registrazione e ID Telegram\n"
                    "/lavori - Mostra lavori assegnati\n"
                    "/aiuto - Questa guida\n\n"
                    "<b>Quando ricevi un lavoro:</b>\n"
                    "✅ Premi 'Accetta' per accettare\n"
                    "❌ Premi 'Rifiuta' per rifiutare\n\n"
                    "<b>Durante il lavoro:</b>\n"
                    "📸 Invia foto per documentare\n"
                    "✅ Premi 'Chiudi' al termine"
                )
                await telegram_bot.send_message(chat_id, help_text)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error("Error processing webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook",
        )


@router.get("/set-webhook")
async def set_telegram_webhook(
    url: str = None,
) -> dict[str, Any]:
    """
    Set the Telegram webhook URL.
    
    Args:
        url: Optional webhook URL (uses config if not provided)
        
    Returns:
        dict: Operation result
    """
    success = await telegram_bot.set_webhook(url)
    return {"success": success}
