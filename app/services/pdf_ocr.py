"""
PDF and OCR parsing service for Gestionale Fibra.

Extracts work order information from PDF files using pdfplumber,
with pytesseract fallback for scanned documents.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedWorkData:
    """Data extracted from a work order PDF."""
    
    wr_number: Optional[str] = None
    operator: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_phone: Optional[str] = None
    scheduled_date: Optional[str] = None
    extra_data: dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


class PDFOCRService:
    """
    Service for extracting work order data from PDF files.
    
    Uses pdfplumber for text-based PDFs and pytesseract OCR
    as a fallback for scanned documents.
    """
    
    # Common patterns for extracting work order data
    PATTERNS = {
        "wr_number": [
            r"WR[:\s]*([A-Z0-9-]+)",
            r"Work Request[:\s]*([A-Z0-9-]+)",
            r"Ordine[:\s]*([A-Z0-9-]+)",
            r"N\.\s*Pratica[:\s]*([A-Z0-9-]+)",
        ],
        "phone": [
            r"Tel[:\s.]*(\+?[\d\s-]{10,})",
            r"Telefono[:\s]*(\+?[\d\s-]{10,})",
            r"Cell[:\s.]*(\+?[\d\s-]{10,})",
        ],
        "date": [
            r"Data[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})",
            r"Scheduled[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})",
            r"(\d{2}[/-]\d{2}[/-]\d{4})",
        ],
    }
    
    # Known telecom operators
    OPERATORS = [
        "TIM", "Vodafone", "WindTre", "Fastweb", "Iliad",
        "Sky", "Eolo", "Tiscali", "Open Fiber",
    ]
    
    def __init__(self):
        """Initialize the PDF/OCR service."""
        self._pdfplumber = None
        self._pytesseract = None
        self._pdf2image = None
    
    def _get_pdfplumber(self):
        """Lazy load pdfplumber."""
        if self._pdfplumber is None:
            try:
                import pdfplumber
                self._pdfplumber = pdfplumber
            except ImportError:
                logger.warning("pdfplumber not installed")
                raise ImportError("pdfplumber is required for PDF parsing")
        return self._pdfplumber
    
    def _get_pytesseract(self):
        """Lazy load pytesseract."""
        if self._pytesseract is None:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
                self._pytesseract = pytesseract
            except ImportError:
                logger.warning("pytesseract not installed")
                return None
        return self._pytesseract
    
    def _get_pdf2image(self):
        """Lazy load pdf2image."""
        if self._pdf2image is None:
            try:
                from pdf2image import convert_from_path
                self._pdf2image = convert_from_path
            except ImportError:
                logger.warning("pdf2image not installed")
                return None
        return self._pdf2image
    
    def extract_text_from_pdf(self, pdf_path: str | Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        pdf_path = Path(pdf_path)
        pdfplumber = self._get_pdfplumber()
        
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            full_text = "\n".join(text_content)
            
            # If no text was extracted, try OCR fallback
            if not full_text.strip():
                logger.info("No text extracted, trying OCR fallback")
                full_text = self._ocr_fallback(pdf_path)
            
            return full_text
            
        except Exception as e:
            logger.error("Error extracting text from PDF", error=str(e))
            raise
    
    def _ocr_fallback(self, pdf_path: Path) -> str:
        """
        Use OCR to extract text from a scanned PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: OCR-extracted text
        """
        pytesseract = self._get_pytesseract()
        convert_from_path = self._get_pdf2image()
        
        if not pytesseract or not convert_from_path:
            logger.warning("OCR fallback not available")
            return ""
        
        try:
            images = convert_from_path(pdf_path)
            text_content = []
            
            for image in images:
                text = pytesseract.image_to_string(image, lang="ita+eng")
                text_content.append(text)
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error("OCR fallback failed", error=str(e))
            return ""
    
    def _find_pattern(self, text: str, patterns: list[str]) -> Optional[str]:
        """
        Find the first matching pattern in text.
        
        Args:
            text: Text to search
            patterns: List of regex patterns to try
            
        Returns:
            str: First matched group or None
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _detect_operator(self, text: str) -> Optional[str]:
        """
        Detect telecom operator from text.
        
        Args:
            text: Text to search
            
        Returns:
            str: Detected operator name or None
        """
        text_upper = text.upper()
        for operator in self.OPERATORS:
            if operator.upper() in text_upper:
                return operator
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """
        Extract address from text.
        
        Args:
            text: Text to search
            
        Returns:
            str: Extracted address or None
        """
        # Common Italian address patterns
        patterns = [
            r"Indirizzo[:\s]*(.+?)(?:\n|Tel|$)",
            r"Via\s+[A-Za-z\s]+,?\s*\d+",
            r"Piazza\s+[A-Za-z\s]+,?\s*\d+",
            r"Corso\s+[A-Za-z\s]+,?\s*\d+",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_customer_name(self, text: str) -> Optional[str]:
        """
        Extract customer name from text.
        
        Args:
            text: Text to search
            
        Returns:
            str: Extracted customer name or None
        """
        patterns = [
            r"Cliente[:\s]*(.+?)(?:\n|Tel|Ind|$)",
            r"Nome[:\s]*(.+?)(?:\n|Tel|Ind|$)",
            r"Intestatario[:\s]*(.+?)(?:\n|Tel|Ind|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        return None
    
    def parse_work_order(self, pdf_path: str | Path) -> ExtractedWorkData:
        """
        Parse a work order PDF and extract relevant data.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedWorkData: Extracted work order data
        """
        text = self.extract_text_from_pdf(pdf_path)
        
        extracted = ExtractedWorkData(
            wr_number=self._find_pattern(text, self.PATTERNS["wr_number"]),
            operator=self._detect_operator(text),
            customer_name=self._extract_customer_name(text),
            customer_address=self._extract_address(text),
            customer_phone=self._find_pattern(text, self.PATTERNS["phone"]),
            scheduled_date=self._find_pattern(text, self.PATTERNS["date"]),
            extra_data={"raw_text_preview": text[:500] if text else None},
        )
        
        logger.info(
            "Parsed work order PDF",
            wr_number=extracted.wr_number,
            operator=extracted.operator,
        )
        
        return extracted
    
    async def parse_work_order_async(
        self, pdf_path: str | Path
    ) -> ExtractedWorkData:
        """
        Async wrapper for parse_work_order.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedWorkData: Extracted work order data
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parse_work_order, pdf_path)


# Singleton instance
pdf_ocr_service = PDFOCRService()
