from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    """Authentication token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token (if supported)")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": "def50200e5b2bce3e0e3b8b5e8c8f1a2..."
            }
        }

class TokenData(BaseModel):
    """Data stored in the JWT token."""
    user_id: int = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User's email")
    scopes: list[str] = Field(default_factory=list, description="List of permission scopes")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    
    class Config:
        orm_mode = True

class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: Optional[int] = Field(None, description="Subject (user ID)")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at time")
    
    class Config:
        orm_mode = True

class RefreshTokenCreate(BaseModel):
    """Request model for refreshing an access token."""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "def50200e5b2bce3e0e3b8b5e8c8f1a2..."
            }
        }

class TokenBlacklistCreate(BaseModel):
    """Model for blacklisting a token."""
    token: str = Field(..., description="Token to blacklist")
    expires_at: datetime = Field(..., description="Token expiration time")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_at": "2023-12-31T23:59:59"
            }
        }
