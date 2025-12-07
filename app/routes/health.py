from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    """Simple health endpoint to verify the app is up.

    Returns a basic JSON with status and current timestamp.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
