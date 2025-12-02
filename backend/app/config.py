from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fibra_db"
    
    # Application
    secret_key: str = "your-secret-key-here-change-in-production"
    debug: bool = True
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    
    # Uploads
    upload_dir: str = "./uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
