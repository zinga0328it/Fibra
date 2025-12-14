from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Technician, Team
from typing import List
from app.utils.security import verify_api_key
from app.schemas import TechnicianCreate, TechnicianOut, TechnicianUpdate
from app.utils.auth import auth_required

router = APIRouter(prefix="/technicians", tags=["technicians"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[TechnicianOut])
def get_technicians(db: Session = Depends(get_db)):
    techs = db.query(Technician).all()
    return techs

@router.post("/", response_model=TechnicianOut)
def create_technician(payload: TechnicianCreate, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin']))):
    tech = Technician(
        nome=payload.nome, 
        cognome=payload.cognome, 
        telefono=payload.telefono, 
        squadra_id=payload.squadra_id,
        telegram_id=payload.telegram_id
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech

@router.patch("/{tech_id}", response_model=TechnicianOut)
def update_technician(
    tech_id: int, 
    payload: TechnicianUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(auth_required(['admin']))
):
    """Aggiorna un tecnico esistente (anche solo il telegram_id) - RICHIEDE AUTENTICAZIONE ADMIN"""
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Tecnico non trovato")
    
    # Aggiorna solo i campi forniti
    if payload.nome is not None:
        tech.nome = payload.nome
    if payload.cognome is not None:
        tech.cognome = payload.cognome
    if payload.telefono is not None:
        tech.telefono = payload.telefono
    if payload.squadra_id is not None:
        tech.squadra_id = payload.squadra_id
    if payload.telegram_id is not None:
        tech.telegram_id = payload.telegram_id
    
    db.commit()
    db.refresh(tech)
    return tech