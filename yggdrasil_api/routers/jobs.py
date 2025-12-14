"""
Jobs Router - For managing background jobs and sync tasks
"""

from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter()

# ============ Schemas ============

class JobCreate(BaseModel):
    job_type: str  # sync, backup, cleanup, etc.
    params: Optional[Dict[str, Any]] = {}


class JobStatus(BaseModel):
    job_id: str
    job_type: str
    status: str  # pending, running, completed, failed
    progress: int = 0
    message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# In-memory job storage (use Redis in production)
jobs_store: Dict[str, JobStatus] = {}
job_counter = 0


# ============ Auth Dependency ============

import os
API_KEY = os.getenv("YGG_API_KEY", "your-secure-yggdrasil-key-here")

async def verify_key(x_key: str = Header(..., alias="X-KEY")):
    if x_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_key


# ============ Background Tasks ============

async def run_sync_job(job_id: str):
    """Simulate a sync job"""
    jobs_store[job_id].status = "running"
    
    for i in range(1, 101, 10):
        await asyncio.sleep(0.5)  # Simulate work
        jobs_store[job_id].progress = i
        jobs_store[job_id].message = f"Syncing... {i}%"
    
    jobs_store[job_id].status = "completed"
    jobs_store[job_id].progress = 100
    jobs_store[job_id].completed_at = datetime.now().isoformat()
    jobs_store[job_id].message = "Sync completed successfully"


async def run_backup_job(job_id: str):
    """Simulate a backup job"""
    jobs_store[job_id].status = "running"
    jobs_store[job_id].message = "Creating backup..."
    
    await asyncio.sleep(2)
    
    jobs_store[job_id].status = "completed"
    jobs_store[job_id].progress = 100
    jobs_store[job_id].completed_at = datetime.now().isoformat()
    jobs_store[job_id].message = "Backup created"


# ============ Endpoints ============

@router.post("/create", dependencies=[Depends(verify_key)])
async def create_job(job: JobCreate, background_tasks: BackgroundTasks):
    """Create a new background job"""
    global job_counter
    job_counter += 1
    job_id = f"job_{job_counter}_{datetime.now().strftime('%H%M%S')}"
    
    job_status = JobStatus(
        job_id=job_id,
        job_type=job.job_type,
        status="pending",
        progress=0,
        created_at=datetime.now().isoformat()
    )
    jobs_store[job_id] = job_status
    
    # Schedule background task
    if job.job_type == "sync":
        background_tasks.add_task(run_sync_job, job_id)
    elif job.job_type == "backup":
        background_tasks.add_task(run_backup_job, job_id)
    else:
        jobs_store[job_id].status = "failed"
        jobs_store[job_id].message = f"Unknown job type: {job.job_type}"
    
    return {"ok": True, "job_id": job_id, "status": "pending"}


@router.get("/status/{job_id}", dependencies=[Depends(verify_key)])
async def get_job_status(job_id: str):
    """Get status of a specific job"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_store[job_id]


@router.get("/list", dependencies=[Depends(verify_key)])
async def list_jobs(status: Optional[str] = None):
    """List all jobs, optionally filtered by status"""
    jobs = list(jobs_store.values())
    
    if status:
        jobs = [j for j in jobs if j.status == status]
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }


@router.delete("/clear", dependencies=[Depends(verify_key)])
async def clear_completed_jobs():
    """Clear completed and failed jobs from the list"""
    to_remove = [jid for jid, j in jobs_store.items() if j.status in ["completed", "failed"]]
    for jid in to_remove:
        del jobs_store[jid]
    
    return {"ok": True, "cleared": len(to_remove)}
