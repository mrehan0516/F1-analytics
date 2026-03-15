"""
F1 Race Strategist Live Agent - Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Cloud
    google_cloud_project: str = Field(default="", env="GOOGLE_CLOUD_PROJECT")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    
    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    port: int = Field(default=8080, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS Configuration (restrict in production)
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # Gemini Model Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
