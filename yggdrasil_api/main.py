"""
FastAPI application running on Yggdrasil private network.
Provides secure internal API for FTTH management system.
"""

import os
import sys
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Configuration
YGGDRASIL_HOST = os.getenv("YGG_HOST", "200:421e:6385:4a8b:dca7:cfb:197f:e9c3")
YGGDRASIL_PORT = int(os.getenv("YGG_PORT", "6040"))
API_KEY = os.getenv("YGG_API_KEY", "your-secure-yggdrasil-key-here")

# Database configuration - point to main project database
MAIN_PROJECT_DIR = Path(__file__).parent.parent
DATABASE_URL = f"sqlite:///{MAIN_PROJECT_DIR}/ftth.db"
os.environ["DATABASE_URL"] = DATABASE_URL

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Yggdrasil API starting on [{YGGDRASIL_HOST}]:{YGGDRASIL_PORT}")
    yield
    print("🛑 Yggdrasil API shutting down")

# Create app
app = FastAPI(
    title="FTTH Yggdrasil API",
    description="Internal API for FTTH management via Yggdrasil network",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for internal network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Yggdrasil network is already private
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Authentication ============

async def verify_api_key(x_key: str = Header(..., alias="X-KEY")):
    """Verify API key from X-KEY header"""
    if x_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_key


# ============ Health Check ============

@app.get("/health")
async def health_check():
    """Basic health check - no auth required"""
    return {
        "status": "ok",
        "service": "ftth-yggdrasil-api",
        "host": YGGDRASIL_HOST,
        "port": YGGDRASIL_PORT
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FTTH Yggdrasil API",
        "docs": f"http://[{YGGDRASIL_HOST}]:{YGGDRASIL_PORT}/docs"
    }


# ============ Import Routers ============

from routers import ingest, jobs, manual

app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])  
app.include_router(manual.router, prefix="/manual", tags=["Manual"])


# ============ Main ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=YGGDRASIL_HOST,
        port=YGGDRASIL_PORT,
        reload=True,
        log_level="info"
    )
