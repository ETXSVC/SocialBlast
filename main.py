"""
Media Blaster API - Main Application

This is the entry point for the Media Blaster API, a social media automation platform.
"""

import logging
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import init_db, get_db
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
from .middleware import setup_middleware
from .utils import setup_logging
from . import __version__

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=__version__,
    description="API for Media Blaster - Social Media Automation Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup middleware
setup_middleware(app)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Media Blaster API...")
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Any other startup tasks
        logger.info("Startup completed successfully")
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Media Blaster API...")
    # Any cleanup tasks

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle custom application errors"""
    logger.error(f"Application error: {exc.detail} (code: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        },
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.critical(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "error_code": "internal_server_error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "environment": "development" if settings.DEBUG else "production"
    }

# Import and include routers
# from .routers import auth, users, posts, social_media
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
# app.include_router(social_media.router, prefix="/api/v1/social", tags=["Social Media"])

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "status": "running",
        "documentation": "/docs",
        "environment": "development" if settings.DEBUG else "production"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
