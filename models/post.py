from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from .social_account import SocialPlatform

class PostStatus(str, Enum):
    """Status of a scheduled post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELED = "canceled"

class PostContentType(str, Enum):
    """Type of post content."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"

class PostBase(BaseModel):
    """Base model for post data."""
    content: str = Field(..., min_length=1, max_length=2200, description="Post content text")
    content_type: PostContentType = Field(..., description="Type of post content")
    scheduled_at: Optional[datetime] = Field(
        None,
        description="When to publish the post. If not provided, will be published immediately."
    )
    platforms: List[SocialPlatform] = Field(
        ..., 
        min_items=1,
        description="List of platforms to post to"
    )
    media_ids: List[int] = Field(
        default_factory=list,
        description="List of media IDs to include in the post"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional platform-specific metadata"
    )
    is_draft: bool = Field(
        default=False,
        description="Whether this is a draft post"
    )
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v
    
    @validator('media_ids')
    def validate_media_ids(cls, v, values):
        content_type = values.get('content_type')
        if content_type in [PostContentType.IMAGE, PostContentType.VIDEO] and not v:
            raise ValueError(f"{content_type.value} posts require at least one media item")
        if content_type == PostContentType.CAROUSEL and len(v) < 2:
            raise ValueError("Carousel posts require at least 2 media items")
        if content_type == PostContentType.TEXT and v:
            raise ValueError("Text posts cannot have media items")
        return v

class PostCreate(PostBase):
    """Model for creating a new post."""
    pass

class PostUpdate(BaseModel):
    """Model for updating an existing post."""
    content: Optional[str] = Field(None, min_length=1, max_length=2200, description="Updated post content")
    scheduled_at: Optional[datetime] = Field(None, description="New scheduled time")
    status: Optional[PostStatus] = Field(None, description="New post status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v

class PostInDB(PostBase):
    """Database model for post."""
    id: int = Field(..., description="Unique post ID")
    user_id: int = Field(..., description="ID of the user who created the post")
    status: PostStatus = Field(..., description="Current status of the post")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    published_at: Optional[datetime] = Field(None, description="When the post was published")
    
    class Config:
        orm_mode = True

class Post(PostInDB):
    """Response model for post data."""
    platform_statuses: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Status of the post on each platform"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "content": "Check out our latest product! #new #productlaunch",
                "content_type": "image",
                "status": "scheduled",
                "platforms": ["instagram", "facebook"],
                "media_ids": [1, 2],
                "is_draft": False,
                "scheduled_at": "2023-12-25T09:00:00",
                "created_at": "2023-12-20T10:30:00",
                "updated_at": "2023-12-20T10:30:00",
                "published_at": None,
                "platform_statuses": {
                    "instagram": {
                        "status": "scheduled",
                        "post_id": "17841405793087218",
                        "url": "https://www.instagram.com/p/ABC123/"
                    },
                    "facebook": {
                        "status": "scheduled",
                        "post_id": "1234567890_1234567890",
                        "url": "https://www.facebook.com/1234567890/posts/1234567890"
                    }
                }
            }
        }

class PostInResponse(BaseModel):
    """Wrapper for post response with additional metadata."""
    post: Post
    
    class Config:
        schema_extra = {
            "example": {
                "post": {
                    "id": 1,
                    "user_id": 1,
                    "content": "Check out our latest product! #new #productlaunch",
                    "content_type": "image",
                    "status": "scheduled",
                    "platforms": ["instagram", "facebook"],
                    "media_ids": [1, 2],
                    "is_draft": False,
                    "scheduled_at": "2023-12-25T09:00:00",
                    "created_at": "2023-12-20T10:30:00",
                    "updated_at": "2023-12-20T10:30:00",
                    "published_at": None,
                    "platform_statuses": {
                        "instagram": {
                            "status": "scheduled",
                            "post_id": "17841405793087218",
                            "url": "https://www.instagram.com/p/ABC123/"
                        }
                    }
                }
            }
        }
