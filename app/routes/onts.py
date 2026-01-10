from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.models import ONT, Work
from typing import List, Optional
from app.utils.security import verify_api_key
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/onts", tags=["onts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ONTCreate(BaseModel):
    serial_number: str
    model: str
    manufacturer: Optional[str] = None
    pon_port: Optional[str] = None
    vlan_id: Optional[int] = None
    ip_address: Optional[str] = None
    installation_notes: Optional[str] = None
    technician_notes: Optional[str] = None
    location: Optional[str] = None

class ONTUpdate(BaseModel):
    status: Optional[str] = None
    pon_port: Optional[str] = None
    vlan_id: Optional[int] = None
    ip_address: Optional[str] = None
    installation_notes: Optional[str] = None
    technician_notes: Optional[str] = None
    location: Optional[str] = None

class ONTOut(BaseModel):
    id: int
    serial_number: str
    model: str
    manufacturer: Optional[str]
    status: str
    work_id: Optional[int]
    assigned_date: Optional[datetime]
    installed_at: Optional[datetime]
    returned_date: Optional[datetime]
    pon_port: Optional[str]
    vlan_id: Optional[int]
    ip_address: Optional[str]
    installation_notes: Optional[str]
    technician_notes: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ONTOut])
def get_onts(
    status: Optional[str] = None,
    assigned: Optional[bool] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all ONTs with optional filtering"""
    query = db.query(ONT)

    if status:
        query = query.filter(ONT.status == status)

    if assigned is not None:
        if assigned:
            query = query.filter(ONT.work_id.isnot(None))
        else:
            query = query.filter(ONT.work_id.is_(None))

    return query.all()

@router.get("/{ont_id}", response_model=ONTOut)
def get_ont(ont_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get ONT by ID"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")
    return ont

@router.post("/", response_model=ONTOut)
def create_ont(ont: ONTCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Create a new ONT"""
    # Check if serial number already exists
    existing = db.query(ONT).filter(ONT.serial_number == ont.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="ONT with this serial number already exists")

    db_ont = ONT(**ont.dict())
    db.add(db_ont)
    db.commit()
    db.refresh(db_ont)
    return db_ont

@router.put("/{ont_id}/assign/{work_id}")
def assign_ont_to_work(ont_id: int, work_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Assign ONT to a work order"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    if ont.status != "available":
        raise HTTPException(status_code=400, detail="ONT is not available for assignment")

    ont.work_id = work_id
    ont.status = "assigned"
    ont.assigned_date = datetime.utcnow()
    ont.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "ONT assigned successfully"}

@router.put("/{ont_id}/install")
def mark_ont_installed(ont_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark ONT as installed"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    if ont.status != "assigned":
        raise HTTPException(status_code=400, detail="ONT must be assigned to a work before installation")

    ont.status = "installed"
    ont.installed_at = datetime.utcnow()
    ont.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "ONT marked as installed"}

@router.put("/{ont_id}/return")
def return_ont(ont_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark ONT as returned"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    ont.status = "available"
    ont.returned_date = datetime.utcnow()
    ont.work_id = None
    ont.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "ONT returned successfully"}

@router.put("/{ont_id}", response_model=ONTOut)
def update_ont(ont_id: int, ont_update: ONTUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update ONT information"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    update_data = ont_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ont, field, value)

    ont.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ont)
    return ont

@router.delete("/{ont_id}")
def delete_ont(ont_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Delete ONT (only if not assigned)"""
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    if ont.work_id is not None:
        raise HTTPException(status_code=400, detail="Cannot delete assigned ONT")

    db.delete(ont)
    db.commit()
    return {"message": "ONT deleted successfully"}