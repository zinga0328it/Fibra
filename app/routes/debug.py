from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Work, Technician, Team, Document, WorkEvent, DocumentAppliedWork, User
from app.utils.auth import auth_required
from typing import List
import base64
import decimal
import uuid
import json
from datetime import datetime

router = APIRouter(prefix='/debug', tags=['debug'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('/db')
def debug_db(table: str = Query('works'), limit: int = Query(100), db: Session = Depends(get_db), current_user = Depends(auth_required(['admin','backoffice']))):
    allowed = {
        'works': Work,
        'technicians': Technician,
        'teams': Team,
        'documents': Document,
        'work_events': WorkEvent,
        'document_applied_works': DocumentAppliedWork,
        'users': User
    }
    if table not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown table {table}. Allowed: {list(allowed.keys())}")
    model = allowed[table]
    # Get rows
    rows = db.query(model).limit(limit).all()
    out = []
    for r in rows:
        row = {}
        for col in r.__table__.columns:
            val = getattr(r, col.name)
            # Ensure some common non-JSON types are converted to serializable forms
            if isinstance(val, datetime):
                row[col.name] = val.isoformat()
            elif isinstance(val, (bytes, bytearray, memoryview)):
                b = bytes(val)
                # Try to decode as UTF-8 first; if that fails, return a base64 preview or a placeholder
                try:
                    row[col.name] = b.decode('utf-8')
                except Exception:
                    if len(b) <= 512:
                        row[col.name] = 'base64:' + base64.b64encode(b).decode('ascii')
                    else:
                        row[col.name] = f'<binary: {len(b)} bytes>'
            elif isinstance(val, decimal.Decimal):
                # Decimal isn't JSON serializable directly; convert to float or string
                try:
                    row[col.name] = float(val)
                except Exception:
                    row[col.name] = str(val)
            elif isinstance(val, uuid.UUID):
                row[col.name] = str(val)
            else:
                row[col.name] = val
        out.append(row)
    return {'table': table, 'count': len(out), 'rows': out}
