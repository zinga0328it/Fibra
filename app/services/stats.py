"""
Statistics service for Gestionale Fibra.

Provides aggregated statistics for works, technicians, teams, and operators.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technician import Technician
from app.models.team import Team
from app.models.work import Work, WorkStatus
from app.schemas.stats import (
    DailyStats,
    OperatorStats,
    StatsResponse,
    TeamStats,
    TechnicianStats,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class StatsService:
    """
    Service for calculating and aggregating statistics.
    
    Provides methods for daily, operator, technician, and team statistics.
    """
    
    async def get_daily_stats(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[DailyStats]:
        """
        Get daily work statistics.
        
        Args:
            db: Database session
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            list[DailyStats]: Daily statistics
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Query works grouped by scheduled date
        query = (
            select(
                Work.scheduled_date,
                func.count(Work.id).label("total"),
                func.sum(
                    func.cast(Work.status == WorkStatus.COMPLETED, type_=int)
                ).label("completed"),
                func.sum(
                    func.cast(Work.status == WorkStatus.PENDING, type_=int)
                ).label("pending"),
                func.sum(
                    func.cast(Work.status == WorkStatus.IN_PROGRESS, type_=int)
                ).label("in_progress"),
                func.sum(
                    func.cast(Work.status == WorkStatus.REFUSED, type_=int)
                ).label("refused"),
            )
            .where(Work.scheduled_date >= start_date)
            .where(Work.scheduled_date <= end_date)
            .group_by(Work.scheduled_date)
            .order_by(Work.scheduled_date)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            DailyStats(
                date=row.scheduled_date,
                total_works=row.total or 0,
                completed=row.completed or 0,
                pending=row.pending or 0,
                in_progress=row.in_progress or 0,
                refused=row.refused or 0,
            )
            for row in rows
            if row.scheduled_date is not None
        ]
    
    async def get_operator_stats(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[OperatorStats]:
        """
        Get statistics grouped by telecom operator.
        
        Args:
            db: Database session
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            list[OperatorStats]: Operator statistics
        """
        query = (
            select(
                Work.operator,
                func.count(Work.id).label("total"),
                func.sum(
                    func.cast(Work.status == WorkStatus.COMPLETED, type_=int)
                ).label("completed"),
            )
            .group_by(Work.operator)
            .order_by(func.count(Work.id).desc())
        )
        
        if start_date:
            query = query.where(Work.scheduled_date >= start_date)
        if end_date:
            query = query.where(Work.scheduled_date <= end_date)
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            OperatorStats(
                operator=row.operator,
                total_works=row.total or 0,
                completed=row.completed or 0,
                completion_rate=(
                    (row.completed / row.total * 100) if row.total > 0 else 0.0
                ),
            )
            for row in rows
        ]
    
    async def get_technician_stats(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[TechnicianStats]:
        """
        Get statistics grouped by technician.
        
        Args:
            db: Database session
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            list[TechnicianStats]: Technician statistics
        """
        query = (
            select(
                Technician.id,
                Technician.name,
                func.count(Work.id).label("total"),
                func.sum(
                    func.cast(Work.status == WorkStatus.COMPLETED, type_=int)
                ).label("completed"),
                func.sum(
                    func.cast(Work.status == WorkStatus.IN_PROGRESS, type_=int)
                ).label("in_progress"),
            )
            .join(Work, Work.technician_id == Technician.id, isouter=True)
            .group_by(Technician.id, Technician.name)
            .order_by(func.count(Work.id).desc())
        )
        
        if start_date:
            query = query.where(Work.scheduled_date >= start_date)
        if end_date:
            query = query.where(Work.scheduled_date <= end_date)
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            TechnicianStats(
                technician_id=row.id,
                technician_name=row.name,
                total_works=row.total or 0,
                completed=row.completed or 0,
                in_progress=row.in_progress or 0,
                completion_rate=(
                    (row.completed / row.total * 100) if row.total and row.total > 0 else 0.0
                ),
            )
            for row in rows
        ]
    
    async def get_team_stats(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[TeamStats]:
        """
        Get statistics grouped by team.
        
        Args:
            db: Database session
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            list[TeamStats]: Team statistics
        """
        # First get technician count per team
        tech_count_query = (
            select(
                Team.id,
                Team.name,
                func.count(Technician.id).label("tech_count"),
            )
            .join(Technician, Technician.team_id == Team.id, isouter=True)
            .group_by(Team.id, Team.name)
        )
        
        tech_result = await db.execute(tech_count_query)
        tech_counts = {row.id: (row.name, row.tech_count or 0) for row in tech_result.all()}
        
        # Now get work stats per team
        work_query = (
            select(
                Team.id,
                func.count(Work.id).label("total"),
                func.sum(
                    func.cast(Work.status == WorkStatus.COMPLETED, type_=int)
                ).label("completed"),
            )
            .join(Technician, Technician.team_id == Team.id)
            .join(Work, Work.technician_id == Technician.id, isouter=True)
            .group_by(Team.id)
        )
        
        if start_date:
            work_query = work_query.where(Work.scheduled_date >= start_date)
        if end_date:
            work_query = work_query.where(Work.scheduled_date <= end_date)
        
        work_result = await db.execute(work_query)
        work_stats = {row.id: (row.total or 0, row.completed or 0) for row in work_result.all()}
        
        return [
            TeamStats(
                team_id=team_id,
                team_name=tech_counts[team_id][0],
                total_technicians=tech_counts[team_id][1],
                total_works=work_stats.get(team_id, (0, 0))[0],
                completed=work_stats.get(team_id, (0, 0))[1],
                completion_rate=(
                    (work_stats.get(team_id, (0, 0))[1] / work_stats.get(team_id, (1, 0))[0] * 100)
                    if work_stats.get(team_id, (0, 0))[0] > 0
                    else 0.0
                ),
            )
            for team_id in tech_counts
        ]
    
    async def get_full_stats(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> StatsResponse:
        """
        Get complete statistics response.
        
        Args:
            db: Database session
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            StatsResponse: Complete statistics
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        daily = await self.get_daily_stats(db, start_date, end_date)
        operators = await self.get_operator_stats(db, start_date, end_date)
        technicians = await self.get_technician_stats(db, start_date, end_date)
        teams = await self.get_team_stats(db, start_date, end_date)
        
        return StatsResponse(
            daily_stats=daily,
            operator_stats=operators,
            technician_stats=technicians,
            team_stats=teams,
            period_start=start_date,
            period_end=end_date,
        )


# Singleton instance
stats_service = StatsService()
