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
from app.utils.rate_limiter import check_telegram_flood, webhook_global_limiter

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

    # ---- ANTI-FLOOD ----
    # Rate limit globale webhook
    if not webhook_global_limiter.is_allowed("webhook_global"):
        logger.warning("Webhook global rate limit hit")
        return {"ok": True}

    # Rate limit per utente + anti doppio-click
    if cmd:
        flood_msg = check_telegram_flood(telegram_id, cmd)
        if flood_msg:
            chat_id = chat.get("id") or from_user.get("id")
            _safe_send(chat_id, flood_msg)
            return {"ok": True}

    # Process commands
    # Provide a help menu via webhook
    logger.info("Telegram webhook: cmd=%s args=%s from_user_id=%s chat_id=%s", cmd, args, telegram_id, chat.get('id'))
    if cmd in ("help", "start"):
        help_text = HELP_TEXT
        # Use chat id to reply
        chat_id = chat.get("id") or from_user.get("id")
        try:
            reply_markup = {
                "keyboard": [["/miei_lavori", "/accetta"], ["/modem", "/chiudi"], ["/sospendi", "/rifiuta"], ["/posizione", "/sos", "/help"]],
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
        # Tutti i lavori ATTIVI (assegnato, in_corso, sospeso) e NON archiviati
        works = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato.in_(["assegnato", "in_corso", "sospeso"]),
            Work.archived == False,
        ).order_by(Work.data_appuntamento.asc().nullslast()).all()
        if not works:
            _safe_send(chat.get("id") or from_user.get("id"), "✅ Non hai lavori attivi al momento.")
            return {"ok": True}
        STATO_EMOJI = {"assegnato": "🆕", "in_corso": "🔧", "sospeso": "⏸️"}
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
                    line += f"\n📅 {w.data_appuntamento.strftime('%d/%m/%Y %H:%M')}"
                lines.append(line)
            parts.append(header + "\n\n" + "\n\n".join(lines))
        msg = f"📊 I tuoi lavori attivi: {len(works)}\n\n" + "\n\n---\n\n".join(parts)
        _safe_send(chat.get("id") or from_user.get("id"), msg.strip())
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
        if len(parts) < 2:
            chat_id = chat.get("id") or from_user.get("id")
            _safe_send(chat_id, "📝 Uso: /chiudi <WR> <note tecniche>\n\nEsempio:\n/chiudi 95005055 Installato ONT e modem, tutto ok\n\n⚠️ Le note sono obbligatorie!")
            return {"ok": True, "message": "usage sent"}
        if len(parts) >= 2:
            wr = parts[0]
            note_chiusura = " ".join(parts[1:])
            work = db.query(Work).filter(Work.numero_wr == wr).first()
            if not work:
                _safe_send(chat.get("id") or from_user.get("id"), f"❌ Lavoro {wr} non trovato.")
                return {"ok": True, "message": "Work not found"}
            if not tech:
                return {"ok": False, "message": "Technician not linked"}
            if work.tecnico_assegnato_id != tech.id:
                _safe_send(chat.get("id") or from_user.get("id"), f"❌ Lavoro {wr} non assegnato a te.")
                return {"ok": True, "message": "Work not assigned to you"}
            if work.stato == "chiuso":
                _safe_send(chat.get("id") or from_user.get("id"), "❌ Il lavoro è già chiuso.")
                return {"ok": True, "message": "Already closed"}
            work.stato = "chiuso"
            work.data_chiusura = datetime.now()
            work.tecnico_chiusura_id = tech.id
            work.note_chiusura = note_chiusura
            tech.stato_posizione = "disponibile"
            # Fix: controlla se ha altri lavori in_corso prima di liberare
            db.flush()
            has_in_corso = db.query(Work).filter(
                Work.tecnico_assegnato_id == tech.id,
                Work.stato == "in_corso",
                Work.archived == False,
            ).first()
            tech.stato_posizione = "occupato" if has_in_corso else "disponibile"
            event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="closed", description=f"Chiuso da {tech.nome} {tech.cognome} via webhook | Note: {note_chiusura}", user_id=tech.id)
            db.add(event)
            db.commit()
            modem_info = f"📶 Modem: {work.modem_sn}\n" if work.modem_sn else ""
            _safe_send(chat.get("id") or from_user.get("id"), f"✅ Lavoro {wr} chiuso!\n👷 {tech.nome} {tech.cognome}\n📍 {work.indirizzo or 'N/D'}\n{modem_info}📝 Note: {note_chiusura}")
            return {"ok": True, "message": "Closed"}

    if cmd == "modem":
        parts = args.split() if args else []
        if len(parts) < 2:
            chat_id = chat.get("id") or from_user.get("id")
            _safe_send(chat_id, "📶 Uso: /modem <WR> <seriale modem>\n\nEsempio:\n/modem 95005055 ZTEGC4B1A2C3")
            return {"ok": True, "message": "usage sent"}
        wr = parts[0]
        modem_sn = " ".join(parts[1:])
        if not tech:
            return {"ok": False, "message": "Technician not linked"}
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if not work:
            _safe_send(chat.get("id") or from_user.get("id"), f"❌ Lavoro {wr} non trovato o non assegnato a te.")
            return {"ok": True, "message": "Work not found"}
        if work.stato == "chiuso":
            _safe_send(chat.get("id") or from_user.get("id"), "❌ Il lavoro è già chiuso.")
            return {"ok": True, "message": "Already closed"}
        old_sn = work.modem_sn
        work.modem_sn = modem_sn
        event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="modem_registered", description=f"Modem SN: {modem_sn} registrato da {tech.nome} {tech.cognome}", user_id=tech.id)
        db.add(event)
        db.commit()
        if old_sn:
            _safe_send(chat.get("id") or from_user.get("id"), f"✅ Modem aggiornato per WR {wr}\n📶 Vecchio: {old_sn}\n📶 Nuovo: {modem_sn}")
        else:
            _safe_send(chat.get("id") or from_user.get("id"), f"✅ Modem registrato per WR {wr}\n📶 Seriale: {modem_sn}")
        return {"ok": True, "message": "Modem saved"}

    if cmd == "sospendi":
        MOTIVI_VALIDI = ["pioggia", "cavo_finito", "scala_insufficiente", "cliente_assente", "problema_logistico", "altro"]
        parts = args.split() if args else []
        if len(parts) < 2:
            motivi_str = ", ".join(MOTIVI_VALIDI)
            chat_id = chat.get("id") or from_user.get("id")
            _safe_send(chat_id, f"Uso: /sospendi <WR> <motivo> [data GG/MM/AAAA HH:MM]\n\nMotivi: {motivi_str}\n\nEsempio:\n/sospendi 95005055 pioggia\n/sospendi 95005055 cliente_assente 15/03/2026 10:00")
            return {"ok": True, "message": "usage sent"}
        wr = parts[0]
        motivo = parts[1].lower()
        if motivo not in MOTIVI_VALIDI:
            _safe_send(chat.get("id") or from_user.get("id"), f"❌ Motivo '{motivo}' non valido.\nValidi: {', '.join(MOTIVI_VALIDI)}")
            return {"ok": True, "message": "Invalid reason"}
        nuova_data = None
        if len(parts) >= 4:
            data_str = f"{parts[2]} {parts[3]}"
            try:
                nuova_data = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
            except ValueError:
                _safe_send(chat.get("id") or from_user.get("id"), "❌ Formato data non valido. Usa: GG/MM/AAAA HH:MM")
                return {"ok": True, "message": "Invalid date"}
        elif len(parts) == 3:
            try:
                nuova_data = datetime.strptime(parts[2], "%d/%m/%Y")
                nuova_data = nuova_data.replace(hour=9, minute=0)
            except ValueError:
                _safe_send(chat.get("id") or from_user.get("id"), "❌ Formato data non valido. Usa: GG/MM/AAAA [HH:MM]")
                return {"ok": True, "message": "Invalid date"}
        if not tech:
            return {"ok": False, "message": "Technician not linked"}
        work = db.query(Work).filter(Work.numero_wr == wr, Work.tecnico_assegnato_id == tech.id).first()
        if not work:
            _safe_send(chat.get("id") or from_user.get("id"), f"❌ Lavoro {wr} non trovato o non assegnato a te.")
            return {"ok": True, "message": "Work not found"}
        if work.stato == "chiuso":
            _safe_send(chat.get("id") or from_user.get("id"), "❌ Il lavoro è già chiuso.")
            return {"ok": True, "message": "Already closed"}
        work.stato = "sospeso"
        work.motivo_rinvio = motivo
        if nuova_data:
            work.data_appuntamento = nuova_data
        db.flush()
        has_in_corso = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).first()
        tech.stato_posizione = "occupato" if has_in_corso else "disponibile"
        desc = f"Sospeso da {tech.nome} {tech.cognome} | Motivo: {motivo}"
        if nuova_data:
            desc += f" | Nuovo appuntamento: {nuova_data.strftime('%d/%m/%Y %H:%M')}"
        event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="suspended", description=desc, user_id=tech.id)
        db.add(event)
        db.commit()
        msg = f"⏸️ Lavoro {wr} sospeso\n⚠️ Motivo: {motivo}"
        if nuova_data:
            msg += f"\n📅 Nuovo appuntamento: {nuova_data.strftime('%d/%m/%Y %H:%M')}"
        _safe_send(chat.get("id") or from_user.get("id"), msg)
        return {"ok": True, "message": "Suspended"}

    if cmd == "posizione":
        chat_id = chat.get("id") or from_user.get("id")
        if not tech:
            _safe_send(chat_id, "❌ Tecnico non trovato.")
            return {"ok": True}
        if tech.lat and tech.lng:
            _safe_send(chat_id, f"📍 Ultima posizione:\nLat: {tech.lat}\nLng: {tech.lng}\n🕐 {tech.last_position_update or 'N/D'}")
        else:
            _safe_send(chat_id, "📍 Nessuna posizione registrata.\nInvia la tua posizione per aggiornarla.")
        return {"ok": True}

    if cmd == "sos":
        chat_id = chat.get("id") or from_user.get("id")
        if not tech:
            _safe_send(chat_id, "❌ Tecnico non trovato.")
            return {"ok": True}
        tech.stato_posizione = "sos"
        db.commit()
        _safe_send(chat_id, "🆘 SOS attivato! Il tuo stato è stato impostato su SOS.\nContatta il coordinatore per assistenza.")
        return {"ok": True}
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


# ============ GPT Integration Endpoints ============

@router.post('/gpt/status')
def enable_gpt_telegram(enabled: bool = Body(..., embed=True), current_user = Depends(auth_required(['admin','backoffice']))):
    """Abilita/disabilita l'invio di messaggi Telegram da parte di GPT"""
    # Salva lo stato in un file o database per persistenza
    status_file = os.path.join(os.path.dirname(__file__), '..', 'gpt_telegram_enabled.json')
    try:
        with open(status_file, 'w') as f:
            json.dump({'enabled': enabled, 'updated_at': datetime.now().isoformat()}, f)
        return {"ok": True, "message": f"GPT Telegram {'abilitato' if enabled else 'disabilitato'}", "enabled": enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel salvare lo stato: {str(e)}")


@router.post('/gpt/send')
def send_gpt_message(payload: dict = Body(...), db: Session = Depends(get_db), current_user = Depends(auth_required(['admin','backoffice']))):
    """Riceve comandi da GPT e invia messaggi Telegram ai tecnici o squadre"""

    # Verifica se GPT è abilitato
    status_file = os.path.join(os.path.dirname(__file__), '..', 'gpt_telegram_enabled.json')
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
                if not status_data.get('enabled', False):
                    raise HTTPException(status_code=403, detail="Invio messaggi GPT disabilitato")
    except Exception:
        pass  # Se non riesce a leggere, permette l'invio

    # Estrai parametri dal payload GPT
    action = payload.get('action', '').lower()
    target_type = payload.get('target_type', 'technician')  # 'technician' o 'team'
    target_id = payload.get('target_id')  # ID del tecnico o squadra
    message = payload.get('message', '')
    work_id = payload.get('work_id')  # Opzionale, per messaggi relativi a lavori

    if not message:
        raise HTTPException(status_code=400, detail="Messaggio obbligatorio")

    # Trova i destinatari
    recipients = []

    if target_type == 'technician':
        if not target_id:
            raise HTTPException(status_code=400, detail="target_id obbligatorio per technician")
        tech = db.query(Technician).filter(Technician.id == target_id).first()
        if not tech:
            raise HTTPException(status_code=404, detail="Tecnico non trovato")
        if tech.telegram_id:
            recipients.append({'id': tech.telegram_id, 'name': f"{tech.nome} {tech.cognome}"})

    elif target_type == 'team':
        if not target_id:
            raise HTTPException(status_code=400, detail="target_id obbligatorio per team")
        team_techs = db.query(Technician).filter(Technician.squadra_id == target_id).all()
        for tech in team_techs:
            if tech.telegram_id:
                recipients.append({'id': tech.telegram_id, 'name': f"{tech.nome} {tech.cognome}"})

    else:
        raise HTTPException(status_code=400, detail="target_type deve essere 'technician' o 'team'")

    if not recipients:
        raise HTTPException(status_code=404, detail="Nessun destinatario trovato con Telegram collegato")

    # Invia messaggi
    sent_count = 0
    failed_count = 0
    results = []

    for recipient in recipients:
        try:
            # Aggiungi contesto se è relativo a un lavoro
            full_message = message
            if work_id:
                work = db.query(Work).filter(Work.id == work_id).first()
                if work:
                    full_message = f"📋 LAVORO: {work.numero_wr}\n\n{message}"

            success = _safe_send(recipient['id'], full_message)
            if success:
                sent_count += 1
                results.append({'recipient': recipient['name'], 'status': 'sent'})
            else:
                failed_count += 1
                results.append({'recipient': recipient['name'], 'status': 'failed'})

        except Exception as e:
            failed_count += 1
            results.append({'recipient': recipient['name'], 'status': 'error', 'error': str(e)})
            logger.error(f"Errore invio messaggio a {recipient['name']}: {str(e)}")

    # Log dell'evento
    if work_id:
        work = db.query(Work).filter(Work.id == work_id).first()
        if work:
            event = WorkEvent(
                work_id=work.id,
                timestamp=datetime.now(),
                event_type="gpt_message",
                description=f"GPT sent message to {len(recipients)} recipients",
                user_id=current_user.get('id') if current_user else None
            )
            db.add(event)
            db.commit()

    return {
        "ok": True,
        "message": f"Messaggio inviato a {sent_count} destinatari",
        "sent": sent_count,
        "failed": failed_count,
        "total_recipients": len(recipients),
        "results": results
    }
