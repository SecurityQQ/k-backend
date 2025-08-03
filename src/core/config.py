from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "K-Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Settings  
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_RELOAD: bool = False
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # JWT Settings
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 90
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # External API Keys
    OPENAI_API_KEY: Optional[str] = None
    BROWSERLESS_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variablses


settings = Settings()