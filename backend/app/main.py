from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import os

from app.database import engine, Base
from app.routes import teams_router, technicians_router, jobs_router, upload_router, statistics_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    yield
    
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Gestionale Fibra",
    description="Sistema gestionale per operazioni sul campo di telecomunicazioni",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
frontend_static = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
if os.path.exists(frontend_static):
    app.mount("/static", StaticFiles(directory=frontend_static), name="static")

# Mount uploads directory for serving photos
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Include API routers
app.include_router(teams_router)
app.include_router(technicians_router)
app.include_router(jobs_router)
app.include_router(upload_router)
app.include_router(statistics_router)


# Frontend routes
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/jobs")
async def jobs_page(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/technicians")
async def technicians_page(request: Request):
    return templates.TemplateResponse("technicians.html", {"request": request})


@app.get("/teams")
async def teams_page(request: Request):
    return templates.TemplateResponse("teams.html", {"request": request})


@app.get("/upload")
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/job/{job_id}")
async def job_detail_page(request: Request, job_id: int):
    return templates.TemplateResponse("job_detail.html", {"request": request, "job_id": job_id})


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
