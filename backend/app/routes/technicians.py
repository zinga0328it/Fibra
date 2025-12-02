from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Technician
from app.schemas import TechnicianCreate, TechnicianUpdate, TechnicianResponse

router = APIRouter(prefix="/api/technicians", tags=["technicians"])


@router.get("/", response_model=List[TechnicianResponse])
def get_technicians(db: Session = Depends(get_db)):
    return db.query(Technician).all()


@router.get("/{technician_id}", response_model=TechnicianResponse)
def get_technician(technician_id: int, db: Session = Depends(get_db)):
    technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician


@router.post("/", response_model=TechnicianResponse)
def create_technician(technician: TechnicianCreate, db: Session = Depends(get_db)):
    db_technician = Technician(**technician.model_dump())
    db.add(db_technician)
    db.commit()
    db.refresh(db_technician)
    return db_technician


@router.put("/{technician_id}", response_model=TechnicianResponse)
def update_technician(technician_id: int, technician: TechnicianUpdate, db: Session = Depends(get_db)):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    update_data = technician.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_technician, key, value)
    
    db.commit()
    db.refresh(db_technician)
    return db_technician


@router.delete("/{technician_id}")
def delete_technician(technician_id: int, db: Session = Depends(get_db)):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    db.delete(db_technician)
    db.commit()
    return {"message": "Technician deleted successfully"}
