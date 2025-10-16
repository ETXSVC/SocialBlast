from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, 
    ForeignKey, Text, JSON, Enum, Table, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func

from .base import Base

class PostStatus(str, PyEnum):
    """Status of a scheduled post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELED = "canceled"

class PostContentType(str, PyEnum):
    """Type of post content."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"
    LINK = "link"
    POLL = "poll"

# Association table for many-to-many relationship between posts and media
post_media = Table(
    'post_media',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('media_id', Integer, ForeignKey('media.id', ondelete='CASCADE'), primary_key=True),
    Column('order', Integer, default=0, nullable=False),
    Column('created_at', DateTime, server_default=func.now(), nullable=False)
)

class Post(Base):
    """A post that can be published to multiple social media platforms."""
    __tablename__ = "posts"
    
    # User who created the post
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Post content
    content = Column(Text, nullable=True)  # Main post text/caption
    content_type = Column(Enum(PostContentType), nullable=False)
    link_url = Column(String(500), nullable=True)  # For link posts
    
    # Scheduling
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    is_draft = Column(Boolean, default=True, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Metadata
    tags = Column(ARRAY(String(50)), default=[], nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="posts")
    media: Mapped[List["Media"]] = relationship(
        "Media",
        secondary=post_media,
        back_populates="posts"
    )
    platforms: Mapped[List["PostPlatform"]] = relationship(
        "PostPlatform", 
        back_populates="post",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Post {self.id} - {self.content_type} - {self.status}>"
    
    @property
    def is_scheduled(self) -> bool:
        """Check if the post is scheduled for future publishing."""
        return self.status == PostStatus.SCHEDULED and self.scheduled_at
    
    @property
    def is_published(self) -> bool:
        """Check if the post has been published."""
        return self.status == PostStatus.PUBLISHED and self.published_at is not None
    
    @property
    def can_edit(self) -> bool:
        """Check if the post can be edited."""
        return self.status in [PostStatus.DRAFT, PostStatus.SCHEDULED]

class PostPlatform(Base):
    """Tracks a post's status on each platform it was published to."""
    __tablename__ = "post_platforms"
    
    post_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Platform-specific post ID
    platform_post_id = Column(String(255), nullable=True)
    platform_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Engagement metrics
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    
    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="platforms")
    account: Mapped["SocialAccount"] = relationship("SocialAccount", back_populates="posts")
    
    def __repr__(self):
        return f"<PostPlatform {self.id} - Post:{self.post_id} - Account:{self.account_id}>"
    
    @property
    def is_published(self) -> bool:
        """Check if the post has been published to this platform."""
        return self.status == PostStatus.PUBLISHED and self.published_at is not None

# Indexes for better query performance
Index('ix_posts_user_id', Post.user_id)
Index('ix_posts_status', Post.status)
Index('ix_posts_scheduled_at', Post.scheduled_at)
Index('ix_post_platforms_post_id', PostPlatform.post_id)
Index('ix_post_platforms_account_id', PostPlatform.account_id)
Index('ix_post_platforms_platform_post_id', PostPlatform.platform_post_id)
