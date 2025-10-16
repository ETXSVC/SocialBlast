from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from typing import Optional, Callable, Awaitable, Dict, Any
import time
import logging

from .config import settings

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Content Security Policy (CSP)
        # Note: Adjust this based on your application's needs
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers["Content-Security-Policy"] = csp
        
        # Feature Policy
        response.headers["Feature-Policy"] = "accelerometer 'none'; camera 'none'; geolocation 'none';"
        
        return response

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Process-Time header to responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Log request
        logger.info(
            "Request: %s %s",
            request.method,
            request.url.path,
            extra={
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Response: %s %s - %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )
        
        return response

def setup_middleware(app):
    """Configure all middleware for the application"""
    
    # Security middleware
    if not settings.DEBUG:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS != ["*"] else ["*"],
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    
    # Logging middleware (add last to catch all exceptions)
    app.add_middleware(LoggingMiddleware)
    
    return app
