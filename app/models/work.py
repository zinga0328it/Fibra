"""
Work model for Gestionale Fibra.

Represents work orders (WR) for FTTH installations with dynamic JSON fields.
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.technician import Technician


class WorkStatus(str, Enum):
    """Enumeration of possible work order statuses."""
    
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REFUSED = "refused"
    CANCELLED = "cancelled"


class Work(Base, TimestampMixin):
    """
    Work model representing a work order (WR) for FTTH installation.
    
    Attributes:
        id: Unique identifier
        wr_number: Work request number (external reference)
        operator: Telecom operator name (e.g., TIM, Vodafone)
        customer_name: Customer's full name
        customer_address: Installation address
        customer_phone: Customer contact number
        scheduled_date: Scheduled date for the work
        status: Current status of the work order
        technician_id: Assigned technician ID
        notes: Additional notes or comments
        extra_data: Dynamic JSON fields for additional data
        photos: JSON array of photo URLs/paths
        completion_date: Date when work was completed
        technician: Related Technician object
    """
    
    __tablename__ = "works"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wr_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    operator: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_address: Mapped[str] = mapped_column(Text, nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[WorkStatus] = mapped_column(
        String(20),
        default=WorkStatus.PENDING,
        index=True,
    )
    technician_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("technicians.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    photos: Mapped[Optional[list[str]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )
    completion_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    technician: Mapped[Optional["Technician"]] = relationship(
        "Technician",
        back_populates="works",
    )
    
    def __repr__(self) -> str:
        return f"<Work(id={self.id}, wr_number='{self.wr_number}', status='{self.status}')>"
