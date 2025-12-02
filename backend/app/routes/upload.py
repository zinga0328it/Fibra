from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import re
from app.database import get_db
from app.models import Job
from app.schemas import JobResponse
from app.config import settings
from app.services.pdf_parser import parse_pdf_work_order

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/workorder", response_model=List[JobResponse])
async def upload_work_order(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF or WR work order file and parse it into jobs."""
    
    # Validate file type
    allowed_extensions = [".pdf", ".wr", ".txt"]
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Save file temporarily
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join(settings.upload_dir, temp_filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Parse the file
        if file_ext == ".pdf":
            jobs_data = parse_pdf_work_order(temp_path)
        else:
            # For WR or TXT files, parse as text
            jobs_data = parse_text_work_order(temp_path)
        
        # Create jobs in database
        created_jobs = []
        for job_data in jobs_data:
            db_job = Job(
                work_order_number=job_data.get("work_order_number"),
                customer_name=job_data.get("customer_name"),
                customer_address=job_data.get("customer_address"),
                customer_phone=job_data.get("customer_phone"),
                description=job_data.get("description"),
                source_file=file.filename,
                extra_fields=str(job_data.get("extra_fields", {}))
            )
            db.add(db_job)
            created_jobs.append(db_job)
        
        # Single commit for all jobs
        db.commit()
        
        # Refresh all jobs to get their IDs
        for db_job in created_jobs:
            db.refresh(db_job)
        
        return created_jobs
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


def parse_text_work_order(file_path: str) -> List[dict]:
    """Parse a text-based work order file (WR or TXT format)."""
    jobs = []
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Split by common delimiters for multiple work orders
    work_orders = re.split(r'(?:---+|===+|\n\n\n+)', content)
    
    for wo in work_orders:
        if not wo.strip():
            continue
        
        job_data = {
            "work_order_number": None,
            "customer_name": None,
            "customer_address": None,
            "customer_phone": None,
            "description": None,
            "extra_fields": {}
        }
        
        # Try to extract common fields
        lines = wo.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for common patterns
            lower_line = line.lower()
            
            # Work order number patterns
            if any(pattern in lower_line for pattern in ["ordine:", "order:", "wo:", "wr:", "pratica:"]):
                parts = re.split(r'[:\s]+', line, 1)
                if len(parts) > 1:
                    job_data["work_order_number"] = parts[1].strip()
            
            # Customer name patterns
            elif any(pattern in lower_line for pattern in ["cliente:", "customer:", "nome:", "name:"]):
                parts = re.split(r'[:\s]+', line, 1)
                if len(parts) > 1:
                    job_data["customer_name"] = parts[1].strip()
            
            # Address patterns
            elif any(pattern in lower_line for pattern in ["indirizzo:", "address:", "via:", "location:"]):
                parts = re.split(r'[:\s]+', line, 1)
                if len(parts) > 1:
                    job_data["customer_address"] = parts[1].strip()
            
            # Phone patterns
            elif any(pattern in lower_line for pattern in ["telefono:", "phone:", "tel:", "cellulare:"]):
                parts = re.split(r'[:\s]+', line, 1)
                if len(parts) > 1:
                    job_data["customer_phone"] = parts[1].strip()
            
            # Description patterns
            elif any(pattern in lower_line for pattern in ["descrizione:", "description:", "lavoro:", "work:"]):
                parts = re.split(r'[:\s]+', line, 1)
                if len(parts) > 1:
                    job_data["description"] = parts[1].strip()
        
        # If we found any meaningful data, add the job
        if any(v for k, v in job_data.items() if k != "extra_fields" and v):
            jobs.append(job_data)
    
    # If no structured data was found, treat entire content as one job description
    if not jobs and content.strip():
        jobs.append({
            "work_order_number": None,
            "customer_name": None,
            "customer_address": None,
            "customer_phone": None,
            "description": content.strip()[:500],
            "extra_fields": {}
        })
    
    return jobs
