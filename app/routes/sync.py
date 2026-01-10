from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.models import ONTModemSync, ONT, Modem, Work
from typing import List, Optional
from app.utils.security import verify_api_key
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["sync"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SyncCreate(BaseModel):
    ont_id: int
    modem_id: int
    work_id: int
    sync_method: str  # pppoe, dhcp, static, bridge
    sync_config: Optional[dict] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    installation_notes: Optional[str] = None

class SyncUpdate(BaseModel):
    sync_config: Optional[dict] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    installation_notes: Optional[str] = None
    technician_notes: Optional[str] = None
    sync_status: Optional[str] = None

class SyncOut(BaseModel):
    id: int
    ont_id: int
    modem_id: int
    work_id: int
    sync_method: str
    sync_config: Optional[dict]
    wifi_ssid: Optional[str]
    wifi_password: Optional[str]
    installation_notes: Optional[str]
    technician_notes: Optional[str]
    sync_status: str
    synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/work/{work_id}", response_model=List[SyncOut])
def get_sync_by_work(work_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get synchronization records for a specific work"""
    syncs = db.query(ONTModemSync).filter(ONTModemSync.work_id == work_id).all()
    return syncs

@router.get("/{sync_id}", response_model=SyncOut)
def get_sync(sync_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get synchronization record by ID"""
    sync = db.query(ONTModemSync).filter(ONTModemSync.id == sync_id).first()
    if not sync:
        raise HTTPException(status_code=404, detail="Synchronization record not found")
    return sync

@router.post("/{ont_id}/{modem_id}", response_model=SyncOut)
def create_sync(ont_id: int, modem_id: int, sync: SyncCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Create a new ONT-Modem synchronization record"""
    # Validate that ONT and Modem exist
    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    work = db.query(Work).filter(Work.id == sync.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    # Check if sync already exists for this ONT-Modem pair in this work
    existing = db.query(ONTModemSync).filter(
        ONTModemSync.ont_id == ont_id,
        ONTModemSync.modem_id == modem_id,
        ONTModemSync.work_id == sync.work_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Synchronization already exists for this ONT-Modem pair in this work")

    db_sync = ONTModemSync(
        ont_id=ont_id,
        modem_id=modem_id,
        work_id=sync.work_id,
        sync_method=sync.sync_method,
        sync_config=sync.sync_config,
        wifi_ssid=sync.wifi_ssid,
        wifi_password=sync.wifi_password,
        installation_notes=sync.installation_notes
    )
    db.add(db_sync)
    db.commit()
    db.refresh(db_sync)
    return db_sync

@router.put("/{sync_id}/complete")
def complete_sync(sync_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark synchronization as completed"""
    sync = db.query(ONTModemSync).filter(ONTModemSync.id == sync_id).first()
    if not sync:
        raise HTTPException(status_code=404, detail="Synchronization record not found")

    sync.sync_status = "completed"
    sync.synced_at = datetime.utcnow()

    db.commit()
    return {"message": "Synchronization marked as completed"}

@router.put("/{sync_id}/notes")
def update_sync_notes(sync_id: int, notes_update: SyncUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update technician notes and configuration"""
    sync = db.query(ONTModemSync).filter(ONTModemSync.id == sync_id).first()
    if not sync:
        raise HTTPException(status_code=404, detail="Synchronization record not found")

    update_data = notes_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sync, field, value)

    db.commit()
    return {"message": "Synchronization notes updated successfully"}

@router.put("/{sync_id}", response_model=SyncOut)
def update_sync(sync_id: int, sync_update: SyncUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Update synchronization record"""
    sync = db.query(ONTModemSync).filter(ONTModemSync.id == sync_id).first()
    if not sync:
        raise HTTPException(status_code=404, detail="Synchronization record not found")

    update_data = sync_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sync, field, value)

    db.commit()
    db.refresh(sync)
    return sync

@router.delete("/{sync_id}")
def delete_sync(sync_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Delete synchronization record"""
    sync = db.query(ONTModemSync).filter(ONTModemSync.id == sync_id).first()
    if not sync:
        raise HTTPException(status_code=404, detail="Synchronization record not found")

    db.delete(sync)
    db.commit()
    return {"message": "Synchronization record deleted successfully"}

@router.get("/", response_model=List[SyncOut])
def get_all_syncs(
    status: Optional[str] = None,
    work_id: Optional[int] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all synchronization records with optional filtering"""
    query = db.query(ONTModemSync)

    if status:
        query = query.filter(ONTModemSync.sync_status == status)

    if work_id:
        query = query.filter(ONTModemSync.work_id == work_id)

    return query.all()