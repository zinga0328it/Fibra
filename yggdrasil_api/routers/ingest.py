"""
Ingest Router - For receiving data from external sources
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path to import from main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, engine
from app.models.models import Work, Technician
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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

API_KEY = os.getenv("YGG_API_KEY", "your-secure-yggdrasil-key-here")

async def verify_key(x_key: str = Header(..., alias="X-KEY")):
    if x_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_key


# ============ Endpoints ============

@router.post("/work", response_model=IngestResponse, dependencies=[Depends(verify_key)])
async def ingest_single_work(work: WorkIngest):
    """Ingest a single work order"""
    db: Session = SessionLocal()
    try:
        # Check if work already exists
        existing_work = db.query(Work).filter(Work.numero_wr == work.numero_wr).first()
        
        if existing_work:
            # Update existing work
            if work.nome_cliente:
                existing_work.nome_cliente = work.nome_cliente
            if work.telefono_cliente:
                # Store phone in extra_fields if not already there
                if not existing_work.extra_fields:
                    existing_work.extra_fields = {}
                existing_work.extra_fields['telefono'] = work.telefono_cliente
            if work.indirizzo:
                existing_work.indirizzo = work.indirizzo
            if work.operatore:
                existing_work.operatore = work.operatore
            if work.tipo_lavoro:
                existing_work.tipo_lavoro = work.tipo_lavoro
            if work.note:
                existing_work.note = work.note
            if work.extra_fields:
                if not existing_work.extra_fields:
                    existing_work.extra_fields = {}
                existing_work.extra_fields.update(work.extra_fields)
            
            db.commit()
            message = f"Work {work.numero_wr} updated"
        else:
            # Create new work
            new_work = Work(
                numero_wr=work.numero_wr,
                nome_cliente=work.nome_cliente,
                indirizzo=work.indirizzo,
                operatore=work.operatore,
                tipo_lavoro=work.tipo_lavoro,
                note=work.note,
                stato="aperto",
                data_apertura=datetime.now(),
                extra_fields={
                    "telefono": work.telefono_cliente,
                    "source": "yggdrasil",
                    "data_appuntamento": work.data_appuntamento,
                    **(work.extra_fields or {})
                }
            )
            db.add(new_work)
            db.commit()
            message = f"Work {work.numero_wr} created"
        
        return IngestResponse(
            ok=True,
            message=message,
            received=1,
            processed=1
        )
    except IntegrityError as e:
        db.rollback()
        return IngestResponse(
            ok=False,
            message=f"Work {work.numero_wr} already exists or constraint violation",
            received=1,
            processed=0,
            errors=[str(e)]
        )
    except Exception as e:
        db.rollback()
        return IngestResponse(
            ok=False,
            message=str(e),
            received=1,
            processed=0,
            errors=[str(e)]
        )
    finally:
        db.close()


@router.post("/bulk", response_model=IngestResponse, dependencies=[Depends(verify_key)])
async def ingest_bulk_works(request: BulkIngestRequest):
    """Ingest multiple work orders at once"""
    db: Session = SessionLocal()
    errors = []
    processed = 0
    
    try:
        for work in request.works:
            try:
                # Check if work already exists
                existing_work = db.query(Work).filter(Work.numero_wr == work.numero_wr).first()
                
                if existing_work:
                    # Update existing work
                    if work.nome_cliente:
                        existing_work.nome_cliente = work.nome_cliente
                    if work.telefono_cliente:
                        if not existing_work.extra_fields:
                            existing_work.extra_fields = {}
                        existing_work.extra_fields['telefono'] = work.telefono_cliente
                    if work.indirizzo:
                        existing_work.indirizzo = work.indirizzo
                    if work.operatore:
                        existing_work.operatore = work.operatore
                    if work.tipo_lavoro:
                        existing_work.tipo_lavoro = work.tipo_lavoro
                    if work.note:
                        existing_work.note = work.note
                    if work.extra_fields:
                        if not existing_work.extra_fields:
                            existing_work.extra_fields = {}
                        existing_work.extra_fields.update(work.extra_fields)
                else:
                    # Create new work
                    new_work = Work(
                        numero_wr=work.numero_wr,
                        nome_cliente=work.nome_cliente,
                        indirizzo=work.indirizzo,
                        operatore=work.operatore,
                        tipo_lavoro=work.tipo_lavoro,
                        note=work.note,
                        stato="aperto",
                        data_apertura=datetime.now(),
                        extra_fields={
                            "telefono": work.telefono_cliente,
                            "source": request.source or "yggdrasil",
                            "data_appuntamento": work.data_appuntamento,
                            **(work.extra_fields or {})
                        }
                    )
                    db.add(new_work)
                
                processed += 1
            except Exception as e:
                errors.append(f"{work.numero_wr}: {str(e)}")
        
        db.commit()
        
        return IngestResponse(
            ok=len(errors) == 0,
            message=f"Bulk ingest from {request.source}: {processed} processed, {len(errors)} errors",
            received=len(request.works),
            processed=processed,
            errors=errors
        )
    except Exception as e:
        db.rollback()
        return IngestResponse(
            ok=False,
            message=f"Bulk ingest failed: {str(e)}",
            received=len(request.works),
            processed=processed,
            errors=[str(e)] + errors
        )
    finally:
        db.close()


@router.get("/status", dependencies=[Depends(verify_key)])
async def ingest_status():
    """Get ingest queue status"""
    return {
        "queue_size": 0,
        "last_ingest": datetime.now().isoformat(),
        "status": "idle"
    }
