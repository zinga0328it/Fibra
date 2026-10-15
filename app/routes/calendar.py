"""
Calendar Router - Gestione appuntamenti e calendario lavori FTTH
File modulare: app/routes/calendar.py

Rotte:
  GET /calendar/              → calendario appuntamenti (filtro per range date)
  PUT /calendar/{work_id}     → sposta/modifica appuntamento
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from typing import Optional
import logging

from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent
router = APIRouter(prefix="/calendar", tags=["calendar"])
logger = logging.getLogger('app.routes.calendar')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET /calendar/ — Calendario appuntamenti
# ============================================================
@router.get("/")
def get_calendar(
    date_from: str = Query(..., description="Data inizio range (YYYY-MM-DD)", alias="from"),
    date_to: str = Query(..., description="Data fine range (YYYY-MM-DD)", alias="to"),
    stato: Optional[str] = Query(None, description="Filtra per stato lavoro"),
    tecnico_id: Optional[int] = Query(None, description="Filtra per tecnico assegnato"),
    db: Session = Depends(get_db),
):
    """
    Restituisce i lavori con appuntamento programmato nel range di date.
    Utile per il calendario settimanale/mensile sul sito web.

    Esempio: GET /calendar/?from=2026-02-15&to=2026-02-22
    """
    try:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD")

    filters = [
        Work.data_appuntamento != None,
        Work.data_appuntamento >= dt_from,
        Work.data_appuntamento <= dt_to,
    ]

    if stato:
        filters.append(Work.stato == stato)
    if tecnico_id:
        filters.append(Work.tecnico_assegnato_id == tecnico_id)

    works = db.query(Work).filter(and_(*filters)).order_by(Work.data_appuntamento).all()

    result = []
    for w in works:
        tecnico_nome = None
        if w.tecnico_assegnato:
            tecnico_nome = f"{w.tecnico_assegnato.nome} {w.tecnico_assegnato.cognome}"

        result.append({
            "work_id": w.id,
            "numero_wr": w.numero_wr,
            "nome_cliente": w.nome_cliente,
            "indirizzo": w.indirizzo,
            "tipo_lavoro": w.tipo_lavoro,
            "stato": w.stato,
            "data_appuntamento": w.data_appuntamento.isoformat() if w.data_appuntamento else None,
            "note_appuntamento": w.note_appuntamento,
            "motivo_rinvio": w.motivo_rinvio,
            "tecnico": tecnico_nome,
            "tecnico_id": w.tecnico_assegnato_id,
            "telefono_cliente": (w.extra_fields or {}).get("telefono_cliente") or (w.extra_fields or {}).get("telefono"),
        })

    return {
        "from": date_from,
        "to": date_to,
        "total": len(result),
        "appointments": result,
    }


# ============================================================
# PUT /calendar/{work_id} — Sposta/modifica appuntamento
# ============================================================
@router.put("/{work_id}")
def update_appointment(
    work_id: int,
    data_appuntamento: Optional[str] = Query(None, description="Nuova data appuntamento (ISO 8601)"),
    note_appuntamento: Optional[str] = Query(None, description="Note per il tecnico (scala alta, orario, ecc.)"),
    motivo_rinvio: Optional[str] = Query(None, description="Motivo rinvio: pioggia, cavo_finito, scala_insufficiente, cliente_assente, problema_logistico, altro"),
    db: Session = Depends(get_db),
):
    """
    Modifica l'appuntamento di un lavoro.
    Permette di spostare la data, aggiungere note per il tecnico, specificare motivo rinvio.

    Esempio: PUT /calendar/45?data_appuntamento=2026-02-25T09:00:00&motivo_rinvio=pioggia&note_appuntamento=Portare scala alta
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    old_date = work.data_appuntamento
    changes = []

    if data_appuntamento:
        try:
            new_date = datetime.fromisoformat(data_appuntamento)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato data non valido. Usa ISO 8601 (es. 2026-02-25T09:00:00)")
        work.data_appuntamento = new_date
        changes.append(f"data: {old_date} → {new_date}")

    if note_appuntamento is not None:
        work.note_appuntamento = note_appuntamento
        changes.append(f"note: {note_appuntamento}")

    if motivo_rinvio is not None:
        allowed = {"pioggia", "cavo_finito", "scala_insufficiente", "cliente_assente", "problema_logistico", "altro"}
        if motivo_rinvio not in allowed:
            raise HTTPException(status_code=400, detail=f"Motivo rinvio non valido. Valori: {', '.join(sorted(allowed))}")
        work.motivo_rinvio = motivo_rinvio
        changes.append(f"motivo: {motivo_rinvio}")

    if not changes:
        raise HTTPException(status_code=400, detail="Nessuna modifica specificata")

    # Log evento
    ev = WorkEvent(
        work_id=work.id,
        timestamp=datetime.now(),
        event_type="appointment_changed",
        description=f"Appuntamento modificato: {'; '.join(changes)}",
        user_id=None,
    )
    db.add(ev)
    db.commit()
    db.refresh(work)

    return {
        "ok": True,
        "work_id": work.id,
        "numero_wr": work.numero_wr,
        "data_appuntamento": work.data_appuntamento.isoformat() if work.data_appuntamento else None,
        "note_appuntamento": work.note_appuntamento,
        "motivo_rinvio": work.motivo_rinvio,
        "changes": changes,
    }
