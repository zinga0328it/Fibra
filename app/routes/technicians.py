from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Technician, Team
from typing import List
from app.utils.security import verify_api_key
from app.schemas import TechnicianCreate, TechnicianOut

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
def create_technician(payload: TechnicianCreate, db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    tech = Technician(nome=payload.nome, cognome=payload.cognome, telefono=payload.telefono, squadra_id=payload.squadra_id)
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech