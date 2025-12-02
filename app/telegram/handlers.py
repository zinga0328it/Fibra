"""
Telegram bot command handlers for Gestionale Fibra.

Handles incoming updates from Telegram for job management.
"""

from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)


async def handle_start(update: Any, context: Any) -> None:
    """
    Handle the /start command.
    
    Registers the technician's Telegram ID and sends welcome message.
    
    Args:
        update: Telegram Update object
        context: Telegram Context object
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    welcome_message = (
        f"👋 <b>Benvenuto {user.first_name}!</b>\n\n"
        f"Questo è il bot di Gestionale Fibra per la gestione dei lavori.\n\n"
        f"Il tuo ID Telegram è: <code>{chat_id}</code>\n\n"
        f"Comunica questo ID all'amministratore per collegare il tuo account.\n\n"
        f"<b>Comandi disponibili:</b>\n"
        f"/start - Mostra questo messaggio\n"
        f"/lavori - Mostra i tuoi lavori assegnati\n"
        f"/aiuto - Mostra la guida"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="HTML",
    )
    
    logger.info(
        "User started bot",
        user_id=user.id,
        username=user.username,
        chat_id=chat_id,
    )


async def handle_accept_job(
    job_id: int,
    chat_id: str,
    db_session: Any,
) -> tuple[bool, str]:
    """
    Handle job acceptance callback.
    
    Updates the work order status to ACCEPTED.
    
    Args:
        job_id: Work order ID
        chat_id: Telegram chat ID
        db_session: Database session
        
    Returns:
        tuple[bool, str]: Success status and message
    """
    from sqlalchemy import select
    from app.models.work import Work, WorkStatus
    
    try:
        result = await db_session.execute(
            select(Work).where(Work.id == job_id)
        )
        work = result.scalar_one_or_none()
        
        if not work:
            return False, "Lavoro non trovato."
        
        if work.status != WorkStatus.ASSIGNED:
            return False, f"Stato lavoro non valido: {work.status}"
        
        work.status = WorkStatus.ACCEPTED
        await db_session.commit()
        
        logger.info("Job accepted", job_id=job_id, chat_id=chat_id)
        return True, f"✅ Lavoro {work.wr_number} accettato!"
        
    except Exception as e:
        logger.error("Error accepting job", error=str(e), job_id=job_id)
        return False, "Errore durante l'accettazione del lavoro."


async def handle_refuse_job(
    job_id: int,
    chat_id: str,
    db_session: Any,
    reason: str = "",
) -> tuple[bool, str]:
    """
    Handle job refusal callback.
    
    Updates the work order status to REFUSED.
    
    Args:
        job_id: Work order ID
        chat_id: Telegram chat ID
        db_session: Database session
        reason: Reason for refusal
        
    Returns:
        tuple[bool, str]: Success status and message
    """
    from sqlalchemy import select
    from app.models.work import Work, WorkStatus
    
    try:
        result = await db_session.execute(
            select(Work).where(Work.id == job_id)
        )
        work = result.scalar_one_or_none()
        
        if not work:
            return False, "Lavoro non trovato."
        
        work.status = WorkStatus.REFUSED
        if reason:
            work.notes = f"{work.notes or ''}\nMotivo rifiuto: {reason}"
        
        await db_session.commit()
        
        logger.info("Job refused", job_id=job_id, chat_id=chat_id)
        return True, f"❌ Lavoro {work.wr_number} rifiutato."
        
    except Exception as e:
        logger.error("Error refusing job", error=str(e), job_id=job_id)
        return False, "Errore durante il rifiuto del lavoro."


async def handle_close_job(
    job_id: int,
    chat_id: str,
    db_session: Any,
    notes: str = "",
) -> tuple[bool, str]:
    """
    Handle job completion callback.
    
    Updates the work order status to COMPLETED.
    
    Args:
        job_id: Work order ID
        chat_id: Telegram chat ID
        db_session: Database session
        notes: Completion notes
        
    Returns:
        tuple[bool, str]: Success status and message
    """
    from datetime import datetime
    from sqlalchemy import select
    from app.models.work import Work, WorkStatus
    
    try:
        result = await db_session.execute(
            select(Work).where(Work.id == job_id)
        )
        work = result.scalar_one_or_none()
        
        if not work:
            return False, "Lavoro non trovato."
        
        if work.status not in [WorkStatus.ACCEPTED, WorkStatus.IN_PROGRESS]:
            return False, f"Stato lavoro non valido: {work.status}"
        
        work.status = WorkStatus.COMPLETED
        work.completion_date = datetime.utcnow()
        if notes:
            work.notes = f"{work.notes or ''}\nNote chiusura: {notes}"
        
        await db_session.commit()
        
        logger.info("Job closed", job_id=job_id, chat_id=chat_id)
        return True, f"✅ Lavoro {work.wr_number} completato!"
        
    except Exception as e:
        logger.error("Error closing job", error=str(e), job_id=job_id)
        return False, "Errore durante la chiusura del lavoro."


async def handle_photo(
    job_id: int,
    chat_id: str,
    photo_file_id: str,
    db_session: Any,
) -> tuple[bool, str]:
    """
    Handle photo upload for a job.
    
    Stores the photo reference in the work order.
    
    Args:
        job_id: Work order ID
        chat_id: Telegram chat ID
        photo_file_id: Telegram file ID of the photo
        db_session: Database session
        
    Returns:
        tuple[bool, str]: Success status and message
    """
    from sqlalchemy import select
    from app.models.work import Work
    
    try:
        result = await db_session.execute(
            select(Work).where(Work.id == job_id)
        )
        work = result.scalar_one_or_none()
        
        if not work:
            return False, "Lavoro non trovato."
        
        # Add photo to the list
        photos = work.photos or []
        photos.append(photo_file_id)
        work.photos = photos
        
        await db_session.commit()
        
        logger.info(
            "Photo added to job",
            job_id=job_id,
            chat_id=chat_id,
            photo_count=len(photos),
        )
        return True, f"📸 Foto aggiunta al lavoro ({len(photos)} totali)."
        
    except Exception as e:
        logger.error("Error adding photo", error=str(e), job_id=job_id)
        return False, "Errore durante il caricamento della foto."
