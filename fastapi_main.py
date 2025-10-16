"""
Main FastAPI Application for Social Media Automation API
Handles image uploads, post scheduling, and platform integrations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import os
from pathlib import Path

# Import our custom modules (these would be in separate files)
# from image_processor import ImageProcessor
# from keyword_extractor import KeywordExtractor
# from social_integrations import FacebookPoster, InstagramPoster
# from database import get_db, User, Post, SocialAccount

app = FastAPI(
    title="Social Media Automation API",
    description="AI-powered multi-platform social media posting API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Initialize processors (would normally use dependency injection)
# image_processor = ImageProcessor(quality=85)
# keyword_extractor = KeywordExtractor()


# Pydantic Models
class ImageUploadResponse(BaseModel):
    image_id: str
    original_filename: str
    file_size_mb: float
    dimensions: tuple
    upload_timestamp: datetime


class KeywordResponse(BaseModel):
    image_id: str
    keywords: List[Dict]
    hashtags: List[str]
    total_detected: int


class PostCreate(BaseModel):
    platforms: List[str] = Field(..., description="List of platforms: 'facebook', 'instagram'")
    post_types: Dict[str, str] = Field(..., description="Platform-specific post types")
    caption: str = Field(..., max_length=2200)
    image_ids: List[str]
    scheduled_for: Optional[datetime] = None
    auto_hashtags: bool = Field(default=True)


class PostResponse(BaseModel):
    post_id: str
    status: str
    platforms: List[str]
    scheduled_for: Optional[datetime]
    created_at: datetime


class PostStatus(BaseModel):
    post_id: str
    status: str
    platform_results: Dict[str, Dict]
    created_at: datetime
    updated_at: datetime


class SocialAccountConnect(BaseModel):
    platform: str
    account_id: str
    account_name: str
    access_token: str
    expires_at: Optional[datetime]


class SocialAccountResponse(BaseModel):
    id: str
    platform: str
    account_name: str
    connected_at: datetime
    status: str


# Dependency for API key validation
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Bearer token"""
    token = credentials.credentials
    
    # TODO: Implement actual API key validation against database
    # user = await get_user_by_api_key(token)
    # if not user:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    # return user
    
    # Placeholder for development
    if token != "dev_api_key_12345":
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {"user_id": "dev_user_1", "tier": "pro"}


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "Social Media Automation API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow()
    }


@app.post("/api/v1/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user: dict = Depends(verify_api_key)
):
    """
    Upload an image for processing
    
    - Accepts: JPG, PNG, GIF
    - Max size: 10MB
    - Returns: Image ID for use in post creation
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate unique ID
    image_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    save_path = UPLOAD_DIR / f"{image_id}{file_extension}"
    
    # Save file
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > 10:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    with open(save_path, "wb") as f:
        f.write(content)
    
    # Get image dimensions (would use PIL in production)
    # from PIL import Image
    # img = Image.open(save_path)
    # dimensions = img.size
    dimensions = (0, 0)  # Placeholder
    
    # TODO: Store in database
    # await db.images.create({
    #     "id": image_id,
    #     "user_id": user["user_id"],
    #     "original_filename": file.filename,
    #     "storage_path": str(save_path),
    #     "file_size_mb": file_size_mb,
    #     "uploaded_at": datetime.utcnow()
    # })
    
    return ImageUploadResponse(
        image_id=image_id,
        original_filename=file.filename,
        file_size_mb=round(file_size_mb, 2),
        dimensions=dimensions,
        upload_timestamp=datetime.utcnow()
    )


@app.get("/api/v1/keywords/{image_id}", response_model=KeywordResponse)
async def extract_keywords(
    image_id: str,
    max_keywords: int = 10,
    user: dict = Depends(verify_api_key)
):
    """
    Extract AI-powered keywords from an uploaded image
    
    - Uses Google Vision API
    - Returns: Top keywords with confidence scores
    - Auto-generates hashtags
    """
    # Find image file
    image_files = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not image_files:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = image_files[0]
    
    # Extract keywords (would use KeywordExtractor in production)
    # result = keyword_extractor.extract_with_context(
    #     str(image_path),
    #     max_keywords=max_keywords
    # )
    
    # Placeholder response
    result = {
        "keywords": [
            {"keyword": "sunset", "score": 0.95, "sources": ["label", "web_entity"]},
            {"keyword": "beach", "score": 0.88, "sources": ["label"]},
            {"keyword": "ocean", "score": 0.82, "sources": ["label", "object"]}
        ],
        "hashtags": ["#Sunset", "#Beach", "#Ocean"],
        "total_detected": 15
    }
    
    return KeywordResponse(
        image_id=image_id,
        keywords=result["keywords"],
        hashtags=result["hashtags"],
        total_detected=result["total_detected"]
    )


@app.post("/api/v1/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_api_key)
):
    """
    Create a new social media post
    
    - Supports: Facebook, Instagram
    - Can schedule for future posting
    - Auto-generates hashtags from image keywords
    - Processes images for each platform automatically
    """
    # Validate platforms
    allowed_platforms = ["facebook", "instagram"]
    for platform in post_data.platforms:
        if platform not in allowed_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}"
            )
    
    # Validate images exist
    for image_id in post_data.image_ids:
        image_files = list(UPLOAD_DIR.glob(f"{image_id}.*"))
        if not image_files:
            raise HTTPException(
                status_code=404,
                detail=f"Image not found: {image_id}"
            )
    
    # Generate post ID
    post_id = str(uuid.uuid4())
    
    # Determine if immediate or scheduled
    is_scheduled = post_data.scheduled_for is not None
    status = "scheduled" if is_scheduled else "processing"
    
    # TODO: Store post in database
    # await db.posts.create({
    #     "id": post_id,
    #     "user_id": user["user_id"],
    #     "platforms": post_data.platforms,
    #     "caption": post_data.caption,
    #     "image_ids": post_data.image_ids,
    #     "scheduled_for": post_data.scheduled_for,
    #     "status": status,
    #     "created_at": datetime.utcnow()
    # })
    
    # Add background task to process and post
    if not is_scheduled:
        background_tasks.add_task(
            process_and_post,
            post_id,
            post_data,
            user["user_id"]
        )
    
    return PostResponse(
        post_id=post_id,
        status=status,
        platforms=post_data.platforms,
        scheduled_for=post_data.scheduled_for,
        created_at=datetime.utcnow()
    )


@app.get("/api/v1/posts/{post_id}", response_model=PostStatus)
async def get_post_status(
    post_id: str,
    user: dict = Depends(verify_api_key)
):
    """
    Get status of a post
    
    - Returns: Current status and platform-specific results
    - Status: processing, scheduled, posted, failed
    """
    # TODO: Fetch from database
    # post = await db.posts.get(post_id)
    # if not post or post.user_id != user["user_id"]:
    #     raise HTTPException(status_code=404, detail="Post not found")
    
    # Placeholder response
    return PostStatus(
        post_id=post_id,
        status="posted",
        platform_results={
            "facebook": {
                "status": "success",
                "post_id": "fb_123456789",
                "url": "https://facebook.com/posts/123456789"
            },
            "instagram": {
                "status": "success",
                "post_id": "ig_987654321",
                "url": "https://instagram.com/p/987654321"
            }
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@app.delete("/api/v1/posts/{post_id}")
async def cancel_post(
    post_id: str,
    user: dict = Depends(verify_api_key)
):
    """
    Cancel a scheduled post
    
    - Only works for scheduled posts that haven't been published yet
    """
    # TODO: Implement cancellation logic
    # post = await db.posts.get(post_id)
    # if not post or post.user_id != user["user_id"]:
    #     raise HTTPException(status_code=404, detail="Post not found")
    # 
    # if post.status != "scheduled":
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Can only cancel scheduled posts"
    #     )
    # 
    # await db.posts.update(post_id, {"status": "cancelled"})
    
    return {"message": "Post cancelled successfully", "post_id": post_id}


@app.post("/api/v1/auth/connect", response_model=SocialAccountResponse)
async def connect_social_account(
    account_data: SocialAccountConnect,
    user: dict = Depends(verify_api_key)
):
    """
    Connect a social media account
    
    - Platform: facebook or instagram
    - Requires OAuth access token from Meta
    """
    # Validate platform
    if account_data.platform not in ["facebook", "instagram"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    # TODO: Validate token with platform API
    # if account_data.platform == "facebook":
    #     is_valid = await validate_facebook_token(account_data.access_token)
    # else:
    #     is_valid = await validate_instagram_token(account_data.access_token)
    
    account_id = str(uuid.uuid4())
    
    # TODO: Store in database (encrypted token)
    # await db.social_accounts.create({
    #     "id": account_id,
    #     "user_id": user["user_id"],
    #     "platform": account_data.platform,
    #     "account_id": account_data.account_id,
    #     "account_name": account_data.account_name,
    #     "access_token": encrypt(account_data.access_token),
    #     "expires_at": account_data.expires_at,
    #     "connected_at": datetime.utcnow(),
    #     "status": "active"
    # })
    
    return SocialAccountResponse(
        id=account_id,
        platform=account_data.platform,
        account_name=account_data.account_name,
        connected_at=datetime.utcnow(),
        status="active"
    )


@app.get("/api/v1/accounts", response_model=List[SocialAccountResponse])
async def list_connected_accounts(user: dict = Depends(verify_api_key)):
    """
    List all connected social media accounts
    """
    # TODO: Fetch from database
    # accounts = await db.social_accounts.find({"user_id": user["user_id"]})
    
    # Placeholder response
    return [
        SocialAccountResponse(
            id="acc_1",
            platform="facebook",
            account_name="My Business Page",
            connected_at=datetime.utcnow(),
            status="active"
        )
    ]


# ==================== BACKGROUND TASKS ====================

async def process_and_post(post_id: str, post_data: PostCreate, user_id: str):
    """
    Background task to process images and post to platforms
    
    This would:
    1. Process images for each platform
    2. Extract keywords if auto_hashtags is enabled
    3. Post to each platform via their APIs
    4. Update database with results
    """
    try:
        # Update status
        # await db.posts.update(post_id, {"status": "processing"})
        
        for platform in post_data.platforms:
            post_type = post_data.post_types.get(platform, "feed")
            
            # Process each image
            for image_id in post_data.image_ids:
                image_path = list(UPLOAD_DIR.glob(f"{image_id}.*"))[0]
                
                # Process image for platform
                # processed = image_processor.process_for_platform(
                #     str(image_path),
                #     platform,
                #     post_type,
                #     str(PROCESSED_DIR / f"{image_id}_{platform}_{post_type}.jpg")
                # )
                
                # Post to platform
                # if platform == "facebook":
                #     result = await facebook_poster.post(
                #         image_path=processed["output_path"],
                #         caption=post_data.caption,
                #         user_id=user_id
                #     )
                # elif platform == "instagram":
                #     result = await instagram_poster.post(
                #         image_path=processed["output_path"],
                #         caption=post_data.caption,
                #         user_id=user_id
                #     )
                
                pass
        
        # Update status to posted
        # await db.posts.update(post_id, {"status": "posted"})
        
    except Exception as e:
        # Log error and update status
        # await db.posts.update(post_id, {"status": "failed", "error": str(e)})
        print(f"Error processing post {post_id}: {str(e)}")


# ==================== STARTUP & SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting Social Media Automation API...")
    # TODO: Initialize database connection, Redis, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down API...")
    # TODO: Close database connections, cleanup temp files


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)