from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class JobStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    CLOSED = "closed"


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    technicians = relationship("Technician", back_populates="team")


class Technician(Base):
    __tablename__ = "technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    team = relationship("Team", back_populates="technicians")
    jobs = relationship("Job", back_populates="technician")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    work_order_number = Column(String(100), nullable=True)
    customer_name = Column(String(200), nullable=True)
    customer_address = Column(Text, nullable=True)
    customer_phone = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.OPEN)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    source_file = Column(String(255), nullable=True)
    extra_fields = Column(Text, nullable=True)  # JSON string for extra fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    technician = relationship("Technician", back_populates="jobs")
    notes = relationship("Note", back_populates="job", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="job", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="notes")


class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    uploaded_via = Column(String(50), default="web")  # web or telegram
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="photos")
