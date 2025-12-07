from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent
from app.utils.auth import auth_required
from datetime import datetime
import logging
import re
import app.utils.telegram as telegram_utils
import os
try:
    import httpx
except Exception:
    httpx = None
import json
from app.utils.help_text import HELP_TEXT

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger("app.routes.telegram")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe_send(chat_id, text, reply_markup=None):
    """Send a message and log if it failed, returning boolean success."""
    try:
        if reply_markup is not None:
            try:
                ok = telegram_utils.send_message_to_telegram(chat_id, text, reply_markup=reply_markup)
            except TypeError:
                # Some tests monkeypatch send_message_to_telegram as a simple two-arg function
                ok = telegram_utils.send_message_to_telegram(chat_id, text)
        else:
            ok = telegram_utils.send_message_to_telegram(chat_id, text)
        if not ok:
            logger.warning("Failed to send telegram message to %s", chat_id)
        return ok
    except Exception as e:
        logger.exception("Error while sending telegram message: %s", e)
        return False


@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    # Support message updates only for now
    message = body.get("message") or body.get("edited_message")
    if not message:
        return {"ok": True}
    text = message.get("text") or ""
    chat = message.get("chat", {})
    from_user = message.get("from", {})
    telegram_id = str(from_user.get("id"))
    # Find technician by telegram_id
    tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
    # Parse command and args (handle /cmd and /cmd@bot and optional args)
    cmd = None
    args = ""
    if text:
        text_stripped = text.strip()
        # regex: /command[@botname] [args...]
        m = re.match(r'^\/([^\s@\/]+)(?:@[\w_]+)?(?:\s+(.+))?', text_stripped)
        if m:
            cmd = m.group(1).lower()
            args = m.group(2) or ""

    # Process commands
    # Provide a help menu via webhook
    logger.info("Telegram webhook: cmd=%s args=%s from_user_id=%s chat_id=%s", cmd, args, telegram_id, chat.get('id'))
    if cmd in ("help", "start"):
        help_text = HELP_TEXT
        # Use chat id to reply
        chat_id = chat.get("id") or from_user.get("id")
        try:
            reply_markup = {
                "keyboard": [["/miei_lavori", "/accetta", "/rifiuta"], ["/chiudi", "/help"]],
                "one_time_keyboard": False,
                "resize_keyboard": True,
            }
            # Use wrapper to log failure
            try:
                _safe_send(chat_id, help_text, reply_markup=reply_markup)
            except TypeError:
                # Tests may monkeypatch send_message_to_telegram with a fake signature that doesn't accept kwargs
                _safe_send(chat_id, help_text)
        except Exception:
            pass
        return {"ok": True, "message": "help sent"}

    # Show the list of works assigned to the technician
    if cmd == "miei_lavori":
        telegram_id = str(from_user.get("id"))
        tech = db.query(Technician).filter(Technician.telegram_id == telegram_id).first()
        if not tech:
            _safe_send(chat.get("id") or from_user.get("id"), "Tecnico non trovato. Contatta l'admin.")
            return {"ok": True}
        works = db.query(Work).filter(Work.tecnico_assegnato_id == tech.id).all()
        if not works:
            _safe_send(chat.get("id") or from_user.get("id"), "Nessun lavoro assegnato")
            return {"ok": True}
        lines = [f"WR {w.numero_wr} - {w.stato} - {w.indirizzo}" for w in works]
        _safe_send(chat.get("id") or from_user.get("id"), "\n".join(lines))
        return {"ok": True}

    if cmd == "accetta":
        parts = args.split() if args else []
        if len(parts) >= 1:
            wr = parts[0]
            work = db.query(Work).filter(Work.numero_wr == wr).first()
            if not work:
                return {"ok": False, "message": "Work not found"}
            if not tech:
                return {"ok": False, "message": "Technician not linked"}
            work.tecnico_assegnato_id = tech.id
            work.stato = "in_corso"
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="accepted", description="Accepted by tech via webhook", user_id=tech.id)
            db.add(event)
            db.commit()
            return {"ok": True, "message": "Accepted"}
    if cmd == "rifiuta":
        parts = args.split() if args else []
        if len(parts) >= 1:
            wr = parts[0]
            work = db.query(Work).filter(Work.numero_wr == wr).first()
            if not work:
                return {"ok": False, "message": "Work not found"}
            if not tech:
                return {"ok": False, "message": "Technician not linked"}
            if work.tecnico_assegnato_id != tech.id:
                return {"ok": False, "message": "Work not assigned to you"}
            work.stato = "aperto"
            work.tecnico_assegnato_id = None
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="rejected", description="Rejected by tech via webhook", user_id=tech.id)
            db.add(event)
            db.commit()
            return {"ok": True, "message": "Rejected"}
    if cmd == "chiudi":
        parts = args.split() if args else []
        if len(parts) >= 1:
            wr = parts[0]
            work = db.query(Work).filter(Work.numero_wr == wr).first()
            if not work:
                return {"ok": False, "message": "Work not found"}
            if not tech:
                return {"ok": False, "message": "Technician not linked"}
            if work.tecnico_assegnato_id != tech.id:
                return {"ok": False, "message": "Work not assigned to you"}
            work.stato = "chiuso"
            work.data_chiusura = datetime.now()
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="closed", description="Closed by tech via webhook", user_id=tech.id)
            db.add(event)
            db.commit()
            return {"ok": True, "message": "Closed"}
    # Default response
    return {"ok": True}


@router.get('/commands')
def get_bot_commands_db():
    """Debug: fetch current commands from Telegram Bot API for the configured token"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise HTTPException(status_code=400, detail='TELEGRAM_BOT_TOKEN not set')
    if not httpx:
        raise HTTPException(status_code=500, detail='httpx not available')
    try:
        resp = httpx.get(f'https://api.telegram.org/bot{token}/getMyCommands', timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/commands/set')
def set_bot_commands_db(payload: dict | None = Body(None)):
    """Debug: set commands via Bot API. Accepts JSON payload with 'commands' list per Bot API format.
    If payload is None, will set the default commands list from the app.
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise HTTPException(status_code=400, detail='TELEGRAM_BOT_TOKEN not set')
    if not httpx:
        raise HTTPException(status_code=500, detail='httpx not available')
    commands = payload.get('commands') if payload else None
    if commands is None:
        commands = [
            {"command": "start", "description": "Benvenuto"},
            {"command": "help", "description": "Mostra comandi"},
            {"command": "miei_lavori", "description": "I tuoi lavori"},
            {"command": "accetta", "description": "Accetta un lavoro"},
            {"command": "rifiuta", "description": "Rifiuta un lavoro"},
            {"command": "chiudi", "description": "Chiudi un lavoro"},
        ]
    try:
        resp = httpx.post(f'https://api.telegram.org/bot{token}/setMyCommands', json={'commands': commands}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/me')
def get_bot_me():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise HTTPException(status_code=400, detail='TELEGRAM_BOT_TOKEN not set')
    if not httpx:
        raise HTTPException(status_code=500, detail='httpx not available')
    try:
        resp = httpx.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/webhook_info')
def get_webhook_info():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise HTTPException(status_code=400, detail='TELEGRAM_BOT_TOKEN not set')
    if not httpx:
        raise HTTPException(status_code=500, detail='httpx not available')
    try:
        resp = httpx.get(f'https://api.telegram.org/bot{token}/getWebhookInfo', timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/set_webhook')
def set_webhook(payload: dict = Body(...)):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise HTTPException(status_code=400, detail='TELEGRAM_BOT_TOKEN not set')
    if not httpx:
        raise HTTPException(status_code=500, detail='httpx not available')
    url = payload.get('url')
    if not url:
        raise HTTPException(status_code=400, detail='url required')
    try:
        resp = httpx.post(f'https://api.telegram.org/bot{token}/setWebhook', json={'url': url}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link/{tech_id}")
def link_telegram(tech_id: int, payload: dict, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin','backoffice']))):
    telegram_id = str(payload.get("telegram_id")) if payload else None
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id required")
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    tech.telegram_id = telegram_id
    db.commit()
    return {"ok": True}


@router.get('/status')
def telegram_status():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    polling_env = os.getenv('TELEGRAM_POLLING', 'true').lower()
    polling_enabled = polling_env in ('1', 'true', 'yes')
    status = {
        'token_set': bool(token),
        'polling_enabled': polling_enabled,
        'httpx_available': bool(httpx),
        'getMe': None,
        'webhookInfo': None,
    }
    if not token:
        return status
    if not httpx:
        return status
    try:
        resp = httpx.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5.0)
        status['getMe'] = resp.json()
    except Exception as e:
        status['getMe'] = {'error': str(e)}
    try:
        resp2 = httpx.get(f'https://api.telegram.org/bot{token}/getWebhookInfo', timeout=5.0)
        status['webhookInfo'] = resp2.json()
    except Exception as e:
        status['webhookInfo'] = {'error': str(e)}
    return status
