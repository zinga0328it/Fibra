from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import func
from app.models.models import Work
from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["stats"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/weekly")
def get_weekly_stats(db: Session = Depends(get_db)):
    week_ago = datetime.now() - timedelta(days=7)
    closed = db.query(func.count(Work.id)).filter(Work.stato == "chiuso", Work.data_chiusura >= week_ago).scalar()
    suspended = db.query(func.count(Work.id)).filter(Work.stato == "sospeso").scalar()
    return {"closed_this_week": closed, "suspended": suspended}

# Add more stats as needed