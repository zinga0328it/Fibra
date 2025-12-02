from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Team
from typing import List
from app.utils.security import verify_api_key
from app.schemas import TeamCreate, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[TeamOut])
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return teams

@router.post("/", response_model=TeamOut)
def create_team(payload: TeamCreate, db: Session = Depends(get_db), api_key=Depends(verify_api_key)):
    team = Team(nome=payload.nome)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team