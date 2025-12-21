from fastapi import APIRouter, HTTPException, Depends
from app.utils.auth import auth_required
import os
import json
try:
    import httpx
except Exception:
    httpx = None

router = APIRouter()

@router.get("/telegram/status")
async def telegram_status():
    """Check Telegram bot status and configuration"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"token_set": False, "error": "TELEGRAM_BOT_TOKEN not configured"}

    result = {
        "token_set": True,
        "polling_enabled": False,
        "httpx_available": httpx is not None
    }

    # Test bot connection
    if httpx:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                result["getMe"] = response.json()
        except Exception as e:
            result["getMe"] = {"error": str(e)}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
                result["webhookInfo"] = response.json()
        except Exception as e:
            result["webhookInfo"] = {"error": str(e)}

    return result

@router.post("/telegram/send")
async def send_telegram_message(chat_id: str, text: str, _=Depends(auth_required)):
    """Send a message via Telegram bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")

    if not httpx:
        raise HTTPException(status_code=500, detail="httpx not available")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/telegram/updates")
async def get_telegram_updates(offset: int = None, limit: int = 100, _=Depends(auth_required)):
    """Get recent Telegram updates"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")

    if not httpx:
        raise HTTPException(status_code=500, detail="httpx not available")

    try:
        params = {"limit": limit}
        if offset:
            params["offset"] = offset

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params=params
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get updates: {str(e)}")

@router.post("/telegram/set_webhook")
async def set_telegram_webhook(url: str, _=Depends(auth_required)):
    """Set Telegram webhook URL"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")

    if not httpx:
        raise HTTPException(status_code=500, detail="httpx not available")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={"url": url}
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {str(e)}")

@router.post("/telegram/delete_webhook")
async def delete_telegram_webhook(_=Depends(auth_required)):
    """Delete Telegram webhook"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")

    if not httpx:
        raise HTTPException(status_code=500, detail="httpx not available")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/deleteWebhook"
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")

@router.post("/telegram/webhook/{bot_token}")
async def telegram_webhook(bot_token: str, update: dict):
    """Handle incoming Telegram webhook updates"""
    # Verify the bot token matches
    expected_token = os.getenv("TELEGRAM_BOT_TOKEN", "").split(":")[0]
    if bot_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid bot token")

    try:
        # Process the update
        if "message" in update:
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")

            if text and chat_id:
                # Handle bot commands
                await handle_telegram_command(chat_id, text, user_id)

        return {"ok": True}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"ok": False, "error": str(e)}

async def handle_telegram_command(chat_id: int, text: str, user_id: int):
    """Handle incoming Telegram commands from technicians"""
    try:
        import httpx
        from app.database import SessionLocal
        from app.models.models import Technician, Work

        # Commands handling
        if text.startswith("/start"):
            welcome_msg = "🤖 Benvenuto nel bot FTTH!\n\nComandi disponibili:\n/miei_lavori - I tuoi lavori assegnati\n/help - Mostra tutti i comandi"
            await send_telegram_message_to_chat(chat_id, welcome_msg)

        elif text.startswith("/miei_lavori"):
            # Get technician by telegram_id
            db = SessionLocal()
            try:
                technician = db.query(Technician).filter(Technician.telegram_id == str(user_id)).first()
                if technician:
                    works = db.query(Work).filter(Work.tecnico_assegnato_id == technician.id, Work.stato != "chiuso").all()
                    if works:
                        msg = f"📋 I tuoi lavori ({len(works)}):\n\n"
                        for work in works:
                            msg += f"🔧 WR {work.numero_wr}\n📍 {work.indirizzo or 'N/D'}\n📞 {work.nome_cliente or 'N/D'}\n📅 Stato: {work.stato}\n\n"
                    else:
                        msg = "✅ Non hai lavori assegnati al momento."
                else:
                    msg = "❌ Non sei registrato come tecnico. Contatta l'amministratore."
                await send_telegram_message_to_chat(chat_id, msg)
            finally:
                db.close()

        elif text.startswith("/accetta"):
            # Accept work - extract work number from message
            parts = text.split()
            if len(parts) > 1:
                work_number = parts[1]
                await update_work_status(chat_id, work_number, "in_corso", user_id)
            else:
                await send_telegram_message_to_chat(chat_id, "Uso: /accetta <numero_WR>")

        elif text.startswith("/rifiuta"):
            parts = text.split()
            if len(parts) > 1:
                work_number = parts[1]
                await update_work_status(chat_id, work_number, "sospeso", user_id)
            else:
                await send_telegram_message_to_chat(chat_id, "Uso: /rifiuta <numero_WR>")

        elif text.startswith("/chiudi"):
            parts = text.split()
            if len(parts) > 1:
                work_number = parts[1]
                await update_work_status(chat_id, work_number, "chiuso", user_id)
            else:
                await send_telegram_message_to_chat(chat_id, "Uso: /chiudi <numero_WR>")

        elif text.startswith("/help"):
            help_msg = """🤖 Comandi disponibili:

/miei_lavori - Mostra i tuoi lavori assegnati
/accetta <numero_WR> - Accetta un lavoro
/rifiuta <numero_WR> - Rifiuta un lavoro
/chiudi <numero_WR> - Chiudi un lavoro
/help - Mostra questo messaggio

Esempi:
/accetta 15699897
/chiudi 15699897"""
            await send_telegram_message_to_chat(chat_id, help_msg)

    except Exception as e:
        print(f"Error handling command: {e}")
        await send_telegram_message_to_chat(chat_id, "❌ Errore nell'elaborazione del comando")

async def send_telegram_message_to_chat(chat_id: int, text: str):
    """Send message to Telegram chat (internal function)"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not httpx:
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            )
    except Exception as e:
        print(f"Error sending message: {e}")

async def update_work_status(chat_id: int, work_number: str, new_status: str, user_id: int):
    """Update work status via Telegram command"""
    try:
        from app.database import SessionLocal
        from app.models.models import Technician, Work, WorkEvent
        from datetime import datetime

        db = SessionLocal()
        try:
            # Find technician
            technician = db.query(Technician).filter(Technician.telegram_id == str(user_id)).first()
            if not technician:
                await send_telegram_message_to_chat(chat_id, "❌ Non sei registrato come tecnico")
                return

            # Find work
            work = db.query(Work).filter(Work.numero_wr == work_number, Work.tecnico_assegnato_id == technician.id).first()
            if not work:
                await send_telegram_message_to_chat(chat_id, f"❌ Lavoro {work_number} non trovato o non assegnato a te")
                return

            # Update work status
            old_status = work.stato
            work.stato = new_status
            work.data_aggiornamento = datetime.utcnow()

            # Create work event
            event = WorkEvent(
                work_id=work.id,
                technician_id=technician.id,
                event_type="status_change",
                old_value=old_status,
                new_value=new_status,
                notes=f"Aggiornato via Telegram da {technician.nome} {technician.cognome}"
            )
            db.add(event)
            db.commit()

            status_emoji = {"in_corso": "▶️", "sospeso": "⏸️", "chiuso": "✅"}
            emoji = status_emoji.get(new_status, "🔄")

            await send_telegram_message_to_chat(
                chat_id,
                f"{emoji} Lavoro {work_number} aggiornato a: {new_status.replace('_', ' ').title()}"
            )

        finally:
            db.close()

    except Exception as e:
        print(f"Error updating work status: {e}")
        await send_telegram_message_to_chat(chat_id, "❌ Errore nell'aggiornamento del lavoro")