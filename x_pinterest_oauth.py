"""
OAuth 2.0 Implementation for X (Twitter) and Pinterest
Handles authentication flows for both platforms
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import requests
import requests_oauthlib
from typing import Dict, Optional
from datetime import datetime, timedelta
import secrets
import hashlib
import base64
import os


class XOAuthConfig:
    """X (Twitter) OAuth configuration"""
    # X App credentials (OAuth 2.0 with PKCE)
    CLIENT_ID = os.getenv('X_CLIENT_ID', 'your_client_id')
    CLIENT_SECRET = os.getenv('X_CLIENT_SECRET', 'your_client_secret')
    
    # OAuth 2.0 endpoints
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    REVOKE_URL = "https://api.twitter.com/2/oauth2/revoke"
    
    # Callback URL
    REDIRECT_URI = os.getenv('X_REDIRECT_URI', 'https://yourdomain.com/api/v1/auth/x/callback')
    
    # Required scopes
    SCOPES = [
        'tweet.read',
        'tweet.write',
        'users.read',
        'offline.access'  # For refresh tokens
    ]
    
    # Session storage
    _sessions = {}


class PinterestOAuthConfig:
    """Pinterest OAuth configuration"""
    # Pinterest App credentials
    APP_ID = os.getenv('PINTEREST_APP_ID', 'your_app_id')
    APP_SECRET = os.getenv('PINTEREST_APP_SECRET', 'your_app_secret')
    
    # OAuth endpoints
    AUTH_URL = "https://www.pinterest.com/oauth/"
    TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
    
    # Callback URL
    REDIRECT_URI = os.getenv('PINTEREST_REDIRECT_URI', 'https://yourdomain.com/api/v1/auth/pinterest/callback')
    
    # Required scopes
    SCOPES = [
        'boards:read',
        'boards:write',
        'pins:read',
        'pins:write',
        'user_accounts:read'
    ]
    
    # Session storage
    _sessions = {}


class XOAuthHandler:
    """
    Handles X (Twitter) OAuth 2.0 flow with PKCE
    """
    
    def __init__(self):
        self.config = XOAuthConfig()
    
    def generate_authorization_url(self, user_id: str) -> Dict:
        """
        Generate X OAuth authorization URL with PKCE
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dict with authorization URL and state
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Store state and verifier
        self.config._sessions[state] = {
            'state': state,
            'code_verifier': code_verifier,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.config.CLIENT_ID,
            'redirect_uri': self.config.REDIRECT_URI,
            'scope': ' '.join(self.config.SCOPES),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.config.AUTH_URL}?{query_string}"
        
        return {
            'authorization_url': auth_url,
            'state': state
        }
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        error: Optional[str] = None
    ) -> Dict:
        """
        Handle X OAuth callback
        
        Args:
            code: Authorization code
            state: State parameter
            error: Error if authorization failed
            
        Returns:
            Dict with access token and user info
        """
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"X OAuth error: {error}"
            )
        
        # Validate state
        session_data = self.config._sessions.get(state)
        if not session_data:
            raise HTTPException(status_code=400, detail="Invalid state")
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(
            code,
            session_data['code_verifier']
        )
        
        # Get user info
        user_info = await self._get_user_info(token_data['access_token'])
        
        # Clean up session
        del self.config._sessions[state]
        
        return {
            'user_id': session_data['user_id'],
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data['expires_in'],
            'x_user_id': user_info.get('id'),
            'x_username': user_info.get('username'),
            'x_name': user_info.get('name'),
            'profile_image': user_info.get('profile_image_url')
        }
    
    async def _exchange_code_for_token(
        self,
        code: str,
        code_verifier: str
    ) -> Dict:
        """Exchange authorization code for access token"""
        # Prepare Basic Auth
        auth_string = f"{self.config.CLIENT_ID}:{self.config.CLIENT_SECRET}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.config.REDIRECT_URI,
            'code_verifier': code_verifier
        }
        
        try:
            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code: {str(e)}"
            )
    
    async def _get_user_info(self, access_token: str) -> Dict:
        """Get X user information"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        params = {
            'user.fields': 'id,name,username,profile_image_url,public_metrics'
        }
        
        try:
            response = requests.get(
                'https://api.twitter.com/2/users/me',
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('data', {})
            
        except requests.exceptions.RequestException as e:
            return {}
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh X access token"""
        auth_string = f"{self.config.CLIENT_ID}:{self.config.CLIENT_SECRET}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh token: {str(e)}"
            )


class PinterestOAuthHandler:
    """
    Handles Pinterest OAuth 2.0 flow
    """
    
    def __init__(self):
        self.config = PinterestOAuthConfig()
    
    def generate_authorization_url(self, user_id: str) -> Dict:
        """
        Generate Pinterest OAuth authorization URL
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dict with authorization URL and state
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state
        self.config._sessions[state] = {
            'state': state,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Build authorization URL
        params = {
            'client_id': self.config.APP_ID,
            'redirect_uri': self.config.REDIRECT_URI,
            'response_type': 'code',
            'scope': ','.join(self.config.SCOPES),
            'state': state
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.config.AUTH_URL}?{query_string}"
        
        return {
            'authorization_url': auth_url,
            'state': state
        }
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        error: Optional[str] = None
    ) -> Dict:
        """
        Handle Pinterest OAuth callback
        
        Args:
            code: Authorization code
            state: State parameter
            error: Error if authorization failed
            
        Returns:
            Dict with access token and user info
        """
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"Pinterest OAuth error: {error}"
            )
        
        # Validate state
        session_data = self.config._sessions.get(state)
        if not session_data:
            raise HTTPException(status_code=400, detail="Invalid state")
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(code)
        
        # Get user info
        user_info = await self._get_user_info(token_data['access_token'])
        
        # Get user's boards
        boards = await self._get_user_boards(token_data['access_token'])
        
        # Clean up session
        del self.config._sessions[state]
        
        return {
            'user_id': session_data['user_id'],
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data.get('expires_in', 0),
            'pinterest_username': user_info.get('username'),
            'pinterest_account_type': user_info.get('account_type'),
            'profile_image': user_info.get('profile_image'),
            'boards': boards
        }
    
    async def _exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.config.REDIRECT_URI,
            'client_id': self.config.APP_ID,
            'client_secret': self.config.APP_SECRET
        }
        
        try:
            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code: {str(e)}"
            )
    
    async def _get_user_info(self, access_token: str) -> Dict:
        """Get Pinterest user information"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(
                'https://api.pinterest.com/v5/user_account',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {}
    
    async def _get_user_boards(self, access_token: str) -> list:
        """Get user's Pinterest boards"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(
                'https://api.pinterest.com/v5/boards',
                headers=headers,
                params={'page_size': 100},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            boards = []
            for board in result.get('items', []):
                boards.append({
                    'id': board.get('id'),
                    'name': board.get('name'),
                    'description': board.get('description'),
                    'pin_count': board.get('pin_count', 0)
                })
            
            return boards
            
        except requests.exceptions.RequestException as e:
            return []
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh Pinterest access token"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.config.APP_ID,
            'client_secret': self.config.APP_SECRET
        }
        
        try:
            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh token: {str(e)}"
            )


# FastAPI Router for X and Pinterest OAuth
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

x_oauth = XOAuthHandler()
pinterest_oauth = PinterestOAuthHandler()


@router.get("/connect/x")
async def initiate_x_oauth(user_id: str):
    """
    Initiate X (Twitter) OAuth flow
    
    - Redirects user to X authorization page
    - Uses OAuth 2.0 with PKCE for security
    """
    result = x_oauth.generate_authorization_url(user_id)
    return RedirectResponse(url=result['authorization_url'])


@router.get("/x/callback")
async def x_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    X OAuth callback endpoint
    
    - Receives authorization code
    - Exchanges for access token
    - Returns connected account info
    """
    try:
        result = await x_oauth.handle_callback(
            code=code,
            state=state,
            error=error
        )
        
        # Store in database
        # await db.store_x_account(result)
        
        return {
            'success': True,
            'message': 'X account connected successfully',
            'username': result['x_username'],
            'user_id': result['x_user_id']
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connect/pinterest")
async def initiate_pinterest_oauth(user_id: str):
    """
    Initiate Pinterest OAuth flow
    
    - Redirects user to Pinterest authorization page
    """
    result = pinterest_oauth.generate_authorization_url(user_id)
    return RedirectResponse(url=result['authorization_url'])


@router.get("/pinterest/callback")
async def pinterest_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Pinterest OAuth callback endpoint
    
    - Receives authorization code
    - Exchanges for access token
    - Returns connected account and boards
    """
    try:
        result = await pinterest_oauth.handle_callback(
            code=code,
            state=state,
            error=error
        )
        
        # Store in database
        # await db.store_pinterest_account(result)
        
        return {
            'success': True,
            'message': 'Pinterest account connected successfully',
            'username': result['pinterest_username'],
            'boards': result['boards'],
            'board_count': len(result['boards'])
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/x/refresh")
async def refresh_x_token(refresh_token: str):
    """Refresh X access token"""
    try:
        result = await x_oauth.refresh_token(refresh_token)
        return result
    except HTTPException as e:
        raise e


@router.post("/pinterest/refresh")
async def refresh_pinterest_token(refresh_token: str):
    """Refresh Pinterest access token"""
    try:
        result = await pinterest_oauth.refresh_token(refresh_token)
        return result
    except HTTPException as e:
        raise e


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_x_oauth():
        handler = XOAuthHandler()
        
        # Generate authorization URL
        auth_data = handler.generate_authorization_url(user_id="user_123")
        
        print(f"X Authorization URL: {auth_data['authorization_url']}")
        print(f"State: {auth_data['state']}")
    
    async def test_pinterest_oauth():
        handler = PinterestOAuthHandler()
        
        # Generate authorization URL
        auth_data = handler.generate_authorization_url(user_id="user_123")
        
        print(f"Pinterest Authorization URL: {auth_data['authorization_url']}")
        print(f"State: {auth_data['state']}")
    
    # Run tests
    asyncio.run(test_x_oauth())
    asyncio.run(test_pinterest_oauth())
