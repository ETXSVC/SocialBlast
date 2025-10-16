from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, DateTime, 
    ForeignKey, Text, JSON, Enum, Index, LargeBinary
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, BYTEA
from sqlalchemy.sql import func

from .base import Base

class MediaType(str, PyEnum):
    """Type of media file."""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    OTHER = "other"

class MediaStatus(str, PyEnum):
    """Status of media processing."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"

class MediaVariantType(str, PyEnum):
    """Type of media variant (different sizes/formats)."""
    ORIGINAL = "original"
    THUMBNAIL = "thumbnail"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HD = "hd"
    STORY = "story"
    PROFILE = "profile"

class Media(Base):
    """A media file that can be used in posts."""
    __tablename__ = "media"
    
    # User who uploaded the media
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Media details
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # In bytes
    mime_type = Column(String(100), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    
    # Storage details
    storage_provider = Column(String(50), default="local", nullable=False)
    storage_path = Column(String(500), nullable=False)
    storage_url = Column(String(500), nullable=True)  # Public URL if stored externally
    
    # Media properties
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Float, nullable=True)  # For videos/audio in seconds
    aspect_ratio = Column(Float, nullable=True)  # width/height
    
    # Status
    status = Column(Enum(MediaStatus), default=MediaStatus.UPLOADING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(ARRAY(String(50)), default=[], nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="media")
    variants: Mapped[List["MediaVariant"]] = relationship(
        "MediaVariant", 
        back_populates="media",
        cascade="all, delete-orphan"
    )
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        secondary="post_media",
        back_populates="media"
    )
    
    def __repr__(self):
        return f"<Media {self.id} - {self.media_type} - {self.file_name}>"
    
    @property
    def is_image(self) -> bool:
        """Check if the media is an image."""
        return self.media_type in [MediaType.IMAGE, MediaType.GIF]
    
    @property
    def is_video(self) -> bool:
        """Check if the media is a video."""
        return self.media_type == MediaType.VIDEO
    
    @property
    def is_ready(self) -> bool:
        """Check if the media is ready to be used."""
        return self.status == MediaStatus.READY
    
    @property
    def thumbnail_url(self) -> Optional[str]:
        """Get the URL of the thumbnail variant if available."""
        for variant in self.variants:
            if variant.variant_type == MediaVariantType.THUMBNAIL:
                return variant.url
        return self.storage_url

class MediaVariant(Base):
    """Different variants of a media file (e.g., thumbnails, different resolutions)."""
    __tablename__ = "media_variants"
    
    media_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Variant details
    variant_type = Column(Enum(MediaVariantType), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(BigInteger, nullable=False)  # In bytes
    
    # Storage details
    storage_provider = Column(String(50), default="local", nullable=False)
    storage_path = Column(String(500), nullable=False)
    url = Column(String(500), nullable=True)  # Public URL if stored externally
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)  # In seconds
    
    # Relationships
    media: Mapped["Media"] = relationship("Media", back_populates="variants")
    
    def __repr__(self):
        return f"<MediaVariant {self.id} - {self.variant_type} for Media {self.media_id}>"

# Indexes for better query performance
Index('ix_media_user_id', Media.user_id)
Index('ix_media_media_type', Media.media_type)
Index('ix_media_status', Media.status)
Index('ix_media_created_at', Media.created_at)
Index('ix_media_variants_media_id', MediaVariant.media_id)
Index('ix_media_variants_variant_type', MediaVariant.variant_type)
