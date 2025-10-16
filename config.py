from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional, Dict, Any
from pathlib import Path

class Settings(BaseSettings):
    # Application
    DEBUG: bool = False
    PROJECT_NAME: str = "Media Blaster API"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Uploads
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif"}
    
    # Rate Limiting
    RATE_LIMIT: str = "100/hour"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Initialize settings
settings = Settings()

# Create upload directory if it doesn't exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
