"""
Team schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    """Base schema for team data."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    description: Optional[str] = Field(None, max_length=500, description="Team description")
    leader_id: Optional[int] = Field(None, description="Team leader's technician ID")
    is_active: bool = Field(True, description="Whether the team is active")


class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    leader_id: Optional[int] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    """Schema for team response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    technician_count: Optional[int] = Field(0, description="Number of technicians in team")


class TeamListResponse(BaseModel):
    """Schema for paginated team list response."""
    
    items: list[TeamResponse]
    total: int
    page: int
    size: int
    pages: int
