import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from datetime import datetime, timezone
import json
from urllib.parse import urlparse
import re

from .config import settings

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # Error file handler
    error_file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

def validate_url(url: str) -> bool:
    """Validate a URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def is_valid_email(email: str) -> bool:
    """Validate an email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_current_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string"""
    return dt.isoformat() if dt else None

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string to datetime object"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def to_json_serializable(data: Any) -> Any:
    """Convert data to JSON serializable format"""
    if isinstance(data, dict):
        return {k: to_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_json_serializable(item) for item in data]
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    elif hasattr(data, 'isoformat'):  # Handle datetime, date, time
        return data.isoformat()
    elif hasattr(data, '__dict__'):  # Handle objects with __dict__
        return to_json_serializable(data.__dict__)
    else:
        return str(data)  # Fallback to string representation

def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return Path(filename).suffix.lower()

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes"""
    return Path(file_path).stat().st_size / (1024 * 1024)

def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def clean_filename(filename: str) -> str:
    """Clean a filename by removing special characters"""
    # Keep only alphanumeric, spaces, dots, and underscores
    cleaned = re.sub(r'[^\w\s.-]', '', filename).strip()
    # Replace spaces with underscores
    return re.sub(r'\s+', '_', cleaned)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, rate_limit: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            rate_limit: Number of allowed requests
            time_window: Time window in seconds (default: 60)
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed"""
        current_time = time.time()
        
        # Remove old entries
        self.requests[key] = [t for t in self.requests.get(key, []) 
                            if current_time - t < self.time_window]
        
        # Check rate limit
        if len(self.requests.get(key, [])) >= self.rate_limit:
            return False
        
        # Add current request
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key].append(current_time)
        
        return True
