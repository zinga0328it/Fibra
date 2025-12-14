"""
Ingest Router - For receiving data from external sources
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# ============ Schemas ============

class WorkIngest(BaseModel):
    numero_wr: str
    nome_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    indirizzo: Optional[str] = None
    operatore: Optional[str] = None
    tipo_lavoro: Optional[str] = None
    note: Optional[str] = None
    data_appuntamento: Optional[str] = None
    extra_fields: Optional[Dict[str, Any]] = None


class BulkIngestRequest(BaseModel):
    works: List[WorkIngest]
    source: Optional[str] = "yggdrasil"


class IngestResponse(BaseModel):
    ok: bool
    message: str
    received: int
    processed: int
    errors: List[str] = []


# ============ Auth Dependency ============

import os
API_KEY = os.getenv("YGG_API_KEY", "your-secure-yggdrasil-key-here")

async def verify_key(x_key: str = Header(..., alias="X-KEY")):
    if x_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_key


# ============ Endpoints ============

@router.post("/work", response_model=IngestResponse, dependencies=[Depends(verify_key)])
async def ingest_single_work(work: WorkIngest):
    """Ingest a single work order"""
    try:
        # Here you would save to database
        # For now, just return success
        return IngestResponse(
            ok=True,
            message=f"Work {work.numero_wr} received",
            received=1,
            processed=1
        )
    except Exception as e:
        return IngestResponse(
            ok=False,
            message=str(e),
            received=1,
            processed=0,
            errors=[str(e)]
        )


@router.post("/bulk", response_model=IngestResponse, dependencies=[Depends(verify_key)])
async def ingest_bulk_works(request: BulkIngestRequest):
    """Ingest multiple work orders at once"""
    errors = []
    processed = 0
    
    for work in request.works:
        try:
            # Process each work
            processed += 1
        except Exception as e:
            errors.append(f"{work.numero_wr}: {str(e)}")
    
    return IngestResponse(
        ok=len(errors) == 0,
        message=f"Bulk ingest from {request.source}",
        received=len(request.works),
        processed=processed,
        errors=errors
    )


@router.get("/status", dependencies=[Depends(verify_key)])
async def ingest_status():
    """Get ingest queue status"""
    return {
        "queue_size": 0,
        "last_ingest": datetime.now().isoformat(),
        "status": "idle"
    }
