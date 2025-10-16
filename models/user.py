from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    role: UserRole = Field(default=UserRole.USER, description="User role/privilege level")

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100, description="User's password (min 8 characters)")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User's full name")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")
    role: Optional[UserRole] = Field(None, description="User role/privilege level")

class UserInDB(UserBase):
    """Database model for user."""
    id: int = Field(..., description="Unique user ID")
    hashed_password: str = Field(..., description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        orm_mode = True

class User(UserBase):
    """Response model for user data (excludes sensitive information)."""
    id: int = Field(..., description="Unique user ID")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True

class UserInResponse(BaseModel):
    """Wrapper for user response with additional metadata."""
    user: User
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "role": "user",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            }
        }
