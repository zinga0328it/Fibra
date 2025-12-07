from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent
from app.utils.auth import auth_required
from datetime import datetime
import logging
from typing import Optional

router = APIRouter(prefix="/manual", tags=["manual"])
logger = logging.getLogger('app.routes.manual')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_datetime(value: Optional[str]):
    if not value:
        return None
    try:
        # Try ISO first
        return datetime.fromisoformat(value)
    except Exception:
        pass
    # Try common format: dd/mm/YYYY HH:MM[:SS]
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    # fallback
    try:
        return datetime.fromtimestamp(float(value))
    except Exception:
        return None


@router.post('/works')
def manual_create_work(payload: dict = Body(...), db: Session = Depends(get_db), user = Depends(auth_required(['admin','backoffice']))):
    """Create a Work record manually into the DB. The payload is flexible; known fields are used and the rest kept in `extra_fields`.
    Requires admin/backoffice role or correct X-API-Key.
    """
    numero_wr = payload.get('numero_wr') or payload.get('WR')
    if not numero_wr:
        raise HTTPException(status_code=400, detail='numero_wr is required')

    existing = db.query(Work).filter(Work.numero_wr == numero_wr).first()
    if existing:
        raise HTTPException(status_code=409, detail='Work with numero_wr already exists')

    work = Work()
    work.numero_wr = numero_wr
    work.operatore = payload.get('operatore') or payload.get('impresa') or payload.get('IMPRESA')
    work.indirizzo = payload.get('indirizzo') or payload.get('INDIRIZZO')
    work.nome_cliente = payload.get('cliente') or payload.get('NOME_CLIENTE') or payload.get('COGNOME_CLIENTE')
    work.tipo_lavoro = payload.get('tipo_lavoro') or payload.get('tipo') or payload.get('TIPOLOGIA_SERVIZIO')
    work.stato = payload.get('stato') or payload.get('STATO_WR') or 'aperto'
    # appointment start and end mapping
    data_inizio = payload.get('data_inizio') or payload.get('appuntamento') or payload.get('INIZIO_APPUNTAMENTO') or payload.get('Appuntamento')
    if data_inizio:
        parsed = parse_datetime(data_inizio)
        if parsed:
            work.data_apertura = parsed
    data_fine = payload.get('data_fine') or payload.get('FINE_APPUNTAMENTO')
    if data_fine:
        parsed = parse_datetime(data_fine)
        if parsed:
            work.data_chiusura = parsed

    # link technician if provided by name or ID
    tecnico = payload.get('tecnico') or payload.get('Tecnico')
    if tecnico:
        # If numeric id
        try:
            tid = int(tecnico)
            tech = db.query(Technician).filter(Technician.id == tid).first()
        except Exception:
            # Try find by name
            parts = tecnico.split() if isinstance(tecnico, str) else []
            if len(parts) >= 2:
                nome = parts[0]
                cognome = ' '.join(parts[1:])
                tech = db.query(Technician).filter(Technician.nome == nome, Technician.cognome == cognome).first()
            else:
                tech = db.query(Technician).filter(Technician.nome == tecnico).first()
        if tech:
            work.tecnico_assegnato_id = tech.id

    # Keep any extra fields in JSON
    known = {'numero_wr', 'operatore', 'indirizzo', 'nome_cliente', 'tipo_lavoro', 'stato', 'data_inizio', 'data_fine', 'tecnico', 'cliente', 'indirizzo', 'impresa', 'tipo', 'WR', 'Appuntamento', 'INIZIO_APPUNTAMENTO', 'FINE_APPUNTAMENTO'}
    extra = {k: v for k, v in payload.items() if k not in known}
    if extra:
        work.extra_fields = extra

    try:
        db.add(work)
        db.commit()
        db.refresh(work)
        # Add event to track manual creation
        ev = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type='created_manual', description='Created via manual entry', user_id=None)
        db.add(ev)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception('Failed to insert manual work: %s', e)
        raise HTTPException(status_code=500, detail='DB error')
    return { 'ok': True, 'id': work.id, 'numero_wr': work.numero_wr }
