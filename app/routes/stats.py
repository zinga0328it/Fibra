from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import func
from app.models.models import Work, Technician
from app.schemas import StatsWeeklyOut, OperatorStatOut, TechnicianStatOut, DailyClosedOut
from datetime import datetime, timedelta
from calendar import monthrange
from app.database import engine

router = APIRouter(prefix="/stats", tags=["stats"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/weekly", response_model=StatsWeeklyOut)
def get_weekly_stats(db: Session = Depends(get_db)):
    week_ago = datetime.now() - timedelta(days=7)
    closed = db.query(func.count(Work.id)).filter(Work.stato == "chiuso", Work.data_chiusura >= week_ago).scalar()
    suspended = db.query(func.count(Work.id)).filter(Work.stato == "sospeso").scalar()
    return {"closed_this_week": closed, "suspended": suspended}


@router.get("/closed_by_operator", response_model=list[OperatorStatOut])
def closed_by_operator(db: Session = Depends(get_db)):
    results = db.query(Work.operatore, func.count(Work.id).label("closed")).filter(Work.stato == "chiuso").group_by(Work.operatore).all()
    return [{"operatore": r[0] or "Unknown", "closed": r[1]} for r in results]


@router.get("/closed_by_technician", response_model=list[TechnicianStatOut])
def closed_by_technician(db: Session = Depends(get_db)):
    results = db.query(Technician.nome, Technician.cognome, func.count(Work.id).label("closed")).join(Work, Work.tecnico_assegnato_id == Technician.id).filter(Work.stato == "chiuso").group_by(Technician.id).all()
    return [{"tecnico": f"{r[0]} {r[1]}", "closed": r[2]} for r in results]


@router.get("/daily_closed", response_model=list[DailyClosedOut])
def daily_closed(db: Session = Depends(get_db)):
    results = db.query(func.date(Work.data_chiusura), func.count(Work.id).label("closed")).filter(Work.stato == "chiuso").group_by(func.date(Work.data_chiusura)).all()
    return [{"date": r[0] or "", "closed": r[1]} for r in results]


@router.get('/yearly', response_model=list[DailyClosedOut])
def yearly_closed(db: Session = Depends(get_db)):
    """Return closed counts grouped by month for the last 12 months."""
    now = datetime.now()
    start = (now.replace(day=1) - timedelta(days=365)).replace(day=1)
    # SQLite vs Postgres formatting
    month_format = None
    if engine.dialect.name == 'sqlite':
        month_format = func.strftime('%Y-%m', Work.data_chiusura)
    else:
        # Postgres fallback
        month_format = func.to_char(Work.data_chiusura, 'YYYY-MM')
    results = db.query(month_format.label('month'), func.count(Work.id).label('closed')).filter(Work.stato == 'chiuso', Work.data_chiusura != None, Work.data_chiusura >= start).group_by('month').all()
    # Convert list of tuples to dict for quick lookup
    data_map = { r[0]: r[1] for r in results }
    # Generate last 12 months labels
    months = []
    cursor = start
    for i in range(0, 12):
        months.append(cursor.strftime('%Y-%m'))
        # increment month
        year = cursor.year + (cursor.month // 12)
        month = (cursor.month % 12) + 1
        cursor = cursor.replace(year=year, month=month)
    out = []
    for m in months:
        out.append({"date": m, "closed": data_map.get(m, 0)})
    return out

@router.get("/equipment")
def get_equipment_stats(db: Session = Depends(get_db)):
    """Get ONT and Modem statistics"""
    from app.models.models import ONT, Modem
    
    ont_stats = {
        "total": db.query(func.count(ONT.id)).scalar(),
        "available": db.query(func.count(ONT.id)).filter(ONT.status == "available").scalar(),
        "assigned": db.query(func.count(ONT.id)).filter(ONT.status == "assigned").scalar(),
        "installed": db.query(func.count(ONT.id)).filter(ONT.status == "installed").scalar(),
        "faulty": db.query(func.count(ONT.id)).filter(ONT.status == "faulty").scalar()
    }
    
    modem_stats = {
        "total": db.query(func.count(Modem.id)).scalar(),
        "available": db.query(func.count(Modem.id)).filter(Modem.status == "available").scalar(),
        "assigned": db.query(func.count(Modem.id)).filter(Modem.status == "assigned").scalar(),
        "configured": db.query(func.count(Modem.id)).filter(Modem.status == "configured").scalar(),
        "installed": db.query(func.count(Modem.id)).filter(Modem.status == "installed").scalar()
    }
    
    # Monthly installations
    now = datetime.now()
    start = (now.replace(day=1) - timedelta(days=365)).replace(day=1)
    
    month_format = None
    if engine.dialect.name == 'sqlite':
        month_format = func.strftime('%Y-%m', ONT.installed_at)
    else:
        month_format = func.to_char(ONT.installed_at, 'YYYY-MM')
    
    ont_installations = db.query(month_format.label('month'), func.count(ONT.id).label('installed')).filter(ONT.installed_at != None, ONT.installed_at >= start).group_by('month').all()
    ont_install_map = {r[0]: r[1] for r in ont_installations}
    
    if engine.dialect.name == 'sqlite':
        month_format = func.strftime('%Y-%m', Modem.installed_at)
    else:
        month_format = func.to_char(Modem.installed_at, 'YYYY-MM')
    
    modem_installations = db.query(month_format.label('month'), func.count(Modem.id).label('installed')).filter(Modem.installed_at != None, Modem.installed_at >= start).group_by('month').all()
    modem_install_map = {r[0]: r[1] for r in modem_installations}
    
    return {
        "ont": ont_stats,
        "modem": modem_stats,
        "monthly_ont_installations": ont_install_map,
        "monthly_modem_installations": modem_install_map
    }

@router.get("/installations")
def get_installation_stats(db: Session = Depends(get_db)):
    """Get installation statistics with sync information"""
    from app.models.models import ONTModemSync
    
    total_syncs = db.query(func.count(ONTModemSync.id)).scalar()
    completed_syncs = db.query(func.count(ONTModemSync.id)).filter(ONTModemSync.sync_status == "completed").scalar()
    failed_syncs = db.query(func.count(ONTModemSync.id)).filter(ONTModemSync.sync_status == "failed").scalar()
    
    # Sync methods distribution
    sync_methods = db.query(ONTModemSync.sync_method, func.count(ONTModemSync.id)).group_by(ONTModemSync.sync_method).all()
    sync_method_stats = {method: count for method, count in sync_methods}
    
    return {
        "total_syncs": total_syncs,
        "completed_syncs": completed_syncs,
        "failed_syncs": failed_syncs,
        "success_rate": (completed_syncs / total_syncs * 100) if total_syncs > 0 else 0,
        "sync_methods": sync_method_stats
    }