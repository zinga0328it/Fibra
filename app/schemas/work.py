"""
Work order schemas for API request/response validation.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkStatus(str, Enum):
    """Enumeration of work order statuses."""
    
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REFUSED = "refused"
    CANCELLED = "cancelled"


class WorkBase(BaseModel):
    """Base schema for work order data."""
    
    wr_number: str = Field(..., min_length=1, max_length=50, description="Work request number")
    operator: str = Field(..., min_length=1, max_length=50, description="Telecom operator")
    customer_name: str = Field(..., min_length=1, max_length=200, description="Customer name")
    customer_address: str = Field(..., min_length=1, description="Installation address")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Customer phone")
    scheduled_date: Optional[date] = Field(None, description="Scheduled date")
    notes: Optional[str] = Field(None, description="Additional notes")
    extra_data: Optional[dict[str, Any]] = Field(None, description="Dynamic extra fields")


class WorkCreate(WorkBase):
    """Schema for creating a new work order."""
    
    technician_id: Optional[int] = Field(None, description="Assigned technician ID")


class WorkUpdate(BaseModel):
    """Schema for updating a work order."""
    
    operator: Optional[str] = Field(None, min_length=1, max_length=50)
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_address: Optional[str] = None
    customer_phone: Optional[str] = Field(None, max_length=20)
    scheduled_date: Optional[date] = None
    status: Optional[WorkStatus] = None
    technician_id: Optional[int] = None
    notes: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None
    photos: Optional[list[str]] = None


class WorkResponse(WorkBase):
    """Schema for work order response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: WorkStatus
    technician_id: Optional[int]
    photos: Optional[list[str]]
    completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class WorkListResponse(BaseModel):
    """Schema for paginated work order list response."""
    
    items: list[WorkResponse]
    total: int
    page: int
    size: int
    pages: int
