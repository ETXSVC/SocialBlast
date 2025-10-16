"""
X (Twitter) and Pinterest Integration Module
Handles posting to X and Pinterest APIs
"""

import requests
import requests_oauthlib
from typing import Dict, Optional, List
from datetime import datetime
import base64
import hashlib
import hmac
import time


class XPoster:
    """
    X (Twitter) API v2 integration for posting content
    Supports: Tweets with media, threads, polls
    """
    
    def __init__(self):
        self.api_version = "2"
        self.base_url = "https://api.twitter.com/2"
        self.upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    
    async def post_tweet(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str,
        text: str,
        media_ids: Optional[List[str]] = None,
        reply_settings: str = "everyone"
    ) -> Dict:
        """
        Post a tweet with optional media
        
        Args:
            access_token: User OAuth access token
            access_token_secret: User OAuth access token secret
            consumer_key: App consumer key
            consumer_secret: App consumer secret
            text: Tweet text (max 280 characters)
            media_ids: List of uploaded media IDs
            reply_settings: "everyone", "mentionedUsers", or "following"
            
        Returns:
            Dict with tweet_id and status
        """
        # Validate text length
        if len(text) > 280:
            return {
                'success': False,
                'error': 'Tweet text exceeds 280 characters',
                'error_type': 'text_too_long'
            }
        
        # Create OAuth1 session
        oauth = requests_oauthlib.OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        # Build tweet payload
        payload = {
            "text": text
        }
        
        if media_ids:
            payload["media"] = {
                "media_ids": media_ids
            }
        
        if reply_settings != "everyone":
            payload["reply_settings"] = reply_settings
        
        try:
            response = requests.post(
                f"{self.base_url}/tweets",
                auth=oauth,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            tweet_data = result.get('data', {})
            
            return {
                'success': True,
                'tweet_id': tweet_data.get('id'),
                'text': tweet_data.get('text'),
                'platform_url': f"https://twitter.com/i/status/{tweet_data.get('id')}",
                'timestamp': datetime.utcnow()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'api_error'
            }
    
    async def upload_media(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str,
        image_path: str,
        alt_text: Optional[str] = None
    ) -> Dict:
        """
        Upload media to X (required before posting tweet with media)
        
        Args:
            access_token: User OAuth access token
            access_token_secret: User OAuth access token secret
            consumer_key: App consumer key
            consumer_secret: App consumer secret
            image_path: Path to image file
            alt_text: Optional alt text for accessibility
            
        Returns:
            Dict with media_id
        """
        oauth = requests_oauthlib.OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        try:
            # Upload media
            with open(image_path, 'rb') as image_file:
                files = {'media': image_file}
                
                response = requests.post(
                    self.upload_url,
                    auth=oauth,
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                media_id = result.get('media_id_string')
                
                # Add alt text if provided
                if alt_text and media_id:
                    await self._add_media_metadata(
                        oauth, media_id, alt_text
                    )
                
                return {
                    'success': True,
                    'media_id': media_id
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'upload_failed'
            }
    
    async def _add_media_metadata(
        self,
        oauth: requests_oauthlib.OAuth1,
        media_id: str,
        alt_text: str
    ):
        """Add metadata (alt text) to uploaded media"""
        url = "https://upload.twitter.com/1.1/media/metadata/create.json"
        
        payload = {
            "media_id": media_id,
            "alt_text": {
                "text": alt_text[:1000]  # Max 1000 characters
            }
        }
        
        try:
            response = requests.post(
                url,
                auth=oauth,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
        except:
            pass  # Non-critical, continue even if metadata fails
    
    async def post_thread(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str,
        tweets: List[Dict]
    ) -> Dict:
        """
        Post a thread of tweets
        
        Args:
            tweets: List of dicts with 'text' and optional 'media_ids'
            
        Returns:
            Dict with all tweet IDs
        """
        thread_ids = []
        reply_to_id = None
        
        oauth = requests_oauthlib.OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        for tweet_data in tweets:
            payload = {
                "text": tweet_data['text']
            }
            
            if tweet_data.get('media_ids'):
                payload["media"] = {
                    "media_ids": tweet_data['media_ids']
                }
            
            # Add reply-to for threading
            if reply_to_id:
                payload["reply"] = {
                    "in_reply_to_tweet_id": reply_to_id
                }
            
            try:
                response = requests.post(
                    f"{self.base_url}/tweets",
                    auth=oauth,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                tweet_id = result['data']['id']
                thread_ids.append(tweet_id)
                reply_to_id = tweet_id
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'posted_tweets': thread_ids
                }
        
        return {
            'success': True,
            'tweet_ids': thread_ids,
            'thread_url': f"https://twitter.com/i/status/{thread_ids[0]}"
        }
    
    async def get_user_info(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str
    ) -> Dict:
        """Get authenticated user information"""
        oauth = requests_oauthlib.OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                auth=oauth,
                params={"user.fields": "id,name,username,profile_image_url,public_metrics"},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('data', {})
            
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}


class PinterestPoster:
    """
    Pinterest API v5 integration for posting pins
    Supports: Image pins, idea pins, boards
    """
    
    def __init__(self):
        self.api_version = "v5"
        self.base_url = f"https://api.pinterest.com/{self.api_version}"
    
    async def create_pin(
        self,
        access_token: str,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        link: Optional[str] = None,
        alt_text: Optional[str] = None
    ) -> Dict:
        """
        Create a pin on Pinterest
        
        Args:
            access_token: Pinterest access token
            board_id: Board ID to pin to
            title: Pin title (max 100 chars)
            description: Pin description (max 500 chars)
            image_url: Public URL of image
            link: Optional destination link
            alt_text: Optional alt text for accessibility
            
        Returns:
            Dict with pin_id and status
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Build pin data
        pin_data = {
            "board_id": board_id,
            "title": title[:100],
            "description": description[:500],
            "media_source": {
                "source_type": "image_url",
                "url": image_url
            }
        }
        
        if link:
            pin_data["link"] = link
        
        if alt_text:
            pin_data["alt_text"] = alt_text[:500]
        
        try:
            response = requests.post(
                f"{self.base_url}/pins",
                headers=headers,
                json=pin_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'pin_id': result.get('id'),
                'platform_url': f"https://www.pinterest.com/pin/{result.get('id')}",
                'board_id': result.get('board_id'),
                'timestamp': datetime.utcnow()
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = e.response.json() if hasattr(e, 'response') else {}
            return {
                'success': False,
                'error': str(e),
                'error_detail': error_detail,
                'error_type': 'api_error'
            }
    
    async def upload_media(
        self,
        access_token: str,
        image_path: str
    ) -> Dict:
        """
        Upload media to Pinterest (returns media_id for use in pins)
        
        Args:
            access_token: Pinterest access token
            image_path: Path to image file
            
        Returns:
            Dict with media_id
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                
                response = requests.post(
                    f"{self.base_url}/media",
                    headers=headers,
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                
                return {
                    'success': True,
                    'media_id': result.get('media_id'),
                    'upload_url': result.get('upload_url')
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'upload_failed'
            }
    
    async def create_board(
        self,
        access_token: str,
        name: str,
        description: Optional[str] = None,
        privacy: str = "PUBLIC"
    ) -> Dict:
        """
        Create a new Pinterest board
        
        Args:
            access_token: Pinterest access token
            name: Board name
            description: Optional board description
            privacy: "PUBLIC" or "SECRET"
            
        Returns:
            Dict with board_id
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        board_data = {
            "name": name,
            "privacy": privacy
        }
        
        if description:
            board_data["description"] = description
        
        try:
            response = requests.post(
                f"{self.base_url}/boards",
                headers=headers,
                json=board_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'board_id': result.get('id'),
                'name': result.get('name'),
                'url': f"https://www.pinterest.com/{result.get('owner', {}).get('username')}/{result.get('name')}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'board_creation_failed'
            }
    
    async def list_boards(
        self,
        access_token: str,
        page_size: int = 25
    ) -> Dict:
        """
        List user's Pinterest boards
        
        Args:
            access_token: Pinterest access token
            page_size: Number of boards per page
            
        Returns:
            Dict with list of boards
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        params = {
            "page_size": page_size
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/boards",
                headers=headers,
                params=params,
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
                    'pin_count': board.get('pin_count', 0),
                    'privacy': board.get('privacy')
                })
            
            return {
                'success': True,
                'boards': boards,
                'total_count': len(boards)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get authenticated user information"""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/user_account",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'username': result.get('username'),
                'account_type': result.get('account_type'),
                'profile_image': result.get('profile_image'),
                'follower_count': result.get('follower_count', 0),
                'board_count': result.get('board_count', 0)
            }
            
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}


# Extended Platform Manager
class ExtendedPlatformManager:
    """
    Unified manager for all social platforms including X and Pinterest
    """
    
    def __init__(self):
        from social_integrations import FacebookPoster, InstagramPoster
        
        self.facebook = FacebookPoster()
        self.instagram = InstagramPoster()
        self.x = XPoster()
        self.pinterest = PinterestPoster()
    
    async def post_to_platform(
        self,
        platform: str,
        post_type: str,
        credentials: Dict,
        content: Dict,
        **kwargs
    ) -> Dict:
        """
        Universal posting method for all platforms
        
        Args:
            platform: 'facebook', 'instagram', 'x', or 'pinterest'
            post_type: Platform-specific post type
            credentials: Platform credentials (access tokens, etc.)
            content: Post content (text, image_path, etc.)
            **kwargs: Additional platform-specific parameters
            
        Returns:
            Standardized response dict
        """
        try:
            if platform == 'x':
                # Upload media first if image provided
                media_ids = []
                if content.get('image_path'):
                    upload_result = await self.x.upload_media(
                        credentials['access_token'],
                        credentials['access_token_secret'],
                        credentials['consumer_key'],
                        credentials['consumer_secret'],
                        content['image_path'],
                        alt_text=content.get('alt_text')
                    )
                    
                    if upload_result['success']:
                        media_ids.append(upload_result['media_id'])
                
                # Post tweet
                return await self.x.post_tweet(
                    credentials['access_token'],
                    credentials['access_token_secret'],
                    credentials['consumer_key'],
                    credentials['consumer_secret'],
                    content['text'],
                    media_ids=media_ids if media_ids else None
                )
            
            elif platform == 'pinterest':
                # Create pin
                return await self.pinterest.create_pin(
                    credentials['access_token'],
                    content['board_id'],
                    content['title'],
                    content['description'],
                    content['image_url'],
                    link=content.get('link'),
                    alt_text=content.get('alt_text')
                )
            
            elif platform == 'facebook':
                if post_type == 'feed':
                    return await self.facebook.post_feed(
                        credentials['page_id'],
                        credentials['access_token'],
                        content['image_path'],
                        content['caption']
                    )
            
            elif platform == 'instagram':
                if post_type == 'feed':
                    return await self.instagram.post_feed(
                        credentials['account_id'],
                        credentials['access_token'],
                        content['image_url'],
                        content['caption']
                    )
            
            return {
                'success': False,
                'error': f'Unsupported platform/type: {platform}/{post_type}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'unexpected_error'
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_x_posting():
        x_poster = XPoster()
        
        # Upload image
        upload_result = await x_poster.upload_media(
            access_token='your_token',
            access_token_secret='your_secret',
            consumer_key='your_key',
            consumer_secret='your_secret',
            image_path='image.jpg',
            alt_text='A beautiful sunset'
        )
        
        if upload_result['success']:
            # Post tweet with media
            result = await x_poster.post_tweet(
                access_token='your_token',
                access_token_secret='your_secret',
                consumer_key='your_key',
                consumer_secret='your_secret',
                text='Check out this amazing sunset! 🌅 #photography',
                media_ids=[upload_result['media_id']]
            )
            print(f"X result: {result}")
    
    async def test_pinterest_posting():
        pinterest_poster = PinterestPoster()
        
        # Create pin
        result = await pinterest_poster.create_pin(
            access_token='your_token',
            board_id='your_board_id',
            title='Amazing Sunset',
            description='Beautiful sunset photo taken at the beach. #sunset #nature',
            image_url='https://example.com/image.jpg',
            link='https://yourwebsite.com'
        )
        print(f"Pinterest result: {result}")
    
    # Run tests
    # asyncio.run(test_x_posting())
    # asyncio.run(test_pinterest_posting())
