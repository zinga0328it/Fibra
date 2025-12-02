from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid
from app.database import get_db
from app.models import Job, Note, Photo, JobStatus
from app.schemas import JobCreate, JobUpdate, JobResponse, NoteCreate, NoteResponse, PhotoResponse
from app.config import settings

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    status: Optional[str] = None,
    technician_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    
    if status:
        try:
            status_enum = JobStatus(status)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            pass
    
    if technician_id:
        query = query.filter(Job.technician_id == technician_id)
    
    return query.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job: JobUpdate, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job.model_dump(exclude_unset=True)
    
    # Handle status change
    if "status" in update_data:
        status_value = update_data["status"]
        if isinstance(status_value, str):
            update_data["status"] = JobStatus(status_value)
        elif hasattr(status_value, "value"):
            update_data["status"] = JobStatus(status_value.value)
        
        # Set closed_at when job is closed
        if update_data["status"] == JobStatus.CLOSED:
            update_data["closed_at"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_job, key, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job deleted successfully"}


# Notes endpoints
@router.post("/{job_id}/notes", response_model=NoteResponse)
def add_note(job_id: int, note: NoteCreate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db_note = Note(job_id=job_id, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/{job_id}/notes", response_model=List[NoteResponse])
def get_notes(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.query(Note).filter(Note.job_id == job_id).order_by(Note.created_at.desc()).all()


# Photos endpoints
@router.post("/{job_id}/photos", response_model=PhotoResponse)
async def upload_photo(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(settings.upload_dir, unique_filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create database record
    db_photo = Photo(
        job_id=job_id,
        filename=unique_filename,
        original_filename=file.filename,
        uploaded_via="web"
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


@router.get("/{job_id}/photos", response_model=List[PhotoResponse])
def get_photos(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.query(Photo).filter(Photo.job_id == job_id).order_by(Photo.created_at.desc()).all()
