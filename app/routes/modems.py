from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.models import Modem, Work
from typing import List, Optional
from app.utils.security import verify_api_key
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/modems", tags=["modems"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ModemCreate(BaseModel):
    serial_number: str
    model: str
    type: str  # adsl, vdsl, fiber, etc.
    manufacturer: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    admin_username: Optional[str] = "admin"
    admin_password: Optional[str] = None
    sync_method: Optional[str] = None  # bridge, pppoe, dhcp
    sync_config: Optional[dict] = None
    configuration_notes: Optional[str] = None
    installation_notes: Optional[str] = None
    location: Optional[str] = None

class ModemUpdate(BaseModel):
    status: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    sync_method: Optional[str] = None
    sync_config: Optional[dict] = None
    configuration_notes: Optional[str] = None
    installation_notes: Optional[str] = None
    location: Optional[str] = None

class ModemOut(BaseModel):
    id: int
    serial_number: str
    model: str
    type: str
    manufacturer: Optional[str]
    status: str
    work_id: Optional[int]
    wifi_ssid: Optional[str]
    wifi_password: Optional[str]
    admin_username: Optional[str]
    admin_password: Optional[str]
    sync_method: Optional[str]
    sync_config: Optional[dict]
    configured_date: Optional[datetime]
    installed_at: Optional[datetime]
    configuration_notes: Optional[str]
    installation_notes: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ModemOut])
def get_modems(
    status: Optional[str] = None,
    type: Optional[str] = None,
    assigned: Optional[bool] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all modems with optional filtering"""
    query = db.query(Modem)

    if status:
        query = query.filter(Modem.status == status)

    if type:
        query = query.filter(Modem.type == type)

    if assigned is not None:
        if assigned:
            query = query.filter(Modem.work_id.isnot(None))
        else:
            query = query.filter(Modem.work_id.is_(None))

    return query.all()

@router.get("/{modem_id}", response_model=ModemOut)
def get_modem(modem_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get modem by ID"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")
    return modem

@router.post("/", response_model=ModemOut)
def create_modem(modem: ModemCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Create a new modem"""
    # Check if serial number already exists
    existing = db.query(Modem).filter(Modem.serial_number == modem.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Modem with this serial number already exists")

    db_modem = Modem(**modem.dict())
    db.add(db_modem)
    db.commit()
    db.refresh(db_modem)
    return db_modem

@router.put("/{modem_id}/assign/{work_id}")
def assign_modem_to_work(modem_id: int, work_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Assign modem to a work order"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    if modem.status != "available":
        raise HTTPException(status_code=400, detail="Modem is not available for assignment")

    modem.work_id = work_id
    modem.status = "assigned"
    modem.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Modem assigned successfully"}

@router.put("/{modem_id}/install")
def mark_modem_installed(modem_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark modem as installed"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    if modem.status != "assigned":
        raise HTTPException(status_code=400, detail="Modem must be assigned to a work before installation")

    modem.status = "installed"
    modem.installed_at = datetime.utcnow()
    modem.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Modem marked as installed"}

@router.put("/{modem_id}/configure")
def configure_modem(modem_id: int, config: dict, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update modem configuration"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    # Update configuration fields
    for key, value in config.items():
        if hasattr(modem, key):
            setattr(modem, key, value)

    modem.status = "configured"
    modem.configured_date = datetime.utcnow()
    modem.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Modem configured successfully"}

@router.put("/{modem_id}/return")
def return_modem(modem_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark modem as returned"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    modem.status = "available"
    modem.work_id = None
    modem.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Modem returned successfully"}

@router.put("/{modem_id}", response_model=ModemOut)
def update_modem(modem_id: int, modem_update: ModemUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update modem information"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    update_data = modem_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(modem, field, value)

    modem.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(modem)
    return modem

@router.delete("/{modem_id}")
def delete_modem(modem_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Delete modem (only if not assigned or installed)"""
    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    if modem.status in ["assigned", "installed"]:
        raise HTTPException(status_code=400, detail="Cannot delete assigned or installed modem")

    db.delete(modem)
    db.commit()
    return {"message": "Modem deleted successfully"}