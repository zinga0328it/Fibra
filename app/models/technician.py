"""
Technician model for Gestionale Fibra.

Represents field technicians who perform FTTH installations.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.work import Work


class Technician(Base, TimestampMixin):
    """
    Technician model representing a field technician.
    
    Attributes:
        id: Unique identifier
        name: Full name of the technician
        phone: Contact phone number
        email: Email address
        telegram_id: Telegram user ID for bot integration
        team_id: ID of the team this technician belongs to
        is_active: Whether the technician is currently active
        team: Related Team object
        works: List of Work orders assigned to this technician
    """
    
    __tablename__ = "technicians"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telegram_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
    )
    team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="technicians",
    )
    works: Mapped[list["Work"]] = relationship(
        "Work",
        back_populates="technician",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Technician(id={self.id}, name='{self.name}')>"
