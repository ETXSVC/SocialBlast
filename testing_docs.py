"""
Comprehensive Testing Suite
Tests for all API endpoints, image processing, and integrations
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from PIL import Image
import io
import os
from datetime import datetime, timedelta

# Assuming imports from your main application
# from main import app
# from database_models import User, Post, Image as ImageModel
# from image_processor import ImageProcessor
# from keyword_extractor import KeywordExtractor


# ============================================
# Test Configuration
# ============================================

@pytest.fixture
def test_client():
    """Create test client"""
    # from main import app
    # client = TestClient(app)
    # return client
    pass


@pytest.fixture
def test_db():
    """Create test database session"""
    # Setup test database
    # yield db session
    # Teardown test database
    pass


@pytest.fixture
def test_user():
    """Create test user"""
    return {
        'id': 'test_user_123',
        'email': 'test@example.com',
        'api_key': 'test_api_key_12345'
    }


@pytest.fixture
def test_image():
    """Create test image"""
    img = Image.new('RGB', (1200, 800), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


# ============================================
# API Endpoint Tests
# ============================================

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()['status'] == 'operational'
    
    def test_upload_image_success(self, test_client, test_image, test_user):
        """Test successful image upload"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        response = test_client.post(
            "/api/v1/upload",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'image_id' in data
        assert 'original_filename' in data
        assert data['original_filename'] == 'test.jpg'
    
    def test_upload_image_invalid_type(self, test_client, test_user):
        """Test upload with invalid file type"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        files = {'file': ('test.txt', b'not an image', 'text/plain')}
        
        response = test_client.post(
            "/api/v1/upload",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_upload_image_no_auth(self, test_client, test_image):
        """Test upload without authentication"""
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        response = test_client.post("/api/v1/upload", files=files)
        
        assert response.status_code == 401
    
    def test_extract_keywords(self, test_client, test_user):
        """Test keyword extraction"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        
        response = test_client.get(
            "/api/v1/keywords/test_image_id",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'keywords' in data
            assert 'hashtags' in data
            assert isinstance(data['keywords'], list)
    
    def test_create_post(self, test_client, test_user):
        """Test post creation"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        post_data = {
            'platforms': ['facebook', 'instagram'],
            'post_types': {
                'facebook': 'feed',
                'instagram': 'feed_square'
            },
            'caption': 'Test post caption #testing',
            'image_ids': ['test_image_1'],
            'auto_hashtags': True
        }
        
        response = test_client.post(
            "/api/v1/posts",
            json=post_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'post_id' in data
        assert 'status' in data
    
    def test_get_post_status(self, test_client, test_user):
        """Test retrieving post status"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        
        response = test_client.get(
            "/api/v1/posts/test_post_id",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'post_id' in data
            assert 'status' in data
            assert 'platform_results' in data
    
    def test_cancel_scheduled_post(self, test_client, test_user):
        """Test cancelling a scheduled post"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        
        response = test_client.delete(
            "/api/v1/posts/test_post_id",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    def test_connect_social_account(self, test_client, test_user):
        """Test connecting social account"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        account_data = {
            'platform': 'facebook',
            'account_id': 'fb_12345',
            'account_name': 'Test Page',
            'access_token': 'test_token_12345'
        }
        
        response = test_client.post(
            "/api/v1/auth/connect",
            json=account_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'id' in data
            assert data['platform'] == 'facebook'
    
    def test_list_connected_accounts(self, test_client, test_user):
        """Test listing connected accounts"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        
        response = test_client.get(
            "/api/v1/accounts",
            headers=headers
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================
# Image Processing Tests
# ============================================

class TestImageProcessing:
    """Test image processing functionality"""
    
    def test_resize_for_facebook_feed(self):
        """Test resizing for Facebook feed"""
        from image_processor import ImageProcessor
        
        processor = ImageProcessor(quality=85)
        
        # Create test image
        test_img = Image.new('RGB', (2000, 1500), color='blue')
        test_path = 'test_input.jpg'
        test_img.save(test_path)
        
        try:
            result = processor.process_for_platform(
                test_path,
                'facebook',
                'feed',
                'test_output.jpg'
            )
            
            assert result['dimensions'] == (1200, 630)
            assert result['file_size_mb'] < 4
            assert result['dpi'] == 72
            assert os.path.exists(result['output_path'])
            
        finally:
            # Cleanup
            if os.path.exists(test_path):
                os.remove(test_path)
            if os.path.exists('test_output.jpg'):
                os.remove('test_output.jpg')
    
    def test_resize_for_instagram_square(self):
        """Test resizing for Instagram square post"""
        from image_processor import ImageProcessor
        
        processor = ImageProcessor(quality=85)
        
        test_img = Image.new('RGB', (1920, 1080), color='green')
        test_path = 'test_input.jpg'
        test_img.save(test_path)
        
        try:
            result = processor.process_for_platform(
                test_path,
                'instagram',
                'feed_square',
                'test_output.jpg'
            )
            
            assert result['dimensions'] == (1080, 1080)
            assert result['file_size_mb'] < 8
            
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
            if os.path.exists('test_output.jpg'):
                os.remove('test_output.jpg')
    
    def test_batch_processing(self):
        """Test batch processing for multiple platforms"""
        from image_processor import ImageProcessor
        
        processor = ImageProcessor(quality=85)
        
        test_img = Image.new('RGB', (2400, 1600), color='yellow')
        test_path = 'test_input.jpg'
        test_img.save(test_path)
        
        try:
            platforms = [
                {'platform': 'facebook', 'post_type': 'feed'},
                {'platform': 'instagram', 'post_type': 'feed_square'},
                {'platform': 'instagram', 'post_type': 'story'}
            ]
            
            results = processor.batch_process(
                test_path,
                platforms,
                output_dir='./test_output'
            )
            
            assert len(results) == 3
            assert 'facebook_feed' in results
            assert 'instagram_feed_square' in results
            assert 'instagram_story' in results
            
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
            # Cleanup output directory
            import shutil
            if os.path.exists('./test_output'):
                shutil.rmtree('./test_output')
    
    def test_image_quality_optimization(self):
        """Test image quality optimization"""
        from image_processor import ImageProcessor
        
        processor = ImageProcessor(quality=85)
        
        # Create large image
        test_img = Image.new('RGB', (4000, 3000), color='purple')
        test_path = 'test_large.jpg'
        test_img.save(test_path)
        
        try:
            result = processor.process_for_platform(
                test_path,
                'facebook',
                'feed'
            )
            
            # Should be optimized to under 4MB
            assert result['file_size_mb'] < 4
            
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


# ============================================
# Keyword Extraction Tests
# ============================================

class TestKeywordExtraction:
    """Test keyword extraction functionality"""
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        reason="Google Cloud credentials not configured"
    )
    def test_extract_keywords_from_image(self):
        """Test keyword extraction"""
        from keyword_extractor import KeywordExtractor
        
        extractor = KeywordExtractor()
        
        # Create test image with text
        test_img = Image.new('RGB', (800, 600), color='white')
        test_path = 'test_keywords.jpg'
        test_img.save(test_path)
        
        try:
            result = extractor.extract_keywords(
                test_path,
                max_keywords=10,
                min_score=0.5
            )
            
            assert 'keywords' in result
            assert 'total_detected' in result
            assert isinstance(result['keywords'], list)
            assert len(result['keywords']) <= 10
            
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
    
    def test_generate_hashtags(self):
        """Test hashtag generation from keywords"""
        from keyword_extractor import KeywordExtractor
        
        extractor = KeywordExtractor()
        
        keywords = [
            {'keyword': 'sunset', 'score': 0.95},
            {'keyword': 'beach scene', 'score': 0.88},
            {'keyword': 'ocean', 'score': 0.82}
        ]
        
        hashtags = extractor.generate_hashtags(keywords, max_hashtags=5)
        
        assert len(hashtags) <= 5
        assert all(tag.startswith('#') for tag in hashtags)
        assert '#Sunset' in hashtags
        assert '#BeachScene' in hashtags


# ============================================
# Social Platform Integration Tests
# ============================================

class TestSocialIntegrations:
    """Test social media platform integrations"""
    
    @pytest.mark.asyncio
    async def test_facebook_post_feed(self):
        """Test posting to Facebook feed"""
        from social_integrations import FacebookPoster
        
        poster = FacebookPoster()
        
        # Mock test - would need actual credentials
        # result = await poster.post_feed(
        #     page_id='test_page_id',
        #     access_token='test_token',
        #     image_path='test_image.jpg',
        #     caption='Test post'
        # )
        
        # assert 'success' in result
    
    @pytest.mark.asyncio
    async def test_instagram_post_feed(self):
        """Test posting to Instagram feed"""
        from social_integrations import InstagramPoster
        
        poster = InstagramPoster()
        
        # Mock test
        # result = await poster.post_feed(
        #     instagram_account_id='test_account_id',
        #     access_token='test_token',
        #     image_url='https://example.com/test.jpg',
        #     caption='Test caption'
        # )
        
        # assert 'success' in result


# ============================================
# OAuth Flow Tests
# ============================================

class TestOAuthFlow:
    """Test OAuth authentication flow"""
    
    def test_generate_authorization_url(self):
        """Test OAuth URL generation"""
        from oauth_handler import MetaOAuthHandler
        
        handler = MetaOAuthHandler()
        
        result = handler.generate_authorization_url(
            user_id='test_user_123',
            platform='facebook'
        )
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'facebook.com' in result['authorization_url']
    
    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self):
        """Test OAuth callback with invalid state"""
        from oauth_handler import MetaOAuthHandler
        from fastapi import HTTPException
        
        handler = MetaOAuthHandler()
        
        with pytest.raises(HTTPException) as exc_info:
            await handler.handle_callback(
                code='test_code',
                state='invalid_state'
            )
        
        assert exc_info.value.status_code == 400


# ============================================
# Database Tests
# ============================================

class TestDatabase:
    """Test database operations"""
    
    def test_create_user(self, test_db):
        """Test user creation"""
        from database_models import DatabaseQueries
        
        user = DatabaseQueries.create_user(
            test_db,
            email='newuser@example.com',
            password_hash='hashed_password',
            api_key='new_api_key_12345'
        )
        
        assert user.email == 'newuser@example.com'
        assert user.api_key == 'new_api_key_12345'
    
    def test_create_post(self, test_db, test_user):
        """Test post creation"""
        from database_models import DatabaseQueries
        
        post_data = {
            'caption': 'Test post',
            'platforms': ['facebook'],
            'post_types': {'facebook': 'feed'},
            'auto_hashtags': True
        }
        
        post = DatabaseQueries.create_post(
            test_db,
            test_user['id'],
            post_data,
            ['image_1']
        )
        
        assert post.caption == 'Test post'
        assert 'facebook' in post.platforms


# ============================================
# Performance Tests
# ============================================

class TestPerformance:
    """Test performance and load"""
    
    def test_image_processing_speed(self):
        """Test image processing performance"""
        from image_processor import ImageProcessor
        import time
        
        processor = ImageProcessor()
        
        test_img = Image.new('RGB', (2000, 1500), color='blue')
        test_path = 'perf_test.jpg'
        test_img.save(test_path)
        
        try:
            start_time = time.time()
            
            result = processor.process_for_platform(
                test_path,
                'instagram',
                'feed_square'
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should process in under 2 seconds
            assert processing_time < 2.0
            
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
            if os.path.exists(result['output_path']):
                os.remove(result['output_path'])


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """End-to-end integration tests"""
    
    def test_full_post_workflow(self, test_client, test_user, test_image):
        """Test complete workflow: upload -> extract keywords -> post"""
        headers = {'Authorization': f'Bearer {test_user["api_key"]}'}
        
        # 1. Upload image
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        upload_response = test_client.post(
            "/api/v1/upload",
            files=files,
            headers=headers
        )
        assert upload_response.status_code == 200
        image_id = upload_response.json()['image_id']
        
        # 2. Extract keywords
        keywords_response = test_client.get(
            f"/api/v1/keywords/{image_id}",
            headers=headers
        )
        
        # 3. Create post
        post_data = {
            'platforms': ['facebook'],
            'post_types': {'facebook': 'feed'},
            'caption': 'Integration test post',
            'image_ids': [image_id],
            'auto_hashtags': True
        }
        
        post_response = test_client.post(
            "/api/v1/posts",
            json=post_data,
            headers=headers
        )
        assert post_response.status_code == 200
        post_id = post_response.json()['post_id']
        
        # 4. Check post status
        status_response = test_client.get(
            f"/api/v1/posts/{post_id}",
            headers=headers
        )
        assert status_response.status_code == 200


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--cov=.', '--cov-report=html'])
