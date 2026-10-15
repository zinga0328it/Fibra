import os
from fastapi import Header, HTTPException


def _get_valid_api_keys() -> set[str]:
    return {k for k in (os.getenv("API_KEY"), os.getenv("API_GPTS")) if k}


def verify_api_key(x_api_key: str | None = Header(None)):
    valid_api_keys = _get_valid_api_keys()
    if not valid_api_keys:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True
