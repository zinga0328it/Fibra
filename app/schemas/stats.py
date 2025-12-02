"""
Statistics schemas for API response validation.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class DailyStats(BaseModel):
    """Daily work statistics."""
    
    date: date
    total_works: int = Field(0, description="Total work orders")
    completed: int = Field(0, description="Completed work orders")
    pending: int = Field(0, description="Pending work orders")
    in_progress: int = Field(0, description="Work orders in progress")
    refused: int = Field(0, description="Refused work orders")


class OperatorStats(BaseModel):
    """Statistics per telecom operator."""
    
    operator: str
    total_works: int = Field(0, description="Total work orders")
    completed: int = Field(0, description="Completed work orders")
    completion_rate: float = Field(0.0, description="Completion rate percentage")
    average_completion_time: Optional[float] = Field(
        None, description="Average completion time in hours"
    )


class TechnicianStats(BaseModel):
    """Statistics per technician."""
    
    technician_id: int
    technician_name: str
    total_works: int = Field(0, description="Total assigned work orders")
    completed: int = Field(0, description="Completed work orders")
    in_progress: int = Field(0, description="Work orders in progress")
    completion_rate: float = Field(0.0, description="Completion rate percentage")
    average_completion_time: Optional[float] = Field(
        None, description="Average completion time in hours"
    )


class TeamStats(BaseModel):
    """Statistics per team."""
    
    team_id: int
    team_name: str
    total_technicians: int = Field(0, description="Number of technicians")
    total_works: int = Field(0, description="Total work orders")
    completed: int = Field(0, description="Completed work orders")
    completion_rate: float = Field(0.0, description="Completion rate percentage")


class StatsResponse(BaseModel):
    """Complete statistics response."""
    
    daily_stats: list[DailyStats] = Field(default_factory=list)
    operator_stats: list[OperatorStats] = Field(default_factory=list)
    technician_stats: list[TechnicianStats] = Field(default_factory=list)
    team_stats: list[TeamStats] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
