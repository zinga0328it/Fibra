"""
app/routes/geo.py - Endpoint per la Centrale Operativa FTTH.

Endpoint:
- GET  /map-data                      → dati per la mappa (tecnici + lavori)
- PUT  /technicians/{id}/position     → aggiorna posizione tecnico
- PUT  /technicians/{id}/tracking     → attiva/disattiva tracking
- POST /sos/{technician_id}           → SOS: trova tecnici più vicini
- POST /geocode-work/{work_id}        → geocodifica un lavoro esistente
- POST /geocode-all-works             → geocodifica tutti i lavori senza coordinate
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import logging
import os

from app.database import SessionLocal
from app.models.models import Work, Technician
from app.utils.geo import haversine, geocode_address, find_nearest_technicians

logger = logging.getLogger("app.routes.geo")

router = APIRouter(tags=["geo"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic models per request/response ──────────────────────────

class PositionUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitudine (-90 a +90)")
    lng: float = Field(..., ge=-180, le=180, description="Longitudine (-180 a +180)")


class TrackingUpdate(BaseModel):
    tracking_attivo: bool


class TechnicianMapItem(BaseModel):
    id: int
    nome: str
    cognome: str
    telefono: str
    squadra_nome: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    stato_posizione: str = "offline"
    tracking_attivo: bool = False
    last_position_update: Optional[str] = None


class WorkMapItem(BaseModel):
    id: int
    numero_wr: str
    indirizzo: Optional[str] = None
    nome_cliente: Optional[str] = None
    tipo_lavoro: Optional[str] = None
    stato: str = "aperto"
    lat: Optional[float] = None
    lng: Optional[float] = None
    tecnico_assegnato_nome: Optional[str] = None
    data_appuntamento: Optional[str] = None


class MapDataResponse(BaseModel):
    technicians: List[TechnicianMapItem]
    works: List[WorkMapItem]


class SOSResult(BaseModel):
    technician_id: int
    nome: str
    cognome: str
    telefono: str
    lat: float
    lng: float
    distance_km: float


class SOSResponse(BaseModel):
    sos_technician_id: int
    sos_technician_name: str
    nearest: List[SOSResult]
    message: str


# ── GET /map-data ─────────────────────────────────────────────────

@router.get("/map-data", response_model=MapDataResponse)
def get_map_data(db: Session = Depends(get_db)):
    """
    Restituisce tutti i dati per la mappa della centrale operativa.
    - Tecnici con tracking_attivo = True
    - Lavori non archiviati e non chiusi (aperti, sospesi, in_corso)
    """
    # Tecnici visibili sulla mappa
    tecnici = db.query(Technician).filter(
        Technician.tracking_attivo == True
    ).all()

    tech_items = []
    for t in tecnici:
        tech_items.append(TechnicianMapItem(
            id=t.id,
            nome=t.nome,
            cognome=t.cognome,
            telefono=t.telefono,
            squadra_nome=t.squadra.nome if t.squadra else None,
            lat=t.lat,
            lng=t.lng,
            stato_posizione=t.stato_posizione or "offline",
            tracking_attivo=t.tracking_attivo or False,
            last_position_update=t.last_position_update.isoformat() if t.last_position_update else None,
        ))

    # Lavori attivi (non chiusi, non archiviati) con coordinate
    lavori = db.query(Work).filter(
        Work.archived == False,
        Work.stato.in_(["aperto", "sospeso", "in_corso"]),
    ).all()

    work_items = []
    for w in lavori:
        tech_name = None
        if w.tecnico_assegnato:
            tech_name = f"{w.tecnico_assegnato.nome} {w.tecnico_assegnato.cognome}"

        work_items.append(WorkMapItem(
            id=w.id,
            numero_wr=w.numero_wr,
            indirizzo=w.indirizzo,
            nome_cliente=w.nome_cliente,
            tipo_lavoro=w.tipo_lavoro,
            stato=w.stato,
            lat=w.lat,
            lng=w.lng,
            tecnico_assegnato_nome=tech_name,
            data_appuntamento=w.data_appuntamento.isoformat() if w.data_appuntamento else None,
        ))

    return MapDataResponse(technicians=tech_items, works=work_items)


# ── PUT /technicians/{id}/position ────────────────────────────────

@router.put("/technicians/{tech_id}/position")
def update_position(tech_id: int, payload: PositionUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna la posizione GPS di un tecnico.
    Automaticamente attiva il tracking e imposta stato 'disponibile' se era 'offline'.
    """
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Tecnico non trovato")

    tech.lat = payload.lat
    tech.lng = payload.lng
    tech.last_position_update = datetime.utcnow()
    tech.tracking_attivo = True

    # Aggiorna la posizione anche dei lavori in corso assegnati a questo tecnico
    in_corso_works = db.query(Work).filter(
        Work.tecnico_assegnato_id == tech.id,
        Work.stato == "in_corso",
        Work.archived == False,
    ).all()
    for work in in_corso_works:
        work.lat = payload.lat
        work.lng = payload.lng

    # Se era offline, diventa disponibile
    if tech.stato_posizione == "offline":
        tech.stato_posizione = "disponibile"

    db.commit()
    db.refresh(tech)

    return {
        "message": "Posizione aggiornata",
        "technician_id": tech.id,
        "lat": tech.lat,
        "lng": tech.lng,
        "stato_posizione": tech.stato_posizione,
    }


# ── PUT /technicians/{id}/tracking ────────────────────────────────

@router.put("/technicians/{tech_id}/tracking")
def update_tracking(tech_id: int, payload: TrackingUpdate, db: Session = Depends(get_db)):
    """
    Attiva/disattiva il tracking di un tecnico.
    Se disattivato, il tecnico va offline e non appare sulla mappa.
    """
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Tecnico non trovato")

    tech.tracking_attivo = payload.tracking_attivo

    if not payload.tracking_attivo:
        tech.stato_posizione = "offline"

    db.commit()
    db.refresh(tech)

    return {
        "message": f"Tracking {'attivato' if payload.tracking_attivo else 'disattivato'}",
        "technician_id": tech.id,
        "tracking_attivo": tech.tracking_attivo,
        "stato_posizione": tech.stato_posizione,
    }


# ── POST /sos/{technician_id} ────────────────────────────────────

@router.post("/sos/{tech_id}", response_model=SOSResponse)
def trigger_sos(tech_id: int, db: Session = Depends(get_db)):
    """
    SOS: un tecnico chiede aiuto.
    - Marca il tecnico come SOS
    - Trova i 3 tecnici disponibili più vicini
    - Restituisce la lista ordinata per distanza
    """
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Tecnico non trovato")

    if not tech.lat or not tech.lng:
        raise HTTPException(
            status_code=400,
            detail="Il tecnico non ha una posizione GPS. Inviare /posizione da Telegram prima."
        )

    # Marca come SOS
    tech.stato_posizione = "sos"
    db.commit()

    # Trova i più vicini
    nearest = find_nearest_technicians(
        db,
        target_lat=tech.lat,
        target_lng=tech.lng,
        limit=3,
        exclude_id=tech.id,
    )

    nearest_list = []
    for item in nearest:
        t = item["technician"]
        nearest_list.append(SOSResult(
            technician_id=t.id,
            nome=t.nome,
            cognome=t.cognome,
            telefono=t.telefono,
            lat=t.lat,
            lng=t.lng,
            distance_km=item["distance_km"],
        ))

    tech_name = f"{tech.nome} {tech.cognome}"

    # Notifica Telegram al tecnico più vicino (se presente)
    if nearest_list:
        _notify_sos_telegram(nearest_list[0], tech, db)

    message = f"SOS attivato per {tech_name}."
    if nearest_list:
        message += f" Tecnico più vicino: {nearest_list[0].nome} {nearest_list[0].cognome} ({nearest_list[0].distance_km} km)"
    else:
        message += " Nessun tecnico disponibile trovato nelle vicinanze."

    return SOSResponse(
        sos_technician_id=tech.id,
        sos_technician_name=tech_name,
        nearest=nearest_list,
        message=message,
    )


@router.post("/clear-sos/{tech_id}")
def clear_sos(tech_id: int, db: Session = Depends(get_db)):
    """
    Disattiva manualmente SOS per un tecnico.
    Aggiorna SOLO stato tecnico, senza toccare i lavori.
    """
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Tecnico non trovato")

    old_status = tech.stato_posizione

    has_in_corso = db.query(Work).filter(
        Work.tecnico_assegnato_id == tech.id,
        Work.stato == "in_corso",
        Work.archived == False,
    ).first()

    if not tech.tracking_attivo:
        new_status = "offline"
    else:
        new_status = "occupato" if has_in_corso else "disponibile"

    tech.stato_posizione = new_status
    db.commit()

    return {
        "message": "SOS disattivato",
        "technician_id": tech.id,
        "old_status": old_status,
        "new_status": new_status,
    }


def _notify_sos_telegram(nearest: SOSResult, sos_tech: Technician, db: Session):
    """Invia notifica Telegram al tecnico più vicino per SOS."""
    try:
        target_tech = db.query(Technician).filter(Technician.id == nearest.technician_id).first()
        if target_tech and target_tech.telegram_id:
            import app.utils.telegram as telegram_utils
            msg = (
                f"🚨 SOS da {sos_tech.nome} {sos_tech.cognome}!\n\n"
                f"📍 È a {nearest.distance_km} km da te.\n"
                f"📞 Telefono: {sos_tech.telefono}\n\n"
                f"Sei il tecnico disponibile più vicino."
            )
            telegram_utils.send_message_to_telegram(target_tech.telegram_id, msg)
            logger.info("SOS notification sent to tech %d", target_tech.id)
    except Exception as e:
        logger.error("Failed to send SOS telegram notification: %s", e)


# ── POST /geocode-work/{work_id} ─────────────────────────────────

@router.post("/geocode-work/{work_id}")
async def geocode_work(work_id: int, db: Session = Depends(get_db)):
    """Geocodifica un lavoro specifico dal suo indirizzo."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")
    if not work.indirizzo:
        raise HTTPException(status_code=400, detail="Lavoro senza indirizzo")

    coords = await geocode_address(work.indirizzo)
    if not coords:
        raise HTTPException(status_code=404, detail=f"Indirizzo non geocodificabile: {work.indirizzo}")

    work.lat, work.lng = coords
    db.commit()
    return {"message": "Geocodificato", "work_id": work.id, "lat": work.lat, "lng": work.lng}


# ── POST /geocode-all-works ──────────────────────────────────────

@router.post("/geocode-all-works")
async def geocode_all_works(db: Session = Depends(get_db)):
    """
    Geocodifica tutti i lavori attivi che non hanno ancora coordinate.
    Usa un delay per rispettare il rate limit di Nominatim (1 req/sec).
    """
    import asyncio

    works = db.query(Work).filter(
        Work.lat.is_(None),
        Work.indirizzo.isnot(None),
        Work.archived == False,
    ).all()

    results = {"geocoded": 0, "failed": 0, "total": len(works)}

    for work in works:
        coords = await geocode_address(work.indirizzo)
        if coords:
            work.lat, work.lng = coords
            results["geocoded"] += 1
        else:
            results["failed"] += 1

        # Rispetta rate limit Nominatim: max 1 req/sec
        await asyncio.sleep(1.1)

    db.commit()
    return results


# ── POST /sync-technician-status ─────────────────────────────────

@router.post("/sync-technician-status")
def sync_technician_status(db: Session = Depends(get_db)):
    """
    Ricalcola lo stato di tutti i tecnici in base ai lavori assegnati.
    - Se ha lavori in_corso → occupato
    - Se non ha lavori in_corso → disponibile (se non era offline/sos)

    Chiamato dal bottone "Aggiorna" della Centrale Operativa.
    """
    technicians = db.query(Technician).all()
    updated = []

    for tech in technicians:
        # Salta tecnici offline o in SOS (stati manuali)
        if tech.stato_posizione in ("offline", "sos"):
            continue

        # Controlla se ha lavori in_corso
        has_in_corso = db.query(Work).filter(
            Work.tecnico_assegnato_id == tech.id,
            Work.stato == "in_corso",
            Work.archived == False,
        ).first()

        new_status = "occupato" if has_in_corso else "disponibile"

        if tech.stato_posizione != new_status:
            old_status = tech.stato_posizione
            tech.stato_posizione = new_status
            updated.append({
                "id": tech.id,
                "nome": f"{tech.nome} {tech.cognome}",
                "old": old_status,
                "new": new_status,
            })
            logger.info("Sync: tech %d (%s %s) %s → %s",
                       tech.id, tech.nome, tech.cognome, old_status, new_status)

    db.commit()
    return {
        "message": f"Sincronizzati {len(updated)} tecnici",
        "updated": updated,
        "total_checked": len(technicians),
    }
