"""
Tests for Pydantic schemas.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from app.schemas.technician import TechnicianCreate, TechnicianResponse, TechnicianUpdate
from app.schemas.team import TeamCreate, TeamResponse
from app.schemas.work import WorkCreate, WorkResponse, WorkStatus
from app.schemas.stats import DailyStats, OperatorStats


class TestTechnicianSchemas:
    """Tests for technician schemas."""
    
    def test_technician_create_valid(self):
        """Test valid technician creation."""
        data = TechnicianCreate(
            name="Mario Rossi",
            phone="+39123456789",
            email="mario@example.com",
            telegram_id="123456789",
        )
        assert data.name == "Mario Rossi"
        assert data.phone == "+39123456789"
        assert data.email == "mario@example.com"
        assert data.telegram_id == "123456789"
        assert data.is_active is True
    
    def test_technician_create_minimal(self):
        """Test technician creation with minimal data."""
        data = TechnicianCreate(name="Test User")
        assert data.name == "Test User"
        assert data.phone is None
        assert data.email is None
    
    def test_technician_create_empty_name_fails(self):
        """Test that empty name fails validation."""
        with pytest.raises(ValidationError):
            TechnicianCreate(name="")
    
    def test_technician_update_partial(self):
        """Test partial update schema."""
        data = TechnicianUpdate(phone="+39987654321")
        dump = data.model_dump(exclude_unset=True)
        assert "phone" in dump
        assert "name" not in dump


class TestTeamSchemas:
    """Tests for team schemas."""
    
    def test_team_create_valid(self):
        """Test valid team creation."""
        data = TeamCreate(
            name="Team Alpha",
            description="First response team",
        )
        assert data.name == "Team Alpha"
        assert data.description == "First response team"
        assert data.is_active is True
    
    def test_team_response_with_count(self):
        """Test team response with technician count."""
        data = TeamResponse(
            id=1,
            name="Team Alpha",
            description="Test",
            leader_id=None,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            technician_count=5,
        )
        assert data.technician_count == 5


class TestWorkSchemas:
    """Tests for work order schemas."""
    
    def test_work_create_valid(self):
        """Test valid work order creation."""
        data = WorkCreate(
            wr_number="WR-2024-001",
            operator="TIM",
            customer_name="Mario Bianchi",
            customer_address="Via Roma 1, Milano",
            scheduled_date=date.today(),
        )
        assert data.wr_number == "WR-2024-001"
        assert data.operator == "TIM"
        assert data.customer_name == "Mario Bianchi"
    
    def test_work_create_with_extra_data(self):
        """Test work order with dynamic JSON fields."""
        data = WorkCreate(
            wr_number="WR-2024-002",
            operator="Vodafone",
            customer_name="Test Customer",
            customer_address="Test Address",
            extra_data={"fiber_type": "GPON", "speed": "1Gbps"},
        )
        assert data.extra_data["fiber_type"] == "GPON"
        assert data.extra_data["speed"] == "1Gbps"
    
    def test_work_status_enum(self):
        """Test work status enumeration."""
        assert WorkStatus.PENDING == "pending"
        assert WorkStatus.COMPLETED == "completed"
        assert WorkStatus.REFUSED == "refused"


class TestStatsSchemas:
    """Tests for statistics schemas."""
    
    def test_daily_stats_defaults(self):
        """Test daily stats default values."""
        data = DailyStats(date=date.today())
        assert data.total_works == 0
        assert data.completed == 0
        assert data.pending == 0
    
    def test_operator_stats_completion_rate(self):
        """Test operator stats with completion rate."""
        data = OperatorStats(
            operator="TIM",
            total_works=100,
            completed=75,
            completion_rate=75.0,
        )
        assert data.completion_rate == 75.0
