from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Job, Technician, Team, JobStatus
from app.schemas import StatisticsResponse, DailyStats, OperatorStats, TeamStats

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/", response_model=StatisticsResponse)
def get_statistics(days: int = 30, db: Session = Depends(get_db)):
    """Get comprehensive statistics about jobs."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Total jobs by status
    total_jobs = db.query(Job).count()
    open_jobs = db.query(Job).filter(Job.status == JobStatus.OPEN).count()
    in_progress_jobs = db.query(Job).filter(Job.status == JobStatus.IN_PROGRESS).count()
    paused_jobs = db.query(Job).filter(Job.status == JobStatus.PAUSED).count()
    closed_jobs = db.query(Job).filter(Job.status == JobStatus.CLOSED).count()
    
    # Jobs per day (last N days)
    jobs_per_day = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = db.query(Job).filter(
            Job.created_at >= day_start,
            Job.created_at < day_end
        ).count()
        jobs_per_day.append(DailyStats(
            date=day_start.strftime("%Y-%m-%d"),
            count=count
        ))
    
    # Jobs per operator
    jobs_per_operator = []
    operator_stats = db.query(
        Technician.id,
        Technician.name,
        Technician.surname,
        func.count(Job.id).label("job_count")
    ).outerjoin(Job, Job.technician_id == Technician.id).group_by(
        Technician.id, Technician.name, Technician.surname
    ).all()
    
    for stat in operator_stats:
        jobs_per_operator.append(OperatorStats(
            technician_id=stat.id,
            technician_name=f"{stat.name} {stat.surname}",
            job_count=stat.job_count
        ))
    
    # Jobs per team
    jobs_per_team = []
    team_stats = db.query(
        Team.id,
        Team.name,
        func.count(Job.id).label("job_count")
    ).outerjoin(Technician, Technician.team_id == Team.id).outerjoin(
        Job, Job.technician_id == Technician.id
    ).group_by(Team.id, Team.name).all()
    
    for stat in team_stats:
        jobs_per_team.append(TeamStats(
            team_id=stat.id,
            team_name=stat.name,
            job_count=stat.job_count
        ))
    
    return StatisticsResponse(
        jobs_per_day=jobs_per_day,
        jobs_per_operator=jobs_per_operator,
        jobs_per_team=jobs_per_team,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        in_progress_jobs=in_progress_jobs,
        paused_jobs=paused_jobs,
        closed_jobs=closed_jobs
    )
