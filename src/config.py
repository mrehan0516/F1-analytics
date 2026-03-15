"""
F1 Pit Wall AI - Configuration Settings
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Google Cloud
    google_cloud_project: str = "f1-pit-wall-ai"
    google_api_key: str = ""
    google_application_credentials: Optional[str] = None
    
    # Gemini Model
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    
    # F1 Data
    f1_cache_dir: str = "./f1_cache"


settings = Settings()
