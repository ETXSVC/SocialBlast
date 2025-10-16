"""
Media Blaster - Social Media Automation Platform

A powerful API for automating social media posts across multiple platforms.
"""

__version__ = "1.0.0"
__author__ = "Your Name <your.email@example.com>"
__license__ = "MIT"

# Import key components for easier access
from .config import settings
from .database import init_db, get_db, SessionLocal
from .exceptions import (
    AppError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitExceededError,
    ServiceUnavailableError,
    DatabaseError,
    FileUploadError,
    SocialMediaError
)

# Initialize logging when the package is imported
from .utils import setup_logging
setup_logging()

# Create a logger instance
import logging
logger = logging.getLogger(__name__)

__all__ = [
    # Core components
    'settings',
    'init_db',
    'get_db',
    'SessionLocal',
    'logger',
    
    # Exceptions
    'AppError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitExceededError',
    'ServiceUnavailableError',
    'DatabaseError',
    'FileUploadError',
    'SocialMediaError',
]
