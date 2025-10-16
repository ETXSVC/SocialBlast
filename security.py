import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Generator
from pathlib import Path
import shutil

from fastapi import HTTPException, status, UploadFile, Request, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from werkzeug.utils import secure_filename

from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Authentication
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get the current user from the JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    try:
        payload = await verify_token(token)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials"
        )

def secure_filename_custom(filename: str) -> str:
    ""
    Sanitize the filename to prevent directory traversal and other security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename with a secure prefix
    """
    # Generate a random prefix to prevent predictable filenames
    prefix = secrets.token_hex(8)
    secure_name = secure_filename(filename)
    return f"{prefix}_{secure_name}"

async def save_upload_file(upload_file: UploadFile, upload_dir: Path) -> Path:
    """
    Save an uploaded file securely.
    
    Args:
        upload_file: Uploaded file
        upload_dir: Directory to save the file in
        
    Returns:
        Path: Path to the saved file
        
    Raises:
        HTTPException: If the file is too large or invalid
    """
    # Ensure upload directory exists
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Secure the filename
    filename = secure_filename_custom(upload_file.filename)
    file_path = upload_dir / filename
    
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Save file in chunks to handle large files
    try:
        with open(file_path, "wb") as buffer:
            # Read file in chunks to handle large files
            while True:
                chunk = await upload_file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                buffer.write(chunk)
                
                # Check file size during upload
                if buffer.tell() > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    buffer.close()
                    file_path.unlink()  # Delete the file if too large
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                    
    except IOError as e:
        if file_path.exists():
            file_path.unlink()  # Clean up if something went wrong
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    return file_path
