from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent
from typing import List
from app.utils.security import verify_api_key
from app.schemas import WorkCreate, WorkOut, WorkStatusUpdate
from io import BytesIO
try:
    import pytesseract
except Exception:
    pytesseract = None
from PIL import Image
try:
    import pdfplumber
except Exception:
    pdfplumber = None
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/works", tags=["works"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=WorkOut)
async def upload_work(file: UploadFile = File(...), db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    content = await file.read()
    text = ""
    if file.filename.endswith('.pdf') and pdfplumber:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
    elif file.filename.endswith(('.png', '.jpg', '.jpeg')) and pytesseract:
        image = Image.open(BytesIO(content))
        text = pytesseract.image_to_string(image)
    else:
        text = content.decode('utf-8')
    
    # Simple parsing, assume JSON for now
    try:
        data = json.loads(text)
    except Exception:
        data = {"numero_wr": "unknown", "operatore": "unknown", "indirizzo": "unknown", "nome_cliente": "unknown", "tipo_lavoro": "attivazione"}

    # Allow only known model fields and collect extras into extra_fields
    allowed_keys = {"numero_wr", "operatore", "indirizzo", "nome_cliente", "tipo_lavoro", "note", "extra_fields"}
    work_kwargs = {k: v for k, v in data.items() if k in allowed_keys}
    extras = {k: v for k, v in data.items() if k not in allowed_keys}
    if extras:
        if "extra_fields" in work_kwargs and isinstance(work_kwargs["extra_fields"], dict):
            work_kwargs["extra_fields"].update(extras)
        else:
            work_kwargs["extra_fields"] = extras

    work = Work(**work_kwargs, data_apertura=datetime.now())
    db.add(work)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.refresh(work)
    # Add event
    event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="created", description="Work uploaded", user_id=None)
    db.add(event)
    db.commit()
    return work


@router.post("/", response_model=WorkOut)
def create_work(payload: WorkCreate, db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    work_kwargs = payload.dict(exclude_unset=True)
    work = Work(**work_kwargs, data_apertura=datetime.now())
    db.add(work)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.refresh(work)
    # Add event
    event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="created", description="Work created via API", user_id=None)
    db.add(event)
    db.commit()
    return work

@router.get("/", response_model=List[WorkOut])
def get_works(db: Session = Depends(get_db)):
    works = db.query(Work).all()
    return works

@router.put("/{work_id}/assign/{tech_id}")
def assign_work(work_id: int, tech_id: int, db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    tech = db.query(Technician).filter(Technician.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    work.tecnico_assegnato_id = tech_id
    work.stato = "in_corso"
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    event = WorkEvent(work_id=work_id, timestamp=datetime.now(), event_type="assigned", description=f"Assigned to tech {tech_id}", user_id=tech_id)
    db.add(event)
    db.commit()
    return {"message": "Assigned"}

@router.put("/{work_id}/status")
def update_status(work_id: int, status: WorkStatusUpdate | None = None, db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    # Accept either a query string or payload
    new_status = None
    if isinstance(status, WorkStatusUpdate):
        new_status = status.status
    elif isinstance(status, str):
        new_status = status
    else:
        raise HTTPException(status_code=400, detail="Missing or invalid status")
    work.stato = new_status
    if status == "chiuso":
        work.data_chiusura = datetime.now()
    db.commit()
    event = WorkEvent(work_id=work_id, timestamp=datetime.now(), event_type="status_change", description=f"Status to {status}", user_id=work.tecnico_assegnato_id)
    db.add(event)
    db.commit()
    return {"message": "Status updated"}