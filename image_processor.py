"""
Image Processing Module for Social Media API
Handles automatic resizing, optimization, and format conversion
"""

from PIL import Image, ImageOps
from typing import Tuple, Optional, Dict
import io
from pathlib import Path


class PlatformSpecs:
    """Platform-specific image requirements"""
    
    FACEBOOK = {
        'feed': {'size': (1200, 630), 'ratio': 1.91, 'max_size_mb': 4},
        'story': {'size': (1080, 1920), 'ratio': 0.5625, 'max_size_mb': 4},
        'profile': {'size': (180, 180), 'ratio': 1.0, 'max_size_mb': 4}
    }
    
    INSTAGRAM = {
        'feed_square': {'size': (1080, 1080), 'ratio': 1.0, 'max_size_mb': 8},
        'feed_portrait': {'size': (1080, 1350), 'ratio': 0.8, 'max_size_mb': 8},
        'story': {'size': (1080, 1920), 'ratio': 0.5625, 'max_size_mb': 8},
        'reels': {'size': (1080, 1920), 'ratio': 0.5625, 'max_size_mb': 8}
    }
    
    X = {
        'tweet': {'size': (1200, 675), 'ratio': 1.78, 'max_size_mb': 5},
        'tweet_square': {'size': (1200, 1200), 'ratio': 1.0, 'max_size_mb': 5},
        'header': {'size': (1500, 500), 'ratio': 3.0, 'max_size_mb': 5}
    }
    
    PINTEREST = {
        'pin': {'size': (1000, 1500), 'ratio': 0.67, 'max_size_mb': 20},
        'pin_square': {'size': (1000, 1000), 'ratio': 1.0, 'max_size_mb': 20},
        'pin_wide': {'size': (1000, 500), 'ratio': 2.0, 'max_size_mb': 20}
    }
    
    DPI = 72  # Web-optimized DPI


class ImageProcessor:
    """
    Handles all image processing operations including:
    - Automatic resizing
    - Smart cropping
    - Quality optimization
    - Format conversion
    """
    
    def __init__(self, quality: int = 85):
        """
        Initialize the image processor
        
        Args:
            quality: JPEG quality (1-100), default 85 for good balance
        """
        self.quality = quality
        self.dpi = PlatformSpecs.DPI
    
    def process_for_platform(
        self,
        image_path: str,
        platform: str,
        post_type: str,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Process image for specific platform and post type
        
        Args:
            image_path: Path to input image
            platform: 'facebook' or 'instagram'
            post_type: 'feed', 'story', etc.
            output_path: Optional output path
            
        Returns:
            Dict with processed image info
        """
        # Load image
        img = Image.open(image_path)
        
        # Get specs for platform
        specs = self._get_platform_specs(platform, post_type)
        if not specs:
            raise ValueError(f"Invalid platform/type: {platform}/{post_type}")
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize and crop
        img_processed = self._smart_resize_crop(img, specs['size'])
        
        # Optimize quality
        img_optimized = self._optimize_quality(img_processed, specs['max_size_mb'])
        
        # Generate output path if not provided
        if output_path is None:
            path = Path(image_path)
            output_path = str(path.parent / f"{path.stem}_{platform}_{post_type}.jpg")
        
        # Save with web optimization
        img_optimized.save(
            output_path,
            'JPEG',
            quality=self.quality,
            optimize=True,
            dpi=(self.dpi, self.dpi)
        )
        
        # Get file size
        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        
        return {
            'output_path': output_path,
            'dimensions': img_optimized.size,
            'file_size_mb': round(file_size_mb, 2),
            'format': 'JPEG',
            'dpi': self.dpi,
            'quality': self.quality
        }
    
    def _get_platform_specs(self, platform: str, post_type: str) -> Optional[Dict]:
        """Get specifications for platform and post type"""
        platform = platform.lower()
        post_type = post_type.lower()
        
        if platform == 'facebook':
            return PlatformSpecs.FACEBOOK.get(post_type)
        elif platform == 'instagram':
            return PlatformSpecs.INSTAGRAM.get(post_type)
        elif platform == 'x':
            return PlatformSpecs.X.get(post_type)
        elif platform == 'pinterest':
            return PlatformSpecs.PINTEREST.get(post_type)
        return None
    
    def _smart_resize_crop(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Smart resize and crop using content-aware approach
        
        Args:
            img: PIL Image object
            target_size: Target (width, height)
            
        Returns:
            Processed PIL Image
        """
        target_width, target_height = target_size
        target_ratio = target_width / target_height
        
        # Get current dimensions
        current_width, current_height = img.size
        current_ratio = current_width / current_height
        
        if abs(current_ratio - target_ratio) < 0.01:
            # Aspect ratio is close enough, just resize
            return img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Calculate dimensions for cropping
        if current_ratio > target_ratio:
            # Image is wider than target, crop width
            new_width = int(current_height * target_ratio)
            new_height = current_height
            left = (current_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = new_height
        else:
            # Image is taller than target, crop height
            new_width = current_width
            new_height = int(current_width / target_ratio)
            left = 0
            top = (current_height - new_height) // 2
            right = new_width
            bottom = top + new_height
        
        # Crop and resize
        img_cropped = img.crop((left, top, right, bottom))
        return img_cropped.resize(target_size, Image.Resampling.LANCZOS)
    
    def _optimize_quality(self, img: Image.Image, max_size_mb: float) -> Image.Image:
        """
        Optimize image quality to fit within size limit
        
        Args:
            img: PIL Image object
            max_size_mb: Maximum file size in MB
            
        Returns:
            Optimized PIL Image
        """
        # Try with current quality first
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG', quality=self.quality, optimize=True)
        size_mb = len(buffer.getvalue()) / (1024 * 1024)
        
        # If too large, reduce quality iteratively
        quality = self.quality
        while size_mb > max_size_mb and quality > 50:
            quality -= 5
            buffer = io.BytesIO()
            img.save(buffer, 'JPEG', quality=quality, optimize=True)
            size_mb = len(buffer.getvalue()) / (1024 * 1024)
        
        return img
    
    def batch_process(
        self,
        image_path: str,
        platforms: list,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        Process single image for multiple platforms
        
        Args:
            image_path: Path to input image
            platforms: List of dicts with 'platform' and 'post_type' keys
            output_dir: Optional output directory
            
        Returns:
            Dict with all processed images info
        """
        results = {}
        
        for platform_config in platforms:
            platform = platform_config['platform']
            post_type = platform_config['post_type']
            
            # Generate output path
            if output_dir:
                path = Path(image_path)
                output_path = str(Path(output_dir) / f"{path.stem}_{platform}_{post_type}.jpg")
            else:
                output_path = None
            
            try:
                result = self.process_for_platform(
                    image_path,
                    platform,
                    post_type,
                    output_path
                )
                results[f"{platform}_{post_type}"] = result
            except Exception as e:
                results[f"{platform}_{post_type}"] = {'error': str(e)}
        
        return results
    
    def get_image_info(self, image_path: str) -> Dict:
        """
        Get information about an image
        
        Args:
            image_path: Path to image
            
        Returns:
            Dict with image information
        """
        img = Image.open(image_path)
        
        return {
            'dimensions': img.size,
            'mode': img.mode,
            'format': img.format,
            'size_mb': Path(image_path).stat().st_size / (1024 * 1024),
            'aspect_ratio': img.size[0] / img.size[1]
        }


# Example usage
if __name__ == "__main__":
    processor = ImageProcessor(quality=85)
    
    # Process for Instagram feed
    result = processor.process_for_platform(
        "input_image.jpg",
        "instagram",
        "feed_square",
        "output_instagram_feed.jpg"
    )
    print(f"Processed: {result}")
    
    # Batch process for multiple platforms
    batch_results = processor.batch_process(
        "input_image.jpg",
        [
            {'platform': 'instagram', 'post_type': 'feed_square'},
            {'platform': 'instagram', 'post_type': 'story'},
            {'platform': 'facebook', 'post_type': 'feed'},
            {'platform': 'facebook', 'post_type': 'story'}
        ],
        output_dir="./processed"
    )
    print(f"Batch results: {batch_results}")
