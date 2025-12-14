"""
Manual Router - For manual data entry and management
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# ============ Schemas ============

class ManualWorkCreate(BaseModel):
    numero_wr: str
    nome_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    indirizzo: Optional[str] = None
    operatore: Optional[str] = None
    tipo_lavoro: Optional[str] = None
    tecnico_id: Optional[int] = None
    note: Optional[str] = None
    stato: str = "aperto"


class ManualWorkUpdate(BaseModel):
    nome_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    indirizzo: Optional[str] = None
    operatore: Optional[str] = None
    tipo_lavoro: Optional[str] = None
    tecnico_id: Optional[int] = None
    note: Optional[str] = None
    stato: Optional[str] = None


class TechnicianCreate(BaseModel):
    nome: str
    cognome: str
    telefono: Optional[str] = None
    telegram_id: Optional[str] = None
    squadra_id: Optional[int] = None


# ============ Auth Dependency ============

import os
API_KEY = os.getenv("YGG_API_KEY", "your-secure-yggdrasil-key-here")

async def verify_key(x_key: str = Header(..., alias="X-KEY")):
    if x_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_key


# ============ Work Endpoints ============

@router.post("/work", dependencies=[Depends(verify_key)])
async def create_work(work: ManualWorkCreate):
    """Create a new work order manually"""
    # Here you would connect to the main database
    # For now, return mock response
    return {
        "ok": True,
        "id": 999,  # Would be real ID from DB
        "numero_wr": work.numero_wr,
        "stato": work.stato,
        "created_at": datetime.now().isoformat()
    }


@router.put("/work/{work_id}", dependencies=[Depends(verify_key)])
async def update_work(work_id: int, work: ManualWorkUpdate):
    """Update an existing work order"""
    return {
        "ok": True,
        "id": work_id,
        "updated_at": datetime.now().isoformat(),
        "changes": work.dict(exclude_none=True)
    }


@router.delete("/work/{work_id}", dependencies=[Depends(verify_key)])
async def delete_work(work_id: int):
    """Delete a work order"""
    return {
        "ok": True,
        "id": work_id,
        "deleted_at": datetime.now().isoformat()
    }


@router.post("/work/{work_id}/status", dependencies=[Depends(verify_key)])
async def change_work_status(work_id: int, status: str):
    """Change work status"""
    valid_statuses = ["aperto", "in_corso", "sospeso", "chiuso"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    return {
        "ok": True,
        "id": work_id,
        "new_status": status,
        "changed_at": datetime.now().isoformat()
    }


# ============ Technician Endpoints ============

@router.post("/technician", dependencies=[Depends(verify_key)])
async def create_technician(tech: TechnicianCreate):
    """Create a new technician"""
    return {
        "ok": True,
        "id": 999,
        "nome": tech.nome,
        "cognome": tech.cognome,
        "created_at": datetime.now().isoformat()
    }


@router.get("/technicians", dependencies=[Depends(verify_key)])
async def list_technicians():
    """List all technicians"""
    # Mock data - would come from DB
    return {
        "technicians": [
            {"id": 1, "nome": "Tecnico", "cognome": "Test", "telefono": "3331234567"}
        ],
        "total": 1
    }


# ============ Sync Endpoints ============

@router.post("/sync/push", dependencies=[Depends(verify_key)])
async def push_to_remote():
    """Push local changes to remote server"""
    return {
        "ok": True,
        "message": "Push initiated",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/sync/pull", dependencies=[Depends(verify_key)])
async def pull_from_remote():
    """Pull changes from remote server"""
    return {
        "ok": True,
        "message": "Pull initiated",
        "timestamp": datetime.now().isoformat()
    }
