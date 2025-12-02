"""
Statistics API router for Gestionale Fibra.

Provides endpoints for aggregated statistics.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.schemas.stats import (
    DailyStats,
    OperatorStats,
    StatsResponse,
    TeamStats,
    TechnicianStats,
)
from app.security import get_api_key_header
from app.services.stats import stats_service

router = APIRouter(
    prefix="/api/stats",
    tags=["statistics"],
    dependencies=[Depends(get_api_key_header)],
)


@router.get("", response_model=StatsResponse)
async def get_statistics(
    start_date: Optional[date] = Query(None, description="Start date for statistics period"),
    end_date: Optional[date] = Query(None, description="End date for statistics period"),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    """
    Get complete statistics for all categories.
    
    Args:
        start_date: Optional start date for the period
        end_date: Optional end date for the period
        db: Database session
        
    Returns:
        StatsResponse: Complete statistics
    """
    return await stats_service.get_full_stats(db, start_date, end_date)


@router.get("/daily", response_model=list[DailyStats])
async def get_daily_statistics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
) -> list[DailyStats]:
    """
    Get daily work statistics.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        
    Returns:
        list[DailyStats]: Daily statistics
    """
    return await stats_service.get_daily_stats(db, start_date, end_date)


@router.get("/operators", response_model=list[OperatorStats])
async def get_operator_statistics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
) -> list[OperatorStats]:
    """
    Get statistics grouped by telecom operator.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        
    Returns:
        list[OperatorStats]: Operator statistics
    """
    return await stats_service.get_operator_stats(db, start_date, end_date)


@router.get("/technicians", response_model=list[TechnicianStats])
async def get_technician_statistics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
) -> list[TechnicianStats]:
    """
    Get statistics grouped by technician.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        
    Returns:
        list[TechnicianStats]: Technician statistics
    """
    return await stats_service.get_technician_stats(db, start_date, end_date)


@router.get("/teams", response_model=list[TeamStats])
async def get_team_statistics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
) -> list[TeamStats]:
    """
    Get statistics grouped by team.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        
    Returns:
        list[TeamStats]: Team statistics
    """
    return await stats_service.get_team_stats(db, start_date, end_date)
