"""
Database Models using SQLAlchemy ORM
PostgreSQL schema for social media automation API
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, 
    Boolean, Text, JSON, ForeignKey, Float, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
from typing import Optional
import os

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/social_media_api'
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Enums
class SubscriptionTier(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PostStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class AccountStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


# Models
class User(Base):
    """User accounts"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    
    subscription_tier = Column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    
    # Usage limits (reset monthly)
    posts_this_month = Column(Integer, default=0)
    images_this_month = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class SocialAccount(Base):
    """Connected social media accounts"""
    __tablename__ = "social_accounts"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    platform = Column(Enum(Platform), nullable=False)
    platform_account_id = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_username = Column(String(255))
    
    # Encrypted access token
    access_token_encrypted = Column(Text, nullable=False)
    token_expires_at = Column(DateTime)
    refresh_token_encrypted = Column(Text)
    
    # Additional metadata
    profile_picture_url = Column(String(512))
    follower_count = Column(Integer)
    
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)
    last_used = Column(DateTime)
    
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")
    post_results = relationship("PostResult", back_populates="social_account")
    
    def __repr__(self):
        return f"<SocialAccount(platform={self.platform}, account={self.account_name})>"


class Image(Base):
    """Uploaded images"""
    __tablename__ = "images"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    storage_url = Column(String(512))  # If using S3/Cloud Storage
    
    # Image metadata
    file_size_mb = Column(Float, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(10))
    
    # AI-extracted keywords
    keywords = Column(JSON)  # Array of keyword objects
    hashtags = Column(JSON)  # Array of hashtag strings
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="images")
    post_images = relationship("PostImage", back_populates="image")
    processed_variants = relationship("ProcessedImage", back_populates="image")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename={self.original_filename})>"


class ProcessedImage(Base):
    """Platform-optimized image variants"""
    __tablename__ = "processed_images"
    
    id = Column(String(36), primary_key=True)
    image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    
    platform = Column(Enum(Platform), nullable=False)
    post_type = Column(String(50), nullable=False)  # feed, story, etc.
    
    storage_path = Column(String(512), nullable=False)
    storage_url = Column(String(512))
    
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size_mb = Column(Float, nullable=False)
    quality = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    image = relationship("Image", back_populates="processed_variants")
    
    def __repr__(self):
        return f"<ProcessedImage(platform={self.platform}, type={self.post_type})>"


class Post(Base):
    """Social media posts"""
    __tablename__ = "posts"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Post content
    caption = Column(Text, nullable=False)
    platforms = Column(JSON, nullable=False)  # Array of platform strings
    post_types = Column(JSON, nullable=False)  # Dict of platform: post_type
    
    # Scheduling
    scheduled_for = Column(DateTime)
    posted_at = Column(DateTime)
    
    # Status
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    error_message = Column(Text)
    
    # Settings
    auto_hashtags = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    post_images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")
    results = relationship("PostResult", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(id={self.id}, status={self.status})>"


class PostImage(Base):
    """Association between posts and images"""
    __tablename__ = "post_images"
    
    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False)
    image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    
    order = Column(Integer, default=0)  # For carousel ordering
    
    # Relationships
    post = relationship("Post", back_populates="post_images")
    image = relationship("Image", back_populates="post_images")
    
    def __repr__(self):
        return f"<PostImage(post={self.post_id}, image={self.image_id})>"


class PostResult(Base):
    """Results of posting to each platform"""
    __tablename__ = "post_results"
    
    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False)
    social_account_id = Column(String(36), ForeignKey("social_accounts.id"), nullable=False)
    
    platform = Column(Enum(Platform), nullable=False)
    platform_post_id = Column(String(255))
    platform_url = Column(String(512))
    
    status = Column(String(50), nullable=False)  # success, failed, pending
    error_message = Column(Text)
    
    # Engagement metrics (optional, can be updated periodically)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    
    posted_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="results")
    social_account = relationship("SocialAccount", back_populates="post_results")
    
    def __repr__(self):
        return f"<PostResult(platform={self.platform}, status={self.status})>"


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)  # login, post_created, token_refresh, etc.
    resource_type = Column(String(50))  # post, image, account
    resource_id = Column(String(36))
    
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    
    details = Column(JSON)  # Additional context
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user={self.user_id})>"


class APIUsage(Base):
    """Track API usage for rate limiting and analytics"""
    __tablename__ = "api_usage"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<APIUsage(endpoint={self.endpoint}, user={self.user_id})>"


# Database helper functions
def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_db():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")


# Migration script
def create_migration():
    """
    Generate Alembic migration
    Run: alembic revision --autogenerate -m "description"
    """
    pass


# Example queries
class DatabaseQueries:
    """Common database queries"""
    
    @staticmethod
    def create_user(db, email: str, password_hash: str, api_key: str) -> User:
        """Create a new user"""
        import uuid
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=password_hash,
            api_key=api_key,
            subscription_tier=SubscriptionTier.FREE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_api_key(db, api_key: str) -> Optional[User]:
        """Get user by API key"""
        return db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
    
    @staticmethod
    def create_social_account(
        db,
        user_id: str,
        platform: Platform,
        account_data: dict,
        access_token_encrypted: str
    ) -> SocialAccount:
        """Create a social account connection"""
        import uuid
        
        account = SocialAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=platform,
            platform_account_id=account_data['id'],
            account_name=account_data['name'],
            account_username=account_data.get('username'),
            access_token_encrypted=access_token_encrypted,
            token_expires_at=account_data.get('expires_at'),
            profile_picture_url=account_data.get('profile_picture_url'),
            follower_count=account_data.get('follower_count'),
            status=AccountStatus.ACTIVE
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def get_active_social_accounts(db, user_id: str, platform: Optional[Platform] = None):
        """Get user's active social accounts"""
        query = db.query(SocialAccount).filter(
            SocialAccount.user_id == user_id,
            SocialAccount.status == AccountStatus.ACTIVE
        )
        
        if platform:
            query = query.filter(SocialAccount.platform == platform)
        
        return query.all()
    
    @staticmethod
    def create_image(db, user_id: str, image_data: dict) -> Image:
        """Create an image record"""
        import uuid
        
        image = Image(
            id=str(uuid.uuid4()),
            user_id=user_id,
            original_filename=image_data['filename'],
            storage_path=image_data['storage_path'],
            storage_url=image_data.get('storage_url'),
            file_size_mb=image_data['file_size_mb'],
            width=image_data.get('width'),
            height=image_data.get('height'),
            format=image_data.get('format')
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    
    @staticmethod
    def update_image_keywords(db, image_id: str, keywords: list, hashtags: list):
        """Update image with AI-extracted keywords"""
        image = db.query(Image).filter(Image.id == image_id).first()
        if image:
            image.keywords = keywords
            image.hashtags = hashtags
            image.is_processed = True
            image.processed_at = datetime.utcnow()
            db.commit()
            db.refresh(image)
        return image
    
    @staticmethod
    def create_post(db, user_id: str, post_data: dict, image_ids: list) -> Post:
        """Create a post with associated images"""
        import uuid
        
        post = Post(
            id=str(uuid.uuid4()),
            user_id=user_id,
            caption=post_data['caption'],
            platforms=post_data['platforms'],
            post_types=post_data['post_types'],
            scheduled_for=post_data.get('scheduled_for'),
            auto_hashtags=post_data.get('auto_hashtags', True),
            status=PostStatus.SCHEDULED if post_data.get('scheduled_for') else PostStatus.PROCESSING
        )
        db.add(post)
        
        # Associate images with post
        for order, image_id in enumerate(image_ids):
            post_image = PostImage(
                id=str(uuid.uuid4()),
                post_id=post.id,
                image_id=image_id,
                order=order
            )
            db.add(post_image)
        
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def get_post(db, post_id: str, user_id: Optional[str] = None) -> Optional[Post]:
        """Get a post by ID"""
        query = db.query(Post).filter(Post.id == post_id)
        
        if user_id:
            query = query.filter(Post.user_id == user_id)
        
        return query.first()
    
    @staticmethod
    def update_post_status(db, post_id: str, status: PostStatus, error_message: Optional[str] = None):
        """Update post status"""
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.status = status
            if error_message:
                post.error_message = error_message
            if status == PostStatus.POSTED:
                post.posted_at = datetime.utcnow()
            db.commit()
            db.refresh(post)
        return post
    
    @staticmethod
    def create_post_result(
        db,
        post_id: str,
        social_account_id: str,
        platform: Platform,
        result_data: dict
    ) -> PostResult:
        """Create a post result record"""
        import uuid
        
        post_result = PostResult(
            id=str(uuid.uuid4()),
            post_id=post_id,
            social_account_id=social_account_id,
            platform=platform,
            platform_post_id=result_data.get('post_id'),
            platform_url=result_data.get('platform_url'),
            status=result_data['status'],
            error_message=result_data.get('error_message'),
            posted_at=datetime.utcnow() if result_data['status'] == 'success' else None
        )
        db.add(post_result)
        db.commit()
        db.refresh(post_result)
        return post_result
    
    @staticmethod
    def get_scheduled_posts(db, before_time: datetime):
        """Get posts scheduled before a certain time"""
        return db.query(Post).filter(
            Post.status == PostStatus.SCHEDULED,
            Post.scheduled_for <= before_time
        ).all()
    
    @staticmethod
    def log_audit_event(
        db,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Log an audit event"""
        import uuid
        
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def log_api_usage(
        db,
        user_id: str,
        endpoint: str,
        method: str,
        response_status: int,
        response_time_ms: int
    ):
        """Log API usage"""
        import uuid
        
        usage = APIUsage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            response_status=response_status,
            response_time_ms=response_time_ms
        )
        db.add(usage)
        db.commit()
    
    @staticmethod
    def get_user_stats(db, user_id: str) -> dict:
        """Get user statistics"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {}
        
        total_posts = db.query(Post).filter(Post.user_id == user_id).count()
        total_images = db.query(Image).filter(Image.user_id == user_id).count()
        connected_accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == user_id,
            SocialAccount.status == AccountStatus.ACTIVE
        ).count()
        
        return {
            'user_id': user_id,
            'subscription_tier': user.subscription_tier.value,
            'total_posts': total_posts,
            'total_images': total_images,
            'connected_accounts': connected_accounts,
            'posts_this_month': user.posts_this_month,
            'images_this_month': user.images_this_month
        }


# Initialize database when module is run directly
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")
    
    # Example: Create a test user
    db = SessionLocal()
    try:
        test_user = DatabaseQueries.create_user(
            db,
            email="test@example.com",
            password_hash="hashed_password_here",
            api_key="test_api_key_12345"
        )
        print(f"Created test user: {test_user}")
        
        # Get user stats
        stats = DatabaseQueries.get_user_stats(db, test_user.id)
        print(f"User stats: {stats}")
        
    finally:
        db.close()
