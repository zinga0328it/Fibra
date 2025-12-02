"""
Team model for Gestionale Fibra.

Represents teams of technicians organized by area or specialization.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.technician import Technician


class Team(Base, TimestampMixin):
    """
    Team model representing a group of technicians.
    
    Attributes:
        id: Unique identifier
        name: Team name
        description: Team description or area of operation
        leader_id: ID of the team leader (technician)
        is_active: Whether the team is currently active
        technicians: List of technicians in this team
    """
    
    __tablename__ = "teams"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    leader_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    technicians: Mapped[list["Technician"]] = relationship(
        "Technician",
        back_populates="team",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"
