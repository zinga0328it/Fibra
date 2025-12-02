from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class JobStatusEnum(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    CLOSED = "closed"


# Team Schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Technician Schemas
class TechnicianBase(BaseModel):
    name: str
    surname: str
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    team_id: Optional[int] = None


class TechnicianCreate(TechnicianBase):
    pass


class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    team_id: Optional[int] = None


class TechnicianResponse(TechnicianBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Note Schemas
class NoteBase(BaseModel):
    content: str


class NoteCreate(NoteBase):
    job_id: int


class NoteResponse(NoteBase):
    id: int
    job_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Photo Schemas
class PhotoBase(BaseModel):
    original_filename: Optional[str] = None


class PhotoResponse(BaseModel):
    id: int
    job_id: int
    filename: str
    original_filename: Optional[str]
    uploaded_via: str
    created_at: datetime

    class Config:
        from_attributes = True


# Job Schemas
class JobBase(BaseModel):
    work_order_number: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_phone: Optional[str] = None
    description: Optional[str] = None
    technician_id: Optional[int] = None
    extra_fields: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    work_order_number: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_phone: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatusEnum] = None
    technician_id: Optional[int] = None
    extra_fields: Optional[str] = None


class JobResponse(JobBase):
    id: int
    status: JobStatusEnum
    source_file: Optional[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    notes: List[NoteResponse] = []
    photos: List[PhotoResponse] = []

    class Config:
        from_attributes = True


# Statistics Schemas
class DailyStats(BaseModel):
    date: str
    count: int


class OperatorStats(BaseModel):
    technician_id: int
    technician_name: str
    job_count: int


class TeamStats(BaseModel):
    team_id: int
    team_name: str
    job_count: int


class StatisticsResponse(BaseModel):
    jobs_per_day: List[DailyStats]
    jobs_per_operator: List[OperatorStats]
    jobs_per_team: List[TeamStats]
    total_jobs: int
    open_jobs: int
    in_progress_jobs: int
    paused_jobs: int
    closed_jobs: int
