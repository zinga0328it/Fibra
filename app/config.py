"""
Configuration module for Gestionale Fibra.

Loads environment variables and provides application settings.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        app_name: Name of the application
        app_env: Environment (development, staging, production)
        debug: Debug mode flag
        secret_key: Secret key for cryptographic operations
        database_url: PostgreSQL connection URL
        api_key: API key for external service authentication
        jwt_secret_key: Secret key for JWT token signing
        jwt_algorithm: Algorithm used for JWT encoding
        access_token_expire_minutes: JWT token expiration time
        telegram_bot_token: Telegram bot API token
        telegram_webhook_url: Webhook URL for Telegram updates
        tesseract_cmd: Path to Tesseract OCR executable
        log_level: Logging level
        log_format: Logging format (json or text)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Gestionale Fibra"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/fibra_db"
    
    # Security
    api_key: Optional[str] = None
    jwt_secret_key: str = "jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    
    # OCR
    tesseract_cmd: str = "/usr/bin/tesseract"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience alias
settings = get_settings()
