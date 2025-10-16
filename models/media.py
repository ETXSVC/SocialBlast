from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl

class MediaType(str, Enum):
    """Type of media file."""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    DOCUMENT = "document"

class MediaStatus(str, Enum):
    """Status of media processing."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class MediaBase(BaseModel):
    """Base model for media data."""
    title: str = Field(..., min_length=1, max_length=255, description="Media title")
    description: Optional[str] = Field(None, max_length=1000, description="Media description")
    media_type: MediaType = Field(..., description="Type of media")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and search"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional media metadata"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

class MediaCreate(MediaBase):
    """Model for creating a new media entry."""
    file_path: str = Field(..., description="Path to the uploaded file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

class MediaUpdate(BaseModel):
    """Model for updating media metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated media title")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class MediaInDB(MediaBase):
    """Database model for media."""
    id: int = Field(..., description="Unique media ID")
    user_id: int = Field(..., description="ID of the user who uploaded the media")
    file_path: str = Field(..., description="Path to the stored file")
    file_url: str = Field(..., description="Public URL to access the media")
    thumbnail_url: Optional[str] = Field(None, description="URL to the media thumbnail")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    width: Optional[int] = Field(None, description="Media width in pixels (for images/videos)")
    height: Optional[int] = Field(None, description="Media height in pixels (for images/videos)")
    duration: Optional[float] = Field(None, description="Media duration in seconds (for videos/audio)")
    status: MediaStatus = Field(..., description="Current processing status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        orm_mode = True

class Media(MediaInDB):
    """Response model for media data."""
    preview_url: Optional[HttpUrl] = Field(
        None,
        description="URL for previewing the media (e.g., lower resolution)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Product Launch",
                "description": "Our new product line launching soon!",
                "media_type": "image",
                "file_path": "uploads/2023/12/01/abc123.jpg",
                "file_url": "https://storage.example.com/uploads/2023/12/01/abc123.jpg",
                "thumbnail_url": "https://storage.example.com/thumbnails/2023/12/01/abc123.jpg",
                "preview_url": "https://storage.example.com/previews/2023/12/01/abc123.jpg",
                "file_size": 1234567,
                "mime_type": "image/jpeg",
                "width": 1920,
                "height": 1080,
                "duration": None,
                "status": "ready",
                "tags": ["product", "launch", "2023"],
                "created_at": "2023-12-01T10:30:00",
                "updated_at": "2023-12-01T10:31:30",
                "metadata": {
                    "format": "JPEG",
                    "color_profile": "sRGB",
                    "camera": "Canon EOS R5",
                    "lens": "RF 24-70mm f/2.8L IS USM"
                }
            }
        }

class MediaInResponse(BaseModel):
    """Wrapper for media response with additional metadata."""
    media: Media
    
    class Config:
        schema_extra = {
            "example": {
                "media": {
                    "id": 1,
                    "user_id": 1,
                    "title": "Product Launch",
                    "description": "Our new product line launching soon!",
                    "media_type": "image",
                    "file_url": "https://storage.example.com/uploads/2023/12/01/abc123.jpg",
                    "thumbnail_url": "https://storage.example.com/thumbnails/2023/12/01/abc123.jpg",
                    "preview_url": "https://storage.example.com/previews/2023/12/01/abc123.jpg",
                    "status": "ready",
                    "created_at": "2023-12-01T10:30:00"
                }
            }
        }

class MediaUploadResponse(BaseModel):
    """Response model for media upload."""
    upload_id: str = Field(..., description="Temporary upload ID")
    upload_url: str = Field(..., description="URL to upload the file to")
    fields: Dict[str, str] = Field(
        ...,
        description="Form fields to include in the upload request"
    )
    expires_at: datetime = Field(..., description="When the upload URL expires")
    
    class Config:
        schema_extra = {
            "example": {
                "upload_id": "abc123xyz",
                "upload_url": "https://storage.example.com/upload",
                "fields": {
                    "key": "uploads/2023/12/01/abc123.jpg",
                    "Content-Type": "image/jpeg",
                    "x-amz-credential": "...",
                    "Policy": "...",
                    "X-Amz-Signature": "..."
                },
                "expires_at": "2023-12-01T11:30:00"
            }
        }
