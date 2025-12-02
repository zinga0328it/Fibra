"""
Logging module for Gestionale Fibra.

Configures structured logging with support for JSON and text formats.
Uses structlog for structured logging capabilities.
"""

import logging
import sys
from typing import Any

import structlog

from app.config import settings


def configure_logging() -> None:
    """
    Configure application logging.
    
    Sets up structlog with appropriate processors based on environment.
    JSON format for production, colored console output for development.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Common processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        # JSON format for production
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Colored console output for development
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)
