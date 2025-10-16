"""
Social Media Platform Integrations
Handles posting to Facebook and Instagram via Graph API
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime
import time


class FacebookPoster:
    """
    Facebook Graph API integration for posting content
    Supports: Feed posts, Stories, Photo albums
    """
    
    def __init__(self):
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    async def post_feed(
        self,
        page_id: str,
        access_token: str,
        image_path: str,
        caption: str,
        link: Optional[str] = None
    ) -> Dict:
        """
        Post an image to Facebook Page feed
        
        Args:
            page_id: Facebook Page ID
            access_token: Page access token
            image_path: Path to image file
            caption: Post caption
            link: Optional link to attach
            
        Returns:
            Dict with post_id and status
        """
        url = f"{self.base_url}/{page_id}/photos"
        
        # Open and send image
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            data = {
                'message': caption,
                'access_token': access_token
            }
            
            if link:
                data['link'] = link
            
            try:
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                return {
                    'success': True,
                    'post_id': result.get('id'),
                    'platform_url': f"https://facebook.com/{result.get('id')}",
                    'timestamp': datetime.utcnow()
                }
                
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'network_error'
                }
    
    async def post_story(
        self,
        page_id: str,
        access_token: str,
        image_path: str
    ) -> Dict:
        """
        Post an image to Facebook Stories
        
        Args:
            page_id: Facebook Page ID
            access_token: Page access token
            image_path: Path to story image (1080x1920)
            
        Returns:
            Dict with story_id and status
        """
        url = f"{self.base_url}/{page_id}/stories"
        
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            data = {'access_token': access_token}
            
            try:
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                return {
                    'success': True,
                    'story_id': result.get('id'),
                    'timestamp': datetime.utcnow()
                }
                
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'network_error'
                }
    
    async def get_page_info(self, page_id: str, access_token: str) -> Dict:
        """Get Facebook Page information"""
        url = f"{self.base_url}/{page_id}"
        params = {
            'fields': 'id,name,username,fan_count,category',
            'access_token': access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate Facebook access token"""
        url = f"{self.base_url}/me"
        params = {'access_token': access_token}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False


class InstagramPoster:
    """
    Instagram Graph API integration for posting content
    Supports: Feed posts, Stories, Reels
    Uses container creation workflow
    """
    
    def __init__(self):
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    async def post_feed(
        self,
        instagram_account_id: str,
        access_token: str,
        image_url: str,
        caption: str,
        location_id: Optional[str] = None
    ) -> Dict:
        """
        Post an image to Instagram feed using container workflow
        
        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Access token with instagram_content_publish permission
            image_url: Publicly accessible URL of the image
            caption: Post caption (max 2200 chars)
            location_id: Optional location ID
            
        Returns:
            Dict with post_id and status
        """
        # Step 1: Create container
        container = await self._create_container(
            instagram_account_id,
            access_token,
            image_url,
            caption,
            location_id
        )
        
        if not container.get('success'):
            return container
        
        container_id = container['container_id']
        
        # Step 2: Wait for container to be ready (important!)
        await self._wait_for_container(container_id, access_token)
        
        # Step 3: Publish container
        return await self._publish_container(
            instagram_account_id,
            access_token,
            container_id
        )
    
    async def _create_container(
        self,
        account_id: str,
        access_token: str,
        image_url: str,
        caption: str,
        location_id: Optional[str] = None
    ) -> Dict:
        """Create media container"""
        url = f"{self.base_url}/{account_id}/media"
        
        data = {
            'image_url': image_url,
            'caption': caption,
            'access_token': access_token
        }
        
        if location_id:
            data['location_id'] = location_id
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'container_id': result.get('id')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'container_creation_failed'
            }
    
    async def _wait_for_container(
        self,
        container_id: str,
        access_token: str,
        max_attempts: int = 10
    ):
        """Wait for container to be ready for publishing"""
        url = f"{self.base_url}/{container_id}"
        params = {
            'fields': 'status_code',
            'access_token': access_token
        }
        
        for _ in range(max_attempts):
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status_code') == 'FINISHED':
                    return True
            
            time.sleep(2)  # Wait 2 seconds between checks
        
        return False
    
    async def _publish_container(
        self,
        account_id: str,
        access_token: str,
        container_id: str
    ) -> Dict:
        """Publish the media container"""
        url = f"{self.base_url}/{account_id}/media_publish"
        
        data = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            media_id = result.get('id')
            
            return {
                'success': True,
                'post_id': media_id,
                'platform_url': f"https://instagram.com/p/{self._get_shortcode(media_id)}",
                'timestamp': datetime.utcnow()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'publish_failed'
            }
    
    def _get_shortcode(self, media_id: str) -> str:
        """Convert media ID to Instagram shortcode (simplified)"""
        # This is a placeholder - actual conversion is more complex
        return media_id
    
    async def post_story(
        self,
        instagram_account_id: str,
        access_token: str,
        image_url: str
    ) -> Dict:
        """
        Post an image to Instagram Stories
        
        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Access token
            image_url: Publicly accessible URL (1080x1920)
            
        Returns:
            Dict with story_id and status
        """
        # Create story container
        url = f"{self.base_url}/{instagram_account_id}/media"
        
        data = {
            'image_url': image_url,
            'media_type': 'STORIES',
            'access_token': access_token
        }
        
        try:
            # Create container
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            container_id = response.json().get('id')
            
            # Wait and publish
            await self._wait_for_container(container_id, access_token)
            
            publish_url = f"{self.base_url}/{instagram_account_id}/media_publish"
            publish_data = {
                'creation_id': container_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            publish_response.raise_for_status()
            
            return {
                'success': True,
                'story_id': publish_response.json().get('id'),
                'timestamp': datetime.utcnow()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'story_post_failed'
            }
    
    async def post_carousel(
        self,
        instagram_account_id: str,
        access_token: str,
        image_urls: List[str],
        caption: str
    ) -> Dict:
        """
        Post a carousel (multiple images) to Instagram
        
        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Access token
            image_urls: List of image URLs (2-10 images)
            caption: Post caption
            
        Returns:
            Dict with post_id and status
        """
        if len(image_urls) < 2 or len(image_urls) > 10:
            return {
                'success': False,
                'error': 'Carousel must have 2-10 images'
            }
        
        # Create containers for each image
        container_ids = []
        for image_url in image_urls:
            url = f"{self.base_url}/{instagram_account_id}/media"
            data = {
                'image_url': image_url,
                'is_carousel_item': True,
                'access_token': access_token
            }
            
            try:
                response = requests.post(url, data=data, timeout=30)
                response.raise_for_status()
                container_ids.append(response.json().get('id'))
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to create carousel item: {str(e)}'
                }
        
        # Create carousel container
        carousel_url = f"{self.base_url}/{instagram_account_id}/media"
        carousel_data = {
            'media_type': 'CAROUSEL',
            'children': ','.join(container_ids),
            'caption': caption,
            'access_token': access_token
        }
        
        try:
            response = requests.post(carousel_url, data=carousel_data, timeout=30)
            response.raise_for_status()
            carousel_id = response.json().get('id')
            
            # Wait and publish
            await self._wait_for_container(carousel_id, access_token)
            
            return await self._publish_container(
                instagram_account_id,
                access_token,
                carousel_id
            )
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'carousel_post_failed'
            }
    
    async def get_account_info(
        self,
        instagram_account_id: str,
        access_token: str
    ) -> Dict:
        """Get Instagram Business Account information"""
        url = f"{self.base_url}/{instagram_account_id}"
        params = {
            'fields': 'id,username,name,profile_picture_url,followers_count,media_count',
            'access_token': access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    async def validate_token(
        self,
        instagram_account_id: str,
        access_token: str
    ) -> bool:
        """Validate Instagram access token"""
        url = f"{self.base_url}/{instagram_account_id}"
        params = {'access_token': access_token}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False


class PlatformManager:
    """
    Unified manager for all social platforms
    Handles routing and error handling
    """
    
    def __init__(self):
        self.facebook = FacebookPoster()
        self.instagram = InstagramPoster()
    
    async def post_to_platform(
        self,
        platform: str,
        post_type: str,
        account_id: str,
        access_token: str,
        image_path_or_url: str,
        caption: str = "",
        **kwargs
    ) -> Dict:
        """
        Universal posting method for all platforms
        
        Args:
            platform: 'facebook' or 'instagram'
            post_type: 'feed', 'story', 'carousel'
            account_id: Platform-specific account ID
            access_token: Access token for the account
            image_path_or_url: Path or URL to image
            caption: Post caption
            **kwargs: Additional platform-specific parameters
            
        Returns:
            Standardized response dict
        """
        try:
            if platform == 'facebook':
                if post_type == 'feed':
                    return await self.facebook.post_feed(
                        account_id, access_token, image_path_or_url, caption, 
                        kwargs.get('link')
                    )
                elif post_type == 'story':
                    return await self.facebook.post_story(
                        account_id, access_token, image_path_or_url
                    )
                    
            elif platform == 'instagram':
                if post_type == 'feed':
                    return await self.instagram.post_feed(
                        account_id, access_token, image_path_or_url, caption,
                        kwargs.get('location_id')
                    )
                elif post_type == 'story':
                    return await self.instagram.post_story(
                        account_id, access_token, image_path_or_url
                    )
                elif post_type == 'carousel':
                    return await self.instagram.post_carousel(
                        account_id, access_token, kwargs.get('image_urls', []), caption
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
    
    async def validate_account(
        self,
        platform: str,
        account_id: str,
        access_token: str
    ) -> Dict:
        """Validate account credentials for a platform"""
        try:
            if platform == 'facebook':
                is_valid = await self.facebook.validate_token(access_token)
                if is_valid:
                    info = await self.facebook.get_page_info(account_id, access_token)
                    return {'valid': True, 'account_info': info}
                    
            elif platform == 'instagram':
                is_valid = await self.instagram.validate_token(account_id, access_token)
                if is_valid:
                    info = await self.instagram.get_account_info(account_id, access_token)
                    return {'valid': True, 'account_info': info}
            
            return {'valid': False, 'error': 'Invalid credentials'}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_posting():
        manager = PlatformManager()
        
        # Test Facebook post
        fb_result = await manager.post_to_platform(
            platform='facebook',
            post_type='feed',
            account_id='YOUR_PAGE_ID',
            access_token='YOUR_ACCESS_TOKEN',
            image_path_or_url='/path/to/image.jpg',
            caption='Check out this amazing content! #social #media'
        )
        print(f"Facebook result: {fb_result}")
        
        # Test Instagram post
        ig_result = await manager.post_to_platform(
            platform='instagram',
            post_type='feed',
            account_id='YOUR_INSTAGRAM_ACCOUNT_ID',
            access_token='YOUR_ACCESS_TOKEN',
            image_path_or_url='https://example.com/image.jpg',
            caption='Beautiful day! #instagram #photo'
        )
        print(f"Instagram result: {ig_result}")
    
    # Run test
    asyncio.run(test_posting())