"""
Pydantic schemas package for Gestionale Fibra.

Contains request/response schemas for all API endpoints.
"""

from app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate,
    TechnicianResponse,
    TechnicianListResponse,
)
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
)
from app.schemas.work import (
    WorkCreate,
    WorkUpdate,
    WorkResponse,
    WorkListResponse,
    WorkStatus,
)
from app.schemas.stats import (
    DailyStats,
    OperatorStats,
    TechnicianStats,
    TeamStats,
    StatsResponse,
)

__all__ = [
    # Technician schemas
    "TechnicianCreate",
    "TechnicianUpdate",
    "TechnicianResponse",
    "TechnicianListResponse",
    # Team schemas
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamListResponse",
    # Work schemas
    "WorkCreate",
    "WorkUpdate",
    "WorkResponse",
    "WorkListResponse",
    "WorkStatus",
    # Stats schemas
    "DailyStats",
    "OperatorStats",
    "TechnicianStats",
    "TeamStats",
    "StatsResponse",
]
