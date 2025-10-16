"""
Meta OAuth 2.0 Implementation
Handles secure authentication flow for Facebook and Instagram
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import secrets
import hashlib
import os


class OAuthConfig:
    """OAuth configuration"""
    # Meta App credentials (store in environment variables)
    APP_ID = os.getenv('META_APP_ID', 'your_app_id')
    APP_SECRET = os.getenv('META_APP_SECRET', 'your_app_secret')
    
    # OAuth endpoints
    FACEBOOK_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
    FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
    FACEBOOK_DEBUG_URL = "https://graph.facebook.com/v21.0/debug_token"
    
    # Callback URL (must match Meta App settings)
    REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'https://yourdomain.com/api/v1/auth/callback')
    
    # Required permissions
    FACEBOOK_SCOPES = [
        'pages_show_list',          # List user's pages
        'pages_read_engagement',    # Read page engagement
        'pages_manage_posts',       # Create posts
        'pages_manage_engagement',  # Manage comments/reactions
        'instagram_basic',          # Basic Instagram access
        'instagram_content_publish' # Publish Instagram content
    ]
    
    # Session storage (use Redis in production)
    _sessions = {}


class OAuthState(BaseModel):
    """OAuth state for CSRF protection"""
    state: str
    code_verifier: Optional[str] = None
    platform: str
    user_id: str
    created_at: datetime


class TokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    token_type: str
    expires_in: int
    granted_scopes: List[str]


class MetaOAuthHandler:
    """
    Handles Meta (Facebook/Instagram) OAuth 2.0 flow
    Implements PKCE for enhanced security
    """
    
    def __init__(self):
        self.config = OAuthConfig()
    
    def generate_authorization_url(
        self,
        user_id: str,
        platform: str = 'facebook',
        use_pkce: bool = True
    ) -> Dict:
        """
        Generate OAuth authorization URL
        
        Args:
            user_id: Internal user ID
            platform: 'facebook' or 'instagram'
            use_pkce: Use PKCE flow for enhanced security
            
        Returns:
            Dict with authorization URL and state
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session (use Redis in production)
        oauth_state = OAuthState(
            state=state,
            platform=platform,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        # Generate PKCE parameters if enabled
        code_verifier = None
        code_challenge = None
        
        if use_pkce:
            code_verifier = secrets.token_urlsafe(64)
            code_challenge = self._generate_code_challenge(code_verifier)
            oauth_state.code_verifier = code_verifier
        
        # Store state
        self.config._sessions[state] = oauth_state.dict()
        
        # Build authorization URL
        params = {
            'client_id': self.config.APP_ID,
            'redirect_uri': self.config.REDIRECT_URI,
            'state': state,
            'scope': ','.join(self.config.FACEBOOK_SCOPES),
            'response_type': 'code'
        }
        
        if code_challenge:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.config.FACEBOOK_AUTH_URL}?{query_string}"
        
        return {
            'authorization_url': auth_url,
            'state': state
        }
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        error: Optional[str] = None,
        error_description: Optional[str] = None
    ) -> Dict:
        """
        Handle OAuth callback
        
        Args:
            code: Authorization code from Meta
            state: State parameter for CSRF validation
            error: Error code if authorization failed
            error_description: Error description
            
        Returns:
            Dict with access token and account info
        """
        # Check for errors
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth error: {error} - {error_description}"
            )
        
        # Validate state
        oauth_state = self.config._sessions.get(state)
        if not oauth_state:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )
        
        # Check state expiration (15 minutes)
        created_at = datetime.fromisoformat(oauth_state['created_at'])
        if datetime.utcnow() - created_at > timedelta(minutes=15):
            raise HTTPException(
                status_code=400,
                detail="OAuth state expired"
            )
        
        # Exchange code for access token
        token_data = await self._exchange_code_for_token(
            code,
            oauth_state.get('code_verifier')
        )
        
        # Get user's Facebook pages
        pages = await self._get_user_pages(token_data['access_token'])
        
        # Get Instagram accounts (if available)
        instagram_accounts = []
        for page in pages:
            ig_account = await self._get_instagram_account(
                page['id'],
                page['access_token']
            )
            if ig_account:
                instagram_accounts.append(ig_account)
        
        # Clean up session
        del self.config._sessions[state]
        
        return {
            'user_id': oauth_state['user_id'],
            'access_token': token_data['access_token'],
            'expires_in': token_data['expires_in'],
            'facebook_pages': pages,
            'instagram_accounts': instagram_accounts,
            'granted_scopes': token_data.get('granted_scopes', [])
        }
    
    async def _exchange_code_for_token(
        self,
        code: str,
        code_verifier: Optional[str] = None
    ) -> Dict:
        """Exchange authorization code for access token"""
        params = {
            'client_id': self.config.APP_ID,
            'client_secret': self.config.APP_SECRET,
            'redirect_uri': self.config.REDIRECT_URI,
            'code': code
        }
        
        if code_verifier:
            params['code_verifier'] = code_verifier
        
        try:
            response = requests.get(
                self.config.FACEBOOK_TOKEN_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Get granted scopes
            debug_data = await self._debug_token(data['access_token'])
            
            return {
                'access_token': data['access_token'],
                'token_type': data.get('token_type', 'bearer'),
                'expires_in': data.get('expires_in', 5184000),  # Default 60 days
                'granted_scopes': debug_data.get('scopes', [])
            }
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code for token: {str(e)}"
            )
    
    async def _get_user_pages(self, access_token: str) -> List[Dict]:
        """Get user's Facebook pages"""
        url = "https://graph.facebook.com/v21.0/me/accounts"
        params = {
            'access_token': access_token,
            'fields': 'id,name,access_token,category,fan_count'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pages: {str(e)}")
            return []
    
    async def _get_instagram_account(
        self,
        page_id: str,
        page_access_token: str
    ) -> Optional[Dict]:
        """Get Instagram Business Account connected to a Facebook Page"""
        url = f"https://graph.facebook.com/v21.0/{page_id}"
        params = {
            'fields': 'instagram_business_account{id,username,name,profile_picture_url,followers_count}',
            'access_token': page_access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            ig_account = data.get('instagram_business_account')
            
            if ig_account:
                ig_account['page_id'] = page_id
                ig_account['page_access_token'] = page_access_token
                return ig_account
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Instagram account: {str(e)}")
            return None
    
    async def _debug_token(self, access_token: str) -> Dict:
        """Debug access token to get metadata"""
        params = {
            'input_token': access_token,
            'access_token': f"{self.config.APP_ID}|{self.config.APP_SECRET}"
        }
        
        try:
            response = requests.get(
                self.config.FACEBOOK_DEBUG_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
            
        except requests.exceptions.RequestException as e:
            print(f"Error debugging token: {str(e)}")
            return {}
    
    async def refresh_token(self, access_token: str) -> Dict:
        """
        Exchange short-lived token for long-lived token
        Long-lived tokens last ~60 days
        """
        url = "https://graph.facebook.com/v21.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.config.APP_ID,
            'client_secret': self.config.APP_SECRET,
            'fb_exchange_token': access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'access_token': data['access_token'],
                'token_type': data.get('token_type', 'bearer'),
                'expires_in': data.get('expires_in', 5184000)
            }
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh token: {str(e)}"
            )
    
    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = code_challenge.hex()
        return code_challenge


# FastAPI Router for OAuth endpoints
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
oauth_handler = MetaOAuthHandler()


@router.get("/connect/{platform}")
async def initiate_oauth(
    platform: str,
    user_id: str,  # In production, get from authenticated session
):
    """
    Initiate OAuth flow
    
    - **platform**: facebook or instagram
    - Redirects user to Meta authorization page
    """
    if platform not in ['facebook', 'instagram']:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    result = oauth_handler.generate_authorization_url(user_id, platform)
    
    # Redirect user to authorization URL
    return RedirectResponse(url=result['authorization_url'])


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    OAuth callback endpoint
    
    - Receives authorization code from Meta
    - Exchanges code for access token
    - Returns connected accounts
    """
    try:
        result = await oauth_handler.handle_callback(
            code=code,
            state=state,
            error=error,
            error_description=error_description
        )
        
        # Store accounts in database
        # await db.store_social_accounts(result)
        
        return {
            'success': True,
            'message': 'Successfully connected accounts',
            'facebook_pages': len(result['facebook_pages']),
            'instagram_accounts': len(result['instagram_accounts'])
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_access_token(access_token: str):
    """
    Refresh short-lived token to long-lived token
    
    - Extends token lifetime to ~60 days
    """
    try:
        result = await oauth_handler.refresh_token(access_token)
        return result
    except HTTPException as e:
        raise e


@router.delete("/disconnect/{account_id}")
async def disconnect_account(
    account_id: str,
    user_id: str  # Get from authenticated session
):
    """
    Disconnect a social media account
    
    - Removes account from database
    - Revokes access token (optional)
    """
    # TODO: Implement account disconnection
    # await db.delete_social_account(account_id, user_id)
    
    return {'success': True, 'message': 'Account disconnected'}


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_oauth():
        handler = MetaOAuthHandler()
        
        # Generate authorization URL
        auth_data = handler.generate_authorization_url(
            user_id="user_123",
            platform="facebook"
        )
        
        print(f"Authorization URL: {auth_data['authorization_url']}")
        print(f"State: {auth_data['state']}")
        
        # User would visit the URL, authorize, and be redirected back
        # Then you'd call handle_callback with the code and state
    
    asyncio.run(test_oauth())
