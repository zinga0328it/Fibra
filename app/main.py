"""
Gestionale Fibra - Main FastAPI Application

FTTH Installation Management System for managing technicians, teams,
work orders, and providing a Telegram bot for field operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.models.base import close_db, init_db
from app.routers import (
    stats_router,
    teams_router,
    technicians_router,
    telegram_router,
    works_router,
)
from app.telegram.bot import telegram_bot

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Initializes database and Telegram bot on startup,
    and cleans up resources on shutdown.
    """
    # Startup
    logger.info(
        "Starting Gestionale Fibra",
        version=__version__,
        environment=settings.app_env,
    )
    
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
    
    try:
        await telegram_bot.initialize()
    except Exception as e:
        logger.error("Failed to initialize Telegram bot", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gestionale Fibra")
    
    try:
        await telegram_bot.shutdown()
    except Exception:
        pass
    
    try:
        await close_db()
    except Exception:
        pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="FTTH Installation Management System for telecom field operations",
    version=__version__,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(technicians_router)
app.include_router(teams_router)
app.include_router(works_router)
app.include_router(stats_router)
app.include_router(telegram_router)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """
    Render the main dashboard page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered dashboard template
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": settings.app_name},
    )


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.app_env,
    }


@app.get("/api")
async def api_info() -> dict:
    """
    API information endpoint.
    
    Returns:
        dict: API information
    """
    return {
        "name": settings.app_name,
        "version": __version__,
        "endpoints": {
            "technicians": "/api/technicians",
            "teams": "/api/teams",
            "works": "/api/works",
            "stats": "/api/stats",
            "telegram_webhook": "/telegram/webhook",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
