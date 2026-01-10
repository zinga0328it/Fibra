from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from app.database import SessionLocal
from app.models.models import Work, Technician, WorkEvent, Document, DocumentAppliedWork
from typing import List
from app.utils.security import verify_api_key
from app.schemas import WorkCreate, WorkOut, WorkStatusUpdate
from app.schemas import WorkUpdate
from app.utils.ocr import extract_wr_fields, normalize_numero_wr
from app.utils.auth import auth_required
from io import BytesIO, StringIO
import csv
# We only accept PDFs here; image OCR is handled by documents routes
try:
    import pdfplumber
except Exception:
    pdfplumber = None
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import app.utils.telegram as telegram_utils
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/works", tags=["works"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_work(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    filename = (file.filename or '').lower()
    # Accept CSV and PDF uploads only here. JSON/file uploads are not accepted via this endpoint.
    if filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="JSON upload is not supported. Please use POST /works/ to create a work manually.")
    # CSV upload processing resumed: accept CSV for bulk create/upsert; otherwise handle single PDF upload.
    if file.filename.lower().endswith('.csv'):
        # Parse CSV
        text = content.decode('utf-8')
        reader = csv.DictReader(StringIO(text))
        works_created = []
        for row in reader:
            data = {k.lower().strip(): v.strip() for k, v in row.items() if v.strip()}
            # Map common column names
            field_map = {
                'numero wr': 'numero_wr',
                'numero_wr': 'numero_wr',
                'wr': 'numero_wr',
                'operatore': 'operatore',
                'fornitore': 'operatore',
                'indirizzo': 'indirizzo',
                'cliente': 'nome_cliente',
                'nome cliente': 'nome_cliente',
                'tipo lavoro': 'tipo_lavoro',
                'tipo_lavoro': 'tipo_lavoro',
                'lavoro': 'tipo_lavoro'
            }
            mapped_data = {}
            for k, v in data.items():
                mapped_key = field_map.get(k.lower(), k)
                mapped_data[mapped_key] = v
            # Set defaults
            mapped_data.setdefault("numero_wr", f"WR-{int(datetime.now().timestamp())}")
            # Normalize numero_wr to canonical format
            if mapped_data.get("numero_wr"):
                mapped_data["numero_wr"] = normalize_numero_wr(mapped_data["numero_wr"])
            mapped_data.setdefault("operatore", "unknown")
            mapped_data.setdefault("indirizzo", "unknown")
            mapped_data.setdefault("nome_cliente", "unknown")
            mapped_data.setdefault("tipo_lavoro", "attivazione")
            # Create or update work (upsert)
            existing = db.query(Work).filter(Work.numero_wr == mapped_data["numero_wr"]).first()
            if existing:
                # Update existing
                existing.operatore = mapped_data.get("operatore", existing.operatore)
                existing.indirizzo = mapped_data.get("indirizzo", existing.indirizzo)
                existing.nome_cliente = mapped_data.get("nome_cliente", existing.nome_cliente)
                existing.tipo_lavoro = mapped_data.get("tipo_lavoro", existing.tipo_lavoro)
                if mapped_data.get('note'):
                    existing.note = mapped_data.get('note')
                db.commit()
                # add event
                event = WorkEvent(work_id=existing.id, timestamp=datetime.now(), event_type="updated", description="Work updated from CSV", user_id=None)
                db.add(event)
                db.commit()
                works_created.append(existing)
            else:
                work = Work(**{k: v for k, v in mapped_data.items() if k in ["numero_wr", "operatore", "indirizzo", "nome_cliente", "tipo_lavoro", "note"]}, data_apertura=datetime.now())
                db.add(work)
                db.commit()
                db.refresh(work)
                event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type="created", description="Work uploaded from CSV", user_id=None)
                db.add(event)
                db.commit()
                works_created.append(work)
                notify_new_work(work, db)
        return {"message": f"Elaborati {len(works_created)} lavori dal CSV"}
    else:
        # Single file parsing as before
        # Only PDF uploads are allowed here (images and text/JSON are not supported via this endpoint)
        if file.filename.lower().endswith('.pdf') and pdfplumber:
            text = ""
            try:
                with pdfplumber.open(BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text
            except Exception:
                # If pdf parsing fails (file could be fake PDF, test stubs, etc.), try to decode as text
                try:
                    text = content.decode('utf-8')
                except Exception:
                    raise HTTPException(status_code=400, detail='Invalid or unreadable PDF')
        else:
            raise HTTPException(status_code=400, detail="Only PDF uploads are allowed here. Use /documents/upload to upload PDFs or POST /works/ to create a work manually.")
        
        # Try JSON first, otherwise extract fields using OCR heuristics
        try:
            data = json.loads(text)
        except Exception:
            data = extract_wr_fields(text)
            # Guarantee minimal required fields
            data.setdefault("numero_wr", "unknown")
            data.setdefault("operatore", "unknown")
            data.setdefault("indirizzo", "unknown")
            data.setdefault("nome_cliente", "unknown")
            data.setdefault("tipo_lavoro", "attivazione")

        # Allow only known model fields and collect extras into extra_fields
        allowed_keys = {"numero_wr", "operatore", "indirizzo", "nome_cliente", "tipo_lavoro", "note", "extra_fields"}
        # Normalize the numero_wr if present
        if data.get('numero_wr'):
            data['numero_wr'] = normalize_numero_wr(data.get('numero_wr'))
        work_kwargs = {k: v for k, v in data.items() if k in allowed_keys}
        extras = {k: v for k, v in data.items() if k not in allowed_keys}
        if extras:
            if "extra_fields" in work_kwargs and isinstance(work_kwargs["extra_fields"], dict):
                work_kwargs["extra_fields"].update(extras)
            else:
                work_kwargs["extra_fields"] = extras

        # Ensure defaults so Work model has non-nullable fields and validate normalization
        work_kwargs.setdefault("numero_wr", f"WR-{int(datetime.now().timestamp())}")
        work_kwargs.setdefault("operatore", "unknown")
        work_kwargs.setdefault("indirizzo", "unknown")
        work_kwargs.setdefault("nome_cliente", "unknown")
        work_kwargs.setdefault("tipo_lavoro", "attivazione")
        # If extra_fields exists and isn't a dict, wrap it
        if 'extra_fields' in work_kwargs and not isinstance(work_kwargs['extra_fields'], dict):
            work_kwargs['extra_fields'] = { 'raw': work_kwargs['extra_fields'] }

        # If numero_wr exists in work_kwargs, try to find existing work and update it instead of creating duplicate
        existing = None
        if work_kwargs.get('numero_wr'):
            logging.getLogger('app.routes.works').info(f"upload_work: lookup numero_wr={work_kwargs.get('numero_wr')}")
            print(f"upload_work: lookup numero_wr={work_kwargs.get('numero_wr')}")
            existing = db.query(Work).filter(Work.numero_wr == work_kwargs.get('numero_wr')).first()
        if existing:
            # update existing
            existing.operatore = work_kwargs.get('operatore', existing.operatore)
            existing.indirizzo = work_kwargs.get('indirizzo', existing.indirizzo)
            existing.nome_cliente = work_kwargs.get('nome_cliente', existing.nome_cliente)
            existing.tipo_lavoro = work_kwargs.get('tipo_lavoro', existing.tipo_lavoro)
            if work_kwargs.get('note'):
                existing.note = work_kwargs.get('note')
            if work_kwargs.get('extra_fields'):
                existing.extra_fields = existing.extra_fields or {}
                existing.extra_fields.update(work_kwargs.get('extra_fields'))
            db.commit()
            db.refresh(existing)
            # Add event to indicate update
            event = WorkEvent(work_id=existing.id, timestamp=datetime.now(), event_type="updated", description="Work uploaded and merged", user_id=None)
            db.add(event)
            db.commit()
            return existing
        else:
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
            notify_new_work(work, db)
            return work


@router.post("/", response_model=WorkOut)
def create_work(payload: WorkCreate, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin', 'backoffice']))):
    work_kwargs = payload.dict(exclude_unset=True)
    if work_kwargs.get('numero_wr'):
        work_kwargs['numero_wr'] = normalize_numero_wr(work_kwargs.get('numero_wr'))
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
    notify_new_work(work, db)
    return work

@router.get("/", response_model=List[WorkOut])
def get_works(db: Session = Depends(get_db)):
    works = db.query(Work).all()
    return works


@router.get("/{work_id}", response_model=WorkOut)
def get_work(work_id: int, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

@router.put("/{work_id}/assign/{tech_id}")
def assign_work(work_id: int, tech_id: int, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin', 'backoffice']))):
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
    # Notify technician via telegram if they have a telegram_id
    try:
        if tech and tech.telegram_id:
            msg = f"""🔄 <b>Lavoro riassegnato!</b>

📋 <b>WR:</b> {work.numero_wr}
👤 <b>Cliente:</b> {work.nome_cliente or 'N/D'}
📍 <b>Indirizzo:</b> {work.indirizzo or 'N/D'}
🔧 <b>Tipo:</b> {work.tipo_lavoro or 'N/D'}
📞 <b>Telefono:</b> {work.telefono_cliente or 'N/D'}

💡 <i>Il lavoro è ora in corso</i>"""
            telegram_utils.send_message_to_telegram(tech.telegram_id, msg)
    except Exception as e:
        logging.getLogger('app.routes.works').exception('Failed to notify technician: %s', e)
    return {"message": "Assigned"}


@router.post("/{work_id}/notify")
def notify_work(work_id: int, payload: dict | None = None, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin','backoffice']))):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    if not work.tecnico_assegnato_id:
        raise HTTPException(status_code=400, detail="Work has no assigned technician")
    tech = db.query(Technician).filter(Technician.id == work.tecnico_assegnato_id).first()
    if not tech or not tech.telegram_id:
        raise HTTPException(status_code=400, detail="Assigned technician has no telegram_id")
    text = None
    if payload and payload.get('message'):
        text = payload.get('message')
    else:
        text = f"Ciao {tech.nome or ''}, ti è stato assegnato il lavoro WR {work.numero_wr} - indirizzo: {work.indirizzo or 'N/A'} - Appuntamento: {work.data_apertura or 'N/A'}"
    ok = telegram_utils.send_message_to_telegram(tech.telegram_id, text)
    return { 'ok': ok }

@router.put("/{work_id}/status")
def update_status(work_id: int, payload: WorkStatusUpdate | None = None, db: Session = Depends(get_db), current_user = Depends(auth_required(['admin','backoffice','tecnico']))):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    # Accept a JSON payload with 'stato' property
    if not payload or not payload.stato:
        raise HTTPException(status_code=400, detail="Missing or invalid status payload")
    new_status = payload.stato
    work.stato = new_status
    if new_status == "chiuso":
        work.data_chiusura = datetime.now()
    # Verify technician privileges: if current_user is a user, check their role
    if isinstance(current_user, bool):
        # API key used; allow
        pass
    else:
        # current_user is a User object; check role
        if current_user.role == "tecnico":
            # Ensure they can only update works assigned to them
            if work.tecnico_assegnato_id != current_user.technician_id:
                raise HTTPException(status_code=403, detail="Not allowed to update this work")
    db.commit()
    event = WorkEvent(work_id=work_id, timestamp=datetime.now(), event_type="status_change", description=f"Status to {new_status}", user_id=work.tecnico_assegnato_id)
    db.add(event)
    db.commit()
    return {"message": "Status updated"}

@router.delete("/{work_id}")
def delete_work(work_id: int, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    db.delete(work)
    db.commit()
    return {"message": "Work deleted"}


@router.put("/{work_id}", response_model=WorkOut)
def update_work(work_id: int, payload: WorkUpdate, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    update_data = payload.dict(exclude_unset=True)
    old_status = work.stato
    old_tech = work.tecnico_assegnato_id
    if 'numero_wr' in update_data:
        new_num = normalize_numero_wr(update_data['numero_wr'])
        # check if another work has this numero
        existing = db.query(Work).filter(Work.numero_wr == new_num, Work.id != work_id).first()
        if existing:
            raise HTTPException(status_code=409, detail='numero_wr already exists on another Work')
        work.numero_wr = new_num
    if 'operatore' in update_data:
        work.operatore = update_data['operatore']
    if 'indirizzo' in update_data:
        work.indirizzo = update_data['indirizzo']
    if 'nome_cliente' in update_data:
        work.nome_cliente = update_data['nome_cliente']
    if 'tipo_lavoro' in update_data:
        work.tipo_lavoro = update_data['tipo_lavoro']
    if 'note' in update_data:
        work.note = update_data['note']
    if 'tecnico_assegnato_id' in update_data:
        work.tecnico_assegnato_id = update_data['tecnico_assegnato_id']
    if 'stato' in update_data:
        work.stato = update_data['stato']
        if update_data['stato'] == 'chiuso':
            work.data_chiusura = datetime.now()
    
    # Update equipment fields
    if 'requires_modem' in update_data:
        work.requires_modem = update_data['requires_modem']
    if 'requires_ont' in update_data:
        work.requires_ont = update_data['requires_ont']
    if 'modem_delivered' in update_data:
        work.modem_delivered = update_data['modem_delivered']
    if 'ont_delivered' in update_data:
        work.ont_delivered = update_data['ont_delivered']
    
    db.commit()
    # Create events for meaningful changes
    if 'stato' in update_data and update_data['stato'] != old_status:
        new_status = update_data['stato']
        if new_status == 'chiuso':
            ev_type = 'closed'
        elif new_status == 'sospeso':
            ev_type = 'suspended'
        else:
            ev_type = 'status_change'
        ev = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type=ev_type, description=f'Status to {new_status}', user_id=work.tecnico_assegnato_id)
        db.add(ev)
        db.commit()
    if 'tecnico_assegnato_id' in update_data and update_data['tecnico_assegnato_id'] != old_tech:
        new_tech = update_data['tecnico_assegnato_id']
        if new_tech:
            ev_type = 'assigned'
            desc = f'Assigned to tech {new_tech}'
        else:
            ev_type = 'unassigned'
            desc = 'Unassigned'
        ev = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type=ev_type, description=desc, user_id=new_tech)
        db.add(ev)
        db.commit()
    # Fallback update event for other changes
    event = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type='updated', description=f'Work updated via API', user_id=None)
    db.add(event)
    db.commit()
    db.refresh(work)
    return work

def notify_new_work(work: Work, db: Session):
    try:
        # Only notify assigned technician if present
        if work.tecnico_assegnato_id:
            tech = db.query(Technician).filter(Technician.id == work.tecnico_assegnato_id).first()
            if tech and tech.telegram_id:
                msg = f"""🔧 <b>Nuovo lavoro assegnato!</b>

📋 <b>WR:</b> {work.numero_wr}
👤 <b>Cliente:</b> {work.nome_cliente or 'N/D'}
📍 <b>Indirizzo:</b> {work.indirizzo or 'N/D'}
🔧 <b>Tipo:</b> {work.tipo_lavoro or 'N/D'}
📞 <b>Telefono:</b> {work.telefono_cliente or 'N/D'}
📅 <b>Data apertura:</b> {work.data_apertura.strftime('%d/%m/%Y %H:%M') if work.data_apertura else 'N/D'}

💡 <i>Ricorda di confermare l'accettazione con /accetta {work.numero_wr}</i>"""
                telegram_utils.send_message_to_telegram(tech.telegram_id, msg)
    except Exception as e:
        # Log error but don't fail
        print(f"Notification error: {e}")


@router.post('/merge_duplicates')
def merge_duplicate_works(db: Session = Depends(get_db)):
    """Merge works that have the same normalized numero_wr into a single work.

    This action scans all works, groups by normalize_numero_wr, and merges duplicates.
    The earliest-created work (smallest id) is kept and others merged into it.
    Returns a summary of what was merged.
    """
    works = db.query(Work).all()
    groups: dict[str, list[Work]] = {}
    for w in works:
        norm = normalize_numero_wr(w.numero_wr) or f"__no_wr__{w.id}"
        groups.setdefault(norm, []).append(w)

    merged = []
    for norm, group in groups.items():
        if len(group) <= 1:
            continue
        # sort by id to keep the earliest
        group_sorted = sorted(group, key=lambda x: x.id)
        keeper = group_sorted[0]
        to_merge = group_sorted[1:]
        for dup in to_merge:
            # move documents referencing dup
            docs = db.query(Document).filter(Document.applied_work_id == dup.id).all()
            for d in docs:
                d.applied_work_id = keeper.id
                db.add(d)
            # move association rows in document_applied_works table (bulk update to avoid session stale errors)
            # First, delete any duplicate associations where the document already has an association to the keeper.
            keeper_doc_ids = [d[0] for d in db.query(DocumentAppliedWork.document_id).filter(DocumentAppliedWork.work_id == keeper.id).all()]
            if keeper_doc_ids:
                db.query(DocumentAppliedWork).filter(DocumentAppliedWork.work_id == dup.id, DocumentAppliedWork.document_id.in_(keeper_doc_ids)).delete(synchronize_session=False)
            # Then update remaining associations from dup to keeper
            db.query(DocumentAppliedWork).filter(DocumentAppliedWork.work_id == dup.id).update({DocumentAppliedWork.work_id: keeper.id}, synchronize_session=False)
            # Also update parsed_data.applied_work_ids on related Documents if present
            affected_docs = db.query(Document).filter(Document.parsed_data != None).all()
            for doc in affected_docs:
                try:
                    if doc.parsed_data and isinstance(doc.parsed_data, dict):
                        parsed = dict(doc.parsed_data)
                        if 'applied_work_ids' in parsed and isinstance(parsed['applied_work_ids'], list):
                            parsed['applied_work_ids'] = [keeper.id if x == dup.id else x for x in parsed['applied_work_ids']]
                            # dedupe keeping order
                            parsed['applied_work_ids'] = list(dict.fromkeys(parsed['applied_work_ids']))
                            doc.parsed_data = parsed
                            db.add(doc)
                except Exception:
                    # be defensive; skip doc on error
                    pass
            # move events referencing dup
            events = db.query(WorkEvent).filter(WorkEvent.work_id == dup.id).all()
            for ev in events:
                ev.work_id = keeper.id
                db.add(ev)
            # merge fields: fill missing basic fields
            if not keeper.operatore and dup.operatore:
                keeper.operatore = dup.operatore
            if not keeper.indirizzo and dup.indirizzo:
                keeper.indirizzo = dup.indirizzo
            if not keeper.nome_cliente and dup.nome_cliente:
                keeper.nome_cliente = dup.nome_cliente
            if not keeper.tipo_lavoro and dup.tipo_lavoro:
                keeper.tipo_lavoro = dup.tipo_lavoro
            # merge extra_fields
            keeper.extra_fields = keeper.extra_fields or {}
            if dup.extra_fields:
                keeper.extra_fields.update(dup.extra_fields)
            # prefer closed status if any
            if dup.stato == 'chiuso' and keeper.stato != 'chiuso':
                keeper.stato = 'chiuso'
                keeper.data_chiusura = dup.data_chiusura or datetime.now()
            # delete duplicate work row
            db.delete(dup)
        # add event describing merge
        event = WorkEvent(work_id=keeper.id, timestamp=datetime.now(), event_type='merged', description=f'Merged {len(to_merge)} duplicate works', user_id=None)
        db.add(event)
        db.commit()
        merged.append({'keeper_id': keeper.id, 'merged_count': len(to_merge)})
        # After commits, dedupe any DocumentAppliedWork rows for this document/keeper
        # For each document that references keeper.id multiple times, remove duplicates
        dup_assocs = db.query(DocumentAppliedWork.document_id, DocumentAppliedWork.work_id).filter(DocumentAppliedWork.work_id == keeper.id).group_by(DocumentAppliedWork.document_id, DocumentAppliedWork.work_id).having(func.count(DocumentAppliedWork.id) > 1).all()
        for (doc_id, work_id) in dup_assocs:
            assocs = db.query(DocumentAppliedWork).filter(DocumentAppliedWork.document_id == doc_id, DocumentAppliedWork.work_id == work_id).order_by(DocumentAppliedWork.id.asc()).all()
            # Keep first, delete the rest
            for extra in assocs[1:]:
                db.delete(extra)
        db.commit()
    return {'merged': merged}

# ONT/Modem management endpoints for works

@router.put("/{work_id}/ont/{ont_id}")
def assign_ont_to_work(work_id: int, ont_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Assign ONT to work and update work flags"""
    from app.models.models import ONT
    
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    ont = db.query(ONT).filter(ONT.id == ont_id).first()
    if not ont:
        raise HTTPException(status_code=404, detail="ONT not found")

    if ont.status != "available":
        raise HTTPException(status_code=400, detail="ONT is not available")

    # Assign ONT to work
    work.ont = ont
    work.requires_ont = True
    ont.status = "assigned"
    ont.assigned_date = datetime.utcnow()

    db.commit()
    return {"message": "ONT assigned to work successfully"}

@router.put("/{work_id}/modem/{modem_id}")
def assign_modem_to_work(work_id: int, modem_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Assign modem to work and update work flags"""
    from app.models.models import Modem
    
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    modem = db.query(Modem).filter(Modem.id == modem_id).first()
    if not modem:
        raise HTTPException(status_code=404, detail="Modem not found")

    if modem.status != "available":
        raise HTTPException(status_code=400, detail="Modem is not available")

    # Assign modem to work
    work.modem = modem
    work.requires_modem = True
    modem.status = "assigned"

    db.commit()
    return {"message": "Modem assigned to work successfully"}

@router.get("/{work_id}/equipment")
def get_work_equipment(work_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get equipment (ONT/Modem) assigned to work"""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    equipment = {
        "work_id": work.id,
        "requires_ont": work.requires_ont,
        "requires_modem": work.requires_modem,
        "ont_delivered": work.ont_delivered,
        "modem_delivered": work.modem_delivered,
        "ont_cost": work.ont_cost,
        "modem_cost": work.modem_cost,
        "ont": None,
        "modem": None
    }

    if work.ont:
        equipment["ont"] = {
            "id": work.ont.id,
            "serial_number": work.ont.serial_number,
            "model": work.ont.model,
            "manufacturer": work.ont.manufacturer,
            "status": work.ont.status,
            "pon_port": work.ont.pon_port,
            "vlan_id": work.ont.vlan_id,
            "ip_address": work.ont.ip_address
        }

    if work.modem:
        equipment["modem"] = {
            "id": work.modem.id,
            "serial_number": work.modem.serial_number,
            "model": work.modem.model,
            "manufacturer": work.modem.manufacturer,
            "status": work.modem.status,
            "wifi_ssid": work.modem.wifi_ssid,
            "sync_method": work.modem.sync_method
        }

    return equipment

@router.put("/{work_id}/equipment/delivered")
def mark_equipment_delivered(work_id: int, ont_delivered: bool = False, modem_delivered: bool = False, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Mark equipment as delivered"""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    if ont_delivered:
        work.ont_delivered = True
    if modem_delivered:
        work.modem_delivered = True

    db.commit()
    return {"message": "Equipment delivery status updated"}

class WorkIngest(BaseModel):
    numero_wr: str
    stato: str
    descrizione: Optional[str] = None
    tecnico: Optional[str] = None
    data_creazione: Optional[str] = None
    data_chiusura: Optional[str] = None
    note: Optional[str] = None
    ont_sn: Optional[str] = None
    modem_sn: Optional[str] = None
    indirizzo: Optional[str] = None
    cliente: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class BulkIngestRequest(BaseModel):
    works: List[WorkIngest]

@router.post("/ingest/work")
def ingest_work(work_data: WorkIngest, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Ingest a single work from external system"""
    try:
        # Normalize numero_wr
        numero_wr = normalize_numero_wr(work_data.numero_wr)

        # Check if work already exists
        existing_work = db.query(Work).filter(Work.numero_wr == numero_wr).first()
        if existing_work:
            # Update existing work
            existing_work.stato = work_data.stato
            if work_data.descrizione:
                existing_work.note = work_data.descrizione
            if work_data.tecnico:
                # Find technician by name
                technician = db.query(Technician).filter(
                    (Technician.nome + ' ' + Technician.cognome) == work_data.tecnico
                ).first()
                if technician:
                    existing_work.tecnico_assegnato_id = technician.id
            if work_data.data_creazione:
                existing_work.data_apertura = datetime.fromisoformat(work_data.data_creazione.replace('Z', '+00:00'))
            if work_data.data_chiusura:
                existing_work.data_chiusura = datetime.fromisoformat(work_data.data_chiusura.replace('Z', '+00:00'))
            if work_data.note:
                existing_work.note = work_data.note
            if work_data.indirizzo:
                existing_work.indirizzo = work_data.indirizzo
            if work_data.cliente:
                existing_work.nome_cliente = work_data.cliente

            # Store additional fields in extra_fields
            extra_data = {}
            if work_data.ont_sn:
                extra_data['ont_sn'] = work_data.ont_sn
            if work_data.modem_sn:
                extra_data['modem_sn'] = work_data.modem_sn
            if work_data.telefono:
                extra_data['telefono'] = work_data.telefono
            if work_data.email:
                extra_data['email'] = work_data.email
            if extra_data:
                existing_work.extra_fields = extra_data

            db.commit()
            return {"message": f"Work {numero_wr} updated successfully", "work_id": existing_work.id}
        else:
            # Create new work
            new_work = Work(
                numero_wr=numero_wr,
                stato=work_data.stato,
                operatore="Imported",  # Default operator for imported works
                indirizzo=work_data.indirizzo,
                nome_cliente=work_data.cliente,
                note=work_data.descrizione or work_data.note,
                data_apertura=datetime.fromisoformat(work_data.data_creazione.replace('Z', '+00:00')) if work_data.data_creazione else datetime.utcnow(),
                data_chiusura=datetime.fromisoformat(work_data.data_chiusura.replace('Z', '+00:00')) if work_data.data_chiusura else None
            )

            # Set technician if provided
            if work_data.tecnico:
                technician = db.query(Technician).filter(
                    (Technician.nome + ' ' + Technician.cognome) == work_data.tecnico
                ).first()
                if technician:
                    new_work.tecnico_assegnato_id = technician.id

            # Store additional fields in extra_fields
            extra_data = {}
            if work_data.ont_sn:
                extra_data['ont_sn'] = work_data.ont_sn
            if work_data.modem_sn:
                extra_data['modem_sn'] = work_data.modem_sn
            if work_data.telefono:
                extra_data['telefono'] = work_data.telefono
            if work_data.email:
                extra_data['email'] = work_data.email
            if extra_data:
                new_work.extra_fields = extra_data

            db.add(new_work)
            db.commit()
            db.refresh(new_work)

            # Log the creation event
            event = WorkEvent(
                work_id=new_work.id,
                event_type="created",
                description=f"Work {numero_wr} created via API ingest",
                timestamp=datetime.utcnow()
            )
            db.add(event)
            db.commit()

            return {"message": f"Work {numero_wr} created successfully", "work_id": new_work.id}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate work number or constraint violation")
    except Exception as e:
        db.rollback()
        logging.error(f"Error ingesting work: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting work: {str(e)}")

@router.post("/ingest/bulk")
def ingest_bulk_works(request: BulkIngestRequest, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Ingest multiple works from external system"""
    results = []
    errors = []

    for i, work_data in enumerate(request.works):
        try:
            # Normalize numero_wr
            numero_wr = normalize_numero_wr(work_data.numero_wr)

            # Check if work already exists
            existing_work = db.query(Work).filter(Work.numero_wr == numero_wr).first()
            if existing_work:
                # Update existing work
                existing_work.stato = work_data.stato
                if work_data.descrizione:
                    existing_work.note = work_data.descrizione
                if work_data.tecnico:
                    # Find technician by name
                    technician = db.query(Technician).filter(
                        (Technician.nome + ' ' + Technician.cognome) == work_data.tecnico
                    ).first()
                    if technician:
                        existing_work.tecnico_assegnato_id = technician.id
                if work_data.data_creazione:
                    existing_work.data_apertura = datetime.fromisoformat(work_data.data_creazione.replace('Z', '+00:00'))
                if work_data.data_chiusura:
                    existing_work.data_chiusura = datetime.fromisoformat(work_data.data_chiusura.replace('Z', '+00:00'))
                if work_data.note:
                    existing_work.note = work_data.note
                if work_data.indirizzo:
                    existing_work.indirizzo = work_data.indirizzo
                if work_data.cliente:
                    existing_work.nome_cliente = work_data.cliente

                # Store additional fields in extra_fields
                extra_data = {}
                if work_data.ont_sn:
                    extra_data['ont_sn'] = work_data.ont_sn
                if work_data.modem_sn:
                    extra_data['modem_sn'] = work_data.modem_sn
                if work_data.telefono:
                    extra_data['telefono'] = work_data.telefono
                if work_data.email:
                    extra_data['email'] = work_data.email
                if extra_data:
                    existing_work.extra_fields = extra_data

                db.commit()
                results.append({"index": i, "numero_wr": numero_wr, "status": "updated", "work_id": existing_work.id})
            else:
                # Create new work
                new_work = Work(
                    numero_wr=numero_wr,
                    stato=work_data.stato,
                    operatore="Imported",  # Default operator for imported works
                    indirizzo=work_data.indirizzo,
                    nome_cliente=work_data.cliente,
                    note=work_data.descrizione or work_data.note,
                    data_apertura=datetime.fromisoformat(work_data.data_creazione.replace('Z', '+00:00')) if work_data.data_creazione else datetime.utcnow(),
                    data_chiusura=datetime.fromisoformat(work_data.data_chiusura.replace('Z', '+00:00')) if work_data.data_chiusura else None
                )
                db.add(new_work)
                db.commit()
                db.refresh(new_work)

                # Log the creation event
                event = WorkEvent(
                    work_id=new_work.id,
                    event_type="created",
                    description=f"Work {numero_wr} created via bulk API ingest",
                    timestamp=datetime.utcnow()
                )
                db.add(event)
                db.commit()

                results.append({"index": i, "numero_wr": numero_wr, "status": "created", "work_id": new_work.id})

        except Exception as e:
            db.rollback()
            error_msg = f"Error processing work at index {i} ({work_data.numero_wr}): {str(e)}"
            errors.append(error_msg)
            logging.error(error_msg)

    return {
        "message": f"Processed {len(request.works)} works",
        "results": results,
        "errors": errors,
        "success_count": len(results),
        "error_count": len(errors)
    }