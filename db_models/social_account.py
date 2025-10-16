from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, 
    ForeignKey, Text, JSON, Enum, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base

class SocialPlatform(str, PyEnum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    GOOGLE_MY_BUSINESS = "google_my_business"
    SNAPCHAT = "snapchat"

class SocialAccountStatus(str, PyEnum):
    """Status of a social media account connection."""
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"

class SocialAccount(Base):
    """Social media account connected by a user."""
    __tablename__ = "social_accounts"
    
    # User who owns this connection
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Platform details
    platform = Column(Enum(SocialPlatform), nullable=False)
    account_id = Column(String(255), nullable=False)  # Platform's user/account ID
    username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Account status
    status = Column(Enum(SocialAccountStatus), default=SocialAccountStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)
    
    # Profile information
    profile_picture_url = Column(String(500), nullable=True)
    profile_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Statistics
    followers_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    media_count = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="social_accounts")
    tokens: Mapped[List["SocialAccountToken"]] = relationship(
        "SocialAccountToken", 
        back_populates="account",
        cascade="all, delete-orphan"
    )
    posts: Mapped[List["PostPlatform"]] = relationship(
        "PostPlatform", 
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<SocialAccount {self.platform}:{self.username or self.account_id}>"
    
    @property
    def is_connected(self) -> bool:
        """Check if the account is connected and active."""
        return self.status == SocialAccountStatus.CONNECTED and self.is_active
    
    @property
    def access_token(self) -> Optional["SocialAccountToken"]:
        """Get the active access token for this account."""
        for token in self.tokens:
            if token.token_type == "access" and not token.is_expired:
                return token
        return None
    
    @property
    def refresh_token(self) -> Optional["SocialAccountToken"]:
        """Get the refresh token for this account."""
        for token in self.tokens:
            if token.token_type == "refresh" and not token.is_expired:
                return token
        return None

class SocialAccountToken(Base):
    """OAuth tokens for social media accounts."""
    __tablename__ = "social_account_tokens"
    
    # Account this token belongs to
    account_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Token details
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_secret = Column(Text, nullable=True)  # For OAuth 1.0a
    expires_at = Column(DateTime, nullable=True)
    
    # Token metadata
    scopes = Column(JSON, default=list, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    account: Mapped["SocialAccount"] = relationship("SocialAccount", back_populates="tokens")
    
    def __repr__(self):
        return f"<SocialAccountToken {self.token_type} for account {self.account_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_refreshable(self) -> bool:
        """Check if the token can be refreshed."""
        return bool(self.refresh_token) and not self.is_expired

# Indexes for better query performance
Index('ix_social_accounts_user_platform', SocialAccount.user_id, SocialAccount.platform)
Index('ix_social_accounts_platform_account_id', SocialAccount.platform, SocialAccount.account_id, unique=True)
Index('ix_social_account_tokens_account_id', SocialAccountToken.account_id)
