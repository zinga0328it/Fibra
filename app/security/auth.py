"""
Authentication and authorization module.

Provides API key validation and JWT token handling for securing endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token payload data."""
    
    sub: str
    exp: datetime
    iat: datetime
    type: str = "access"


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (usually user ID or username)
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenData(**payload)
    except JWTError:
        return None


def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key.
    
    Args:
        api_key: API key to verify
        
    Returns:
        bool: True if API key is valid
    """
    if not settings.api_key:
        # No API key configured, allow all requests
        return True
    return api_key == settings.api_key


async def get_api_key_header(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Dependency to get and validate API key from header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not settings.api_key:
        # No API key required
        return None
    
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[TokenData]:
    """
    Dependency to get current user from JWT token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_token(credentials.credentials)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data
