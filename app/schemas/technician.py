"""
Technician schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TechnicianBase(BaseModel):
    """Base schema for technician data."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Technician's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    telegram_id: Optional[str] = Field(None, max_length=50, description="Telegram user ID")
    team_id: Optional[int] = Field(None, description="Team ID")
    is_active: bool = Field(True, description="Whether the technician is active")


class TechnicianCreate(TechnicianBase):
    """Schema for creating a new technician."""
    pass


class TechnicianUpdate(BaseModel):
    """Schema for updating a technician."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = Field(None, max_length=50)
    team_id: Optional[int] = None
    is_active: Optional[bool] = None


class TechnicianResponse(TechnicianBase):
    """Schema for technician response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class TechnicianListResponse(BaseModel):
    """Schema for paginated technician list response."""
    
    items: list[TechnicianResponse]
    total: int
    page: int
    size: int
    pages: int
