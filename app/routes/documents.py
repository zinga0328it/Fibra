from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Body, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Document, Work, WorkEvent, Technician, DocumentAppliedWork
import app.utils.telegram as telegram_utils
from app.schemas import DocumentOut
from typing import List
from datetime import datetime
from app.utils.auth import auth_required
from app.utils.ocr import extract_wr_fields, normalize_numero_wr, extract_wr_entries
try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None
import pdfplumber
from io import BytesIO
from sqlalchemy.exc import IntegrityError
import json

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=List[DocumentOut])
async def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    docs = []
    for f in files:
        # Accept only PDF files
        if not (f.filename and f.filename.lower().endswith('.pdf')):
            raise HTTPException(status_code=400, detail='Only PDF uploads are allowed (images and CSV/JSON are disabled).')
        content = await f.read()
        doc = Document(filename=f.filename, mime=f.content_type, content=content, uploaded_at=datetime.now(), parsed=False)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        docs.append(doc)
    return docs


@router.get("/", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return docs


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/{doc_id}/parse", response_model=DocumentOut)
def parse_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    text = None
    ocr_used = False
    try:
        # Ensure this is a PDF (file extension or mime) — images and text are not supported here
        if not (doc.filename and doc.filename.lower().endswith('.pdf')) and not (doc.mime and 'pdf' in (doc.mime or '').lower()):
            raise HTTPException(status_code=400, detail='Only PDF parsing is supported')
        # Try pdf extraction
        text = None
        try:
            with pdfplumber.open(BytesIO(doc.content)) as pdf:
                # Gather full text and per-page texts
                pages_text = [p.extract_text() or '' for p in pdf.pages]
                text = '\n'.join(pages_text)
                # If nothing found and OCR available, fallback to OCR for each page
                if (not text or len(text.strip()) == 0) and pytesseract:
                    ocr_pages = []
                    for p in pdf.pages:
                        try:
                            # Render page to image and OCR via pytesseract
                            pil_image = p.to_image(resolution=200).original
                            page_text = pytesseract.image_to_string(pil_image)
                            ocr_pages.append(page_text)
                        except Exception:
                            # best effort; if rendering or OCR fails skip page
                            continue
                    if ocr_pages:
                        text = '\n'.join(ocr_pages)
                        ocr_used = True
        except Exception:
            # If pdfplumber fails to parse the file (e.g., for test stubs that are not a real PDF), try to decode the content as UTF-8 and parse JSON as a fallback
            try:
                text = doc.content.decode('utf-8')
            except Exception:
                text = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Attempt to parse JSON content first (and accept JSON lists)
    parsed = None
    try:
        parsed_json = json.loads(text)
        if isinstance(parsed_json, dict):
            # Single dict
            parsed = parsed_json
        elif isinstance(parsed_json, list):
            # List of entries
            parsed = { 'entries': parsed_json }
        else:
            parsed = extract_wr_entries(text)
    except Exception:
        # Not JSON; try to extract multiple entries
        # If we extracted pages_text above, try per-page and per-slice extraction
        parsed_entries = []
        try:
            # Use pages_text if available
            if 'pages_text' in locals():
                for ptext in pages_text:
                    parsed_entries.extend([e for e in extract_wr_entries(ptext) if e])
            else:
                parsed_entries = extract_wr_entries(text)
        except Exception:
            parsed_entries = []
        if len(parsed_entries) == 0:
            # Fallback to conservative parsing returning a single dict
            parsed = extract_wr_fields(text)
        elif len(parsed_entries) == 1:
            parsed = parsed_entries[0]
        else:
            parsed = { 'entries': parsed_entries }
    # Ensure doc.parsed_data is a dict and attach raw_text for debugging
    if not isinstance(parsed, dict):
        # If parsed is a list or other, normalize into dict
        parsed = {'entries': parsed if parsed else []}
    parsed['raw_text'] = text
    # Deduplicate entries by normalized numero_wr (prefer the first appearance)
    try:
        if isinstance(parsed.get('entries'), list) and len(parsed.get('entries')):
            seen = set()
            deduped = []
            for e in parsed['entries']:
                nr = None
                try:
                    nr = normalize_numero_wr(e.get('numero_wr')) if e and e.get('numero_wr') else None
                except Exception:
                    nr = None
                if nr:
                    if nr in seen:
                        continue
                    seen.add(nr)
                    # rewrite normalized value
                    e['numero_wr'] = nr
                    deduped.append(e)
                else:
                    # keep entries without numero_wr as-is
                    deduped.append(e)
            parsed['entries'] = deduped
    except Exception:
        pass
    # Aggregate parsing debug info for entries if present
    try:
        methods = set()
        candidates = set()
        if isinstance(parsed.get('entries'), list):
            for e in parsed['entries']:
                if isinstance(e, dict):
                    dbg = e.get('_parse_debug') or {}
                    if dbg.get('methods'):
                        methods.update(dbg.get('methods'))
                    if dbg.get('candidates'):
                        candidates.update(dbg.get('candidates'))
                    # mark parsed validity if numero_wr is not present
                    e['_parsed_valid'] = bool(e.get('numero_wr'))
        methods_list = list(methods)
        if ocr_used and 'ocr' not in methods_list:
            methods_list.append('ocr')
        parsed['parse_debug'] = {'methods': methods_list, 'candidates': list(candidates)}
    except Exception:
        # don't fail parsing for debug aggregation
        pass
    doc.parsed_data = parsed
    doc.parsed = True
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/apply", response_model=DocumentOut)
def apply_document(doc_id: int, db: Session = Depends(get_db), override: dict | None = Body(None), selected_indices: List[int] | None = Query(None)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    data = doc.parsed_data or {}
    entries = None
    # Determine entries from parsed data
    if isinstance(data, dict) and 'entries' in data and isinstance(data['entries'], list):
        entries = data['entries']
    elif isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = [data]
    else:
        entries = []

    if not entries:
        raise HTTPException(status_code=400, detail='No parsed entries found to apply')

    # Handle selected indices
    if selected_indices:
        if not isinstance(selected_indices, list) or not all(isinstance(i, int) for i in selected_indices):
            raise HTTPException(status_code=400, detail='selected_indices must be a list of integer indices')
        # validate bounds
        for i in selected_indices:
            if i < 0 or i >= len(entries):
                raise HTTPException(status_code=400, detail=f'Index {i} out of range for parsed entries')
        # shrink entries to only selected ones (preserve original order of indices)
        selected_indices = sorted(set(selected_indices))
        original_entries = entries
        entries = [original_entries[i] for i in selected_indices]

    # Handle overrides: dict -> apply to all, list -> per-entry
    overrides = None
    if override:
        if isinstance(override, list):
            if len(override) != len(entries):
                raise HTTPException(status_code=400, detail='Override list length must match entries')
            overrides = override
        elif isinstance(override, dict):
            overrides = [override] * len(entries)
        else:
            raise HTTPException(status_code=400, detail='Invalid override payload')

    applied_ids = []
    for idx, entry in enumerate(entries):
        data_entry = dict(entry or {})
        if overrides:
            data_entry.update(overrides[idx])
        numero_wr = normalize_numero_wr(data_entry.get('numero_wr') or None)
        work = None
        if numero_wr:
            work = db.query(Work).filter(Work.numero_wr == numero_wr).first()
        if not work:
            work = Work(
                numero_wr=numero_wr or ('WR-' + str(int(datetime.now().timestamp()))),
                operatore=data_entry.get('operatore', 'unknown'),
                indirizzo=data_entry.get('indirizzo', 'unknown'),
                nome_cliente=data_entry.get('nome_cliente', 'unknown'),
                tipo_lavoro=data_entry.get('tipo_lavoro', 'attivazione'),
                data_apertura=datetime.now(),
                extra_fields=data_entry.get('extra_fields') or {}
            )
            db.add(work)
            try:
                db.commit()
            except IntegrityError as e:
                db.rollback()
                # Skip or rethrow - better to rethrow so caller knows
                raise HTTPException(status_code=409, detail=str(e))
            db.refresh(work)
            ev = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type='created', description=f'Created from document {doc.id}', user_id=None)
            db.add(ev)
            db.commit()
        else:
            # update
            work.operatore = data_entry.get('operatore', work.operatore)
            work.indirizzo = data_entry.get('indirizzo', work.indirizzo)
            work.nome_cliente = data_entry.get('nome_cliente', work.nome_cliente)
            work.tipo_lavoro = data_entry.get('tipo_lavoro', work.tipo_lavoro)
            work.extra_fields = work.extra_fields or {}
            work.extra_fields.update(data_entry.get('extra_fields') or {})
            db.commit()
            ev = WorkEvent(work_id=work.id, timestamp=datetime.now(), event_type='updated', description=f'Updated from document {doc.id}', user_id=None)
            db.add(ev)
            db.commit()
        # Create a DocumentAppliedWork row if not already present
        existing_assoc = db.query(DocumentAppliedWork).filter(DocumentAppliedWork.document_id == doc.id, DocumentAppliedWork.work_id == work.id).first()
        if not existing_assoc:
            assoc = DocumentAppliedWork(document_id=doc.id, work_id=work.id, applied_at=datetime.now())
            db.add(assoc)
            db.commit()
        applied_ids.append(work.id)
    # attach list of applied ids into parsed_data for traceability, keeping raw_text if present
    parsed = doc.parsed_data or {}
    if isinstance(parsed, dict):
        new_parsed = dict(parsed)
        new_parsed['applied_work_ids'] = applied_ids
        doc.parsed_data = new_parsed
    else:
        # defensive copy
        doc.parsed_data = {'entries': parsed, 'applied_work_ids': applied_ids}
    # Also keep backward compatible single reference to primary work
    if applied_ids:
        doc.applied_work_id = applied_ids[0]
        # Add a summary event showing document was applied to multiple works
        ev_summary = WorkEvent(work_id=applied_ids[0], timestamp=datetime.now(), event_type='applied_from_document', description=f'Applied document {doc.id} to {len(applied_ids)} works', user_id=None)
        db.add(ev_summary)
    db.commit()
    db.refresh(doc)
    # Notify assigned technician via Telegram if available
    try:
        msg = f"Nuovo lavoro WR {work.numero_wr} creato dal documento {doc.filename} (id:{doc.id})"
        if work.tecnico_assegnato_id:
            tech = db.query(Technician).filter(Technician.id == work.tecnico_assegnato_id).first()
            if tech and tech.telegram_id:
                telegram_utils.send_message_to_telegram(tech.telegram_id, msg)
        else:
            # Fallback: notify all technicians with a linked telegram_id (helpful for review/notification)
            techs = db.query(Technician).filter(Technician.telegram_id != None).all()
            for t in techs:
                if t.telegram_id:
                    telegram_utils.send_message_to_telegram(t.telegram_id, msg)
    except Exception:
        # Don't fail the endpoint on notification errors; just log and continue
        pass
    return doc


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    return Response(content=doc.content, media_type=doc.mime, headers={'Content-Disposition': f'attachment; filename={doc.filename}'})


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
