"""
Services package for Gestionale Fibra.

Contains business logic services for various operations.
"""

from app.services.pdf_ocr import PDFOCRService
from app.services.stats import StatsService

__all__ = ["PDFOCRService", "StatsService"]
