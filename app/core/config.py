from pydantic import BaseSettings, validator
from typing import Optional, List
import os
from pathlib import Path
from functools import lru_cache
import logging
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Talk2SQL"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    USE_DB: bool = os.getenv("USE_DB", "false").lower() == "true"
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DATABASE_HOST: Optional[str] = os.getenv("DATABASE_HOST")
    DATABASE_PORT: Optional[str] = os.getenv("DATABASE_PORT")
    DATABASE_USER: Optional[str] = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD: Optional[str] = os.getenv("DATABASE_PASSWORD")
    DATABASE_NAME: Optional[str] = os.getenv("DATABASE_NAME")
    
    # Session management
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "60"))
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @validator("SESSION_SECRET_KEY", pre=True)
    def validate_session_secret_key(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("SESSION_SECRET_KEY must be set in production environment")
        return v

    @validator("DATABASE_HOST", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME", pre=True)
    def validate_database_settings(cls, v: Optional[str], field: str) -> Optional[str]:
        if not cls.USE_DB:
            return None
        if not v:
            # Default values for development when database is enabled
            defaults = {
                "DATABASE_HOST": "localhost",
                "DATABASE_PORT": "5432",
                "DATABASE_USER": "postgres",
                "DATABASE_PASSWORD": "postgres",
                "DATABASE_NAME": "postgres"
            }
            return defaults.get(field)
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"

    def get_database_url(self) -> Optional[str]:
        """Generate database URL if not explicitly set and database is enabled"""
        if not self.USE_DB:
            return None
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if not all([self.DATABASE_HOST, self.DATABASE_PORT, self.DATABASE_USER, 
                   self.DATABASE_PASSWORD, self.DATABASE_NAME]):
            return None
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance"""
    return Settings()

settings = get_settings()
