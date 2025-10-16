from datetime import datetime, timedelta
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, 
    ForeignKey, Text, Index, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base

class TokenBlacklist(Base):
    """Blacklisted JWT tokens."""
    __tablename__ = "token_blacklist"
    
    jti = Column(String(36), unique=True, nullable=False, index=True)
    token_type = Column(String(10), nullable=False)  # 'access' or 'refresh'
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    expires_at = Column(DateTime, nullable=False)
    
    # Additional metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="blacklisted_tokens")
    
    def __repr__(self):
        return f"<TokenBlacklist {self.jti}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at

class RefreshToken(Base):
    """Refresh tokens for JWT authentication."""
    __tablename__ = "refresh_tokens"
    
    token = Column(String(500), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken {self.token[:10]}...>"
    
    @property
    def is_active(self) -> bool:
        """Check if the refresh token is active and not expired."""
        now = datetime.utcnow()
        return not self.is_revoked and now < self.expires_at

class PasswordResetToken(Base):
    """Password reset tokens for users."""
    __tablename__ = "password_reset_tokens"
    
    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="password_reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken {self.token[:10]}...>"
    
    @property
    def is_valid(self) -> bool:
        """Check if the password reset token is valid and not expired."""
        now = datetime.utcnow()
        return not self.is_used and now < self.expires_at

class EmailVerificationToken(Base):
    """Email verification tokens for users."""
    __tablename__ = "email_verification_tokens"
    
    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="email_verification_tokens")
    
    def __repr__(self):
        return f"<EmailVerificationToken {self.token[:10]}...>"
    
    @property
    def is_valid(self) -> bool:
        """Check if the email verification token is valid and not expired."""
        now = datetime.utcnow()
        return now < self.expires_at

# Indexes for better query performance
Index('ix_token_blacklist_user_id', TokenBlacklist.user_id)
Index('ix_refresh_tokens_user_id', RefreshToken.user_id)
Index('ix_refresh_tokens_token', RefreshToken.token, postgresql_using='hash')
Index('ix_password_reset_tokens_token', PasswordResetToken.token, postgresql_using='hash')
Index('ix_email_verification_tokens_token', EmailVerificationToken.token, postgresql_using='hash')
