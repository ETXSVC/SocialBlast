from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, 
    ForeignKey, Table, Enum, Text, JSON, event
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .base import Base

class UserRole(str, PyEnum):
    """User roles in the system."""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class UserStatus(str, PyEnum):
    """User account status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(100), unique=True, nullable=True)
    verification_sent_at = Column(DateTime, nullable=True)
    
    # Profile
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Settings
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    preferences = Column(JSONB, default=dict, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    
    # Security
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    oauth_accounts: Mapped[List["UserOAuth"]] = relationship(
        "UserOAuth", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    social_accounts: Mapped[List["SocialAccount"]] = relationship(
        "SocialAccount", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    media: Mapped[List["Media"]] = relationship(
        "Media", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Methods
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.email.split('@')[0]
    
    @property
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_superuser(self) -> bool:
        """Check if the user has superuser privileges."""
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

class UserOAuth(Base):
    """OAuth account information for users."""
    __tablename__ = "user_oauth"
    
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # OAuth provider details
    provider = Column(String(50), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(String(1000), nullable=False)
    refresh_token = Column(String(1000), nullable=True)
    expires_at = Column(Integer, nullable=True)  # Token expiration timestamp
    token_type = Column(String(50), nullable=True)
    scope = Column(Text, nullable=True)
    
    # User info from provider
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")
    
    # Constraints
    __table_args__ = (
        # A user can only have one account per provider
        # {'sqlite_autoincrement': True},
        # {'sqlite_with_rowid': False},
    )
    
    def __repr__(self):
        return f"<UserOAuth {self.provider}:{self.provider_user_id}>"

# Update the updated_at timestamp on record update
@event.listens_for(User, 'before_update')
def update_updated_at(mapper, connection, target):
    target.updated_at = func.now()

# Indexes
# Index('ix_users_email_lower', func.lower(User.email), unique=True)
# Index('ix_user_oauth_provider_user_id', UserOAuth.provider, UserOAuth.provider_user_id, unique=True)
