from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import User
from app.schemas import LoginRequest, RegisterRequest, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token, create_refresh_token, get_user_by_username, get_db, require_role, get_current_user, get_current_user_optional
from fastapi import Body
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=dict)
def register(payload: RegisterRequest, db: Session = Depends(get_db_dep), current_user: User | None = Depends(get_current_user_optional)):
    # Allow public registration only if no users exist
    existing = db.query(User).first()
    if existing and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only admins can create new users")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=payload.username, hashed_password=get_password_hash(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db_dep)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "expires_in": 60 * 60, "refresh_token": refresh_token}


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db_dep)):
    try:
        payload = jwt.decode(refresh_token, os.getenv("SECRET_KEY") or "unsafe-secret", algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    new_refresh_token = create_refresh_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "expires_in": 60 * 60, "refresh_token": new_refresh_token}
