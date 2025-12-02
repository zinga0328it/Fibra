from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os
from app.database import engine
from app.models import models

try:
	models.Base.metadata.create_all(bind=engine)
except Exception as e:
	# If DB isn't available (for example during local development without Postgres), warn and continue
	import logging
	logging.getLogger("uvicorn.error").warning(f"Could not create tables on startup: {e}")

app = FastAPI(title="FTTH Management System")

app.mount("/static", StaticFiles(directory="web/publica"), name="static")

# Allow cross origin requests for development. Tighten this in production.
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Basic rotating file logger (can be monitored by fail2ban if desired). Keep this optional.
os.makedirs("logs", exist_ok=True)
handler = RotatingFileHandler("logs/ftth.log", maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# Include routers
from app.routes import works, technicians, teams, stats
app.include_router(works.router)
app.include_router(technicians.router)
app.include_router(teams.router)
app.include_router(stats.router)