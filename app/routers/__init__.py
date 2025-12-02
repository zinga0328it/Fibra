"""
API routers package for Gestionale Fibra.

Contains all API route handlers organized by resource.
"""

from app.routers.technicians import router as technicians_router
from app.routers.teams import router as teams_router
from app.routers.works import router as works_router
from app.routers.stats import router as stats_router
from app.routers.telegram import router as telegram_router

__all__ = [
    "technicians_router",
    "teams_router",
    "works_router",
    "stats_router",
    "telegram_router",
]
