from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class AppError(HTTPException):
    """Base exception for application errors"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "app_error"
        self.headers = headers or {}
        
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=self.headers
        )

class ValidationError(AppError):
    """Raised when input validation fails"""
    def __init__(self, detail: str = "Validation error", errors: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="validation_error",
            headers={"X-Error-Code": "validation_error"}
        )
        self.errors = errors or {}

class AuthenticationError(AppError):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="authentication_error",
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(AppError):
    """Raised when a user doesn't have permission to access a resource"""
    def __init__(self, detail: str = "Not authorized to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="authorization_error"
        )

class NotFoundError(AppError):
    """Raised when a resource is not found"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
            error_code="not_found"
        )

class ConflictError(AppError):
    """Raised when a resource conflict occurs"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="conflict"
        )

class RateLimitExceededError(AppError):
    """Raised when rate limit is exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="rate_limit_exceeded",
            headers={"Retry-After": "60"}
        )

class ServiceUnavailableError(AppError):
    """Raised when a required service is unavailable"""
    def __init__(self, service: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is currently unavailable. Please try again later.",
            error_code="service_unavailable"
        )

class DatabaseError(AppError):
    """Raised when a database operation fails"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="database_error"
        )

class FileUploadError(AppError):
    """Raised when file upload fails"""
    def __init__(self, detail: str = "File upload failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="file_upload_error"
        )

class SocialMediaError(AppError):
    """Raised when a social media API operation fails"""
    def __init__(self, platform: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{platform} error: {detail}",
            error_code=f"{platform.lower()}_error"
        )
