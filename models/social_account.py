from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl

class SocialPlatform(str, Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"

class SocialAccountStatus(str, Enum):
    """Status of a social media account connection."""
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"

class SocialAccountBase(BaseModel):
    """Base model for social account data."""
    platform: SocialPlatform = Field(..., description="Social media platform")
    account_name: str = Field(..., min_length=1, max_length=255, description="Account display name")
    account_id: str = Field(..., description="Platform-specific account ID")
    is_active: bool = Field(default=True, description="Whether the account is active")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional platform-specific account data"
    )
    
    @validator('account_name')
    def validate_account_name(cls, v):
        if not v.strip():
            raise ValueError("Account name cannot be empty")
        return v.strip()

class SocialAccountCreate(SocialAccountBase):
    """Model for creating a new social account connection."""
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(
        None,
        description="When the access token expires"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "instagram",
                "account_name": "my_business",
                "account_id": "17841405793087218",
                "is_active": True,
                "access_token": "IGQVJ...",
                "refresh_token": "IGQVJ...",
                "token_expires_at": "2024-12-31T23:59:59",
                "metadata": {
                    "username": "my_business",
                    "profile_picture": "https://..."
                }
            }
        }

class SocialAccountUpdate(BaseModel):
    """Model for updating a social account."""
    account_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated account display name"
    )
    is_active: Optional[bool] = Field(None, description="Whether the account is active")
    access_token: Optional[str] = Field(None, description="New OAuth access token")
    refresh_token: Optional[str] = Field(None, description="New OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(
        None,
        description="New token expiration time"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated platform-specific account data"
    )

class SocialAccountInDB(SocialAccountBase):
    """Database model for social account."""
    id: int = Field(..., description="Unique account ID")
    user_id: int = Field(..., description="ID of the user who owns this account")
    status: SocialAccountStatus = Field(..., description="Connection status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_synced_at: Optional[datetime] = Field(None, description="When the account was last synced")
    
    class Config:
        orm_mode = True

class SocialAccount(SocialAccountInDB):
    """Response model for social account data."""
    profile_picture: Optional[HttpUrl] = Field(
        None,
        description="URL of the account's profile picture"
    )
    username: Optional[str] = Field(
        None,
        description="Platform username/handle"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "platform": "instagram",
                "account_name": "My Business",
                "account_id": "17841405793087218",
                "username": "my_business",
                "profile_picture": "https://scontent.cdninstagram.com/v/...",
                "status": "connected",
                "is_active": True,
                "created_at": "2023-01-15T10:30:00",
                "updated_at": "2023-12-01T15:45:00",
                "last_synced_at": "2023-12-01T15:45:00",
                "metadata": {
                    "followers_count": 1234,
                    "media_count": 56,
                    "category": "Business"
                }
            }
        }

class SocialAccountInResponse(BaseModel):
    """Wrapper for social account response with additional metadata."""
    account: SocialAccount
    
    class Config:
        schema_extra = {
            "example": {
                "account": {
                    "id": 1,
                    "user_id": 1,
                    "platform": "instagram",
                    "account_name": "My Business",
                    "account_id": "17841405793087218",
                    "username": "my_business",
                    "profile_picture": "https://scontent.cdninstagram.com/v/...",
                    "status": "connected",
                    "is_active": True,
                    "created_at": "2023-01-15T10:30:00",
                    "updated_at": "2023-12-01T15:45:00",
                    "last_synced_at": "2023-12-01T15:45:00"
                }
            }
        }

class SocialAccountConnectRequest(BaseModel):
    """Request model for connecting a social account via OAuth."""
    platform: SocialPlatform = Field(..., description="Social media platform to connect")
    redirect_uri: str = Field(..., description="URI to redirect to after authentication")
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "instagram",
                "redirect_uri": "https://yourapp.com/callback/instagram"
            }
        }

class SocialAccountConnectResponse(BaseModel):
    """Response model for social account connection request."""
    auth_url: str = Field(..., description="URL to redirect user for OAuth authentication")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")
    
    class Config:
        schema_extra = {
            "example": {
                "auth_url": "https://api.instagram.com/oauth/authorize?client_id=...",
                "state": "abc123xyz"
            }
        }
