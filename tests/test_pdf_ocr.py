"""
Tests for PDF/OCR parsing service.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.pdf_ocr import PDFOCRService, ExtractedWorkData


class TestPDFOCRService:
    """Tests for PDF/OCR parsing service."""
    
    @pytest.fixture
    def service(self):
        """Create a PDF/OCR service instance."""
        return PDFOCRService()
    
    def test_extract_work_data_initialization(self):
        """Test ExtractedWorkData default initialization."""
        data = ExtractedWorkData()
        
        assert data.wr_number is None
        assert data.operator is None
        assert data.extra_data == {}
    
    def test_extract_work_data_with_values(self):
        """Test ExtractedWorkData with values."""
        data = ExtractedWorkData(
            wr_number="WR-001",
            operator="TIM",
            customer_name="Test Customer",
            customer_address="Via Test 1",
        )
        
        assert data.wr_number == "WR-001"
        assert data.operator == "TIM"
    
    def test_detect_operator(self, service):
        """Test operator detection from text."""
        text = "Ordine di lavoro per TIM FTTH installazione"
        
        operator = service._detect_operator(text)
        
        assert operator == "TIM"
    
    def test_detect_operator_case_insensitive(self, service):
        """Test operator detection is case insensitive."""
        text = "Installazione vodafone fibra"
        
        operator = service._detect_operator(text)
        
        assert operator == "Vodafone"
    
    def test_detect_operator_not_found(self, service):
        """Test operator detection when not found."""
        text = "Generic text without operator"
        
        operator = service._detect_operator(text)
        
        assert operator is None
    
    def test_find_pattern_wr_number(self, service):
        """Test WR number pattern extraction."""
        text = "WR: ABC-123-456"
        
        wr = service._find_pattern(text, service.PATTERNS["wr_number"])
        
        assert wr == "ABC-123-456"
    
    def test_find_pattern_phone(self, service):
        """Test phone number pattern extraction."""
        text = "Tel: +39 333 123 4567"
        
        phone = service._find_pattern(text, service.PATTERNS["phone"])
        
        assert phone is not None
        assert "333" in phone
    
    def test_find_pattern_date(self, service):
        """Test date pattern extraction."""
        text = "Data: 15/12/2024"
        
        date_str = service._find_pattern(text, service.PATTERNS["date"])
        
        assert date_str == "15/12/2024"
    
    def test_extract_customer_name(self, service):
        """Test customer name extraction."""
        text = "Cliente: Mario Rossi\nTel: 123456"
        
        name = service._extract_customer_name(text)
        
        assert name is not None
        assert "Mario Rossi" in name
    
    def test_extract_address(self, service):
        """Test address extraction."""
        text = "Via Roma 123, Milano"
        
        address = service._extract_address(text)
        
        assert address is not None
        assert "Via Roma" in address
