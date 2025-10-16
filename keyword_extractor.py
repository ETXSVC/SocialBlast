"""
AI Keyword Extraction Module using Google Vision API
Extracts relevant keywords from images for social media posts
"""

from google.cloud import vision
from typing import List, Dict, Optional
import os
from collections import Counter
import re


class KeywordExtractor:
    """
    Extracts keywords from images using Google Vision API
    Features:
    - Label detection (objects, scenes)
    - Text detection (OCR)
    - Web entity detection
    - Relevance scoring
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Vision API client
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
        """
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.client = vision.ImageAnnotatorClient()
        
        # Stop words to filter out
        self.stop_words = {
            'image', 'photo', 'picture', 'snapshot', 'photograph',
            'jpeg', 'jpg', 'png', 'file', 'digital', 'camera'
        }
    
    def extract_keywords(
        self,
        image_path: str,
        max_keywords: int = 10,
        min_score: float = 0.5
    ) -> Dict:
        """
        Extract top keywords from an image
        
        Args:
            image_path: Path to image file
            max_keywords: Maximum number of keywords to return
            min_score: Minimum confidence score (0-1)
            
        Returns:
            Dict with keywords and metadata
        """
        # Read image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Collect all keywords from different detection methods
        all_keywords = []
        
        # 1. Label Detection (objects, scenes, concepts)
        labels = self._detect_labels(image, min_score)
        all_keywords.extend(labels)
        
        # 2. Text Detection (OCR for text in image)
        text_keywords = self._detect_text(image)
        all_keywords.extend(text_keywords)
        
        # 3. Web Entity Detection (related concepts)
        web_entities = self._detect_web_entities(image, min_score)
        all_keywords.extend(web_entities)
        
        # 4. Object Localization (specific objects with locations)
        objects = self._detect_objects(image, min_score)
        all_keywords.extend(objects)
        
        # Process and rank keywords
        top_keywords = self._rank_keywords(all_keywords, max_keywords)
        
        return {
            'keywords': top_keywords,
            'total_detected': len(all_keywords),
            'sources': {
                'labels': len(labels),
                'text': len(text_keywords),
                'web_entities': len(web_entities),
                'objects': len(objects)
            }
        }
    
    def _detect_labels(self, image: vision.Image, min_score: float) -> List[Dict]:
        """Detect labels (objects, scenes, activities)"""
        response = self.client.label_detection(image=image)
        labels = response.label_annotations
        
        keywords = []
        for label in labels:
            if label.score >= min_score:
                keywords.append({
                    'keyword': label.description.lower(),
                    'score': label.score,
                    'source': 'label'
                })
        
        return keywords
    
    def _detect_text(self, image: vision.Image) -> List[Dict]:
        """Detect and extract text from image"""
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        
        keywords = []
        if texts:
            # First annotation contains full detected text
            full_text = texts[0].description
            
            # Extract meaningful words (3+ characters, alphanumeric)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', full_text.lower())
            
            # Filter stop words
            words = [w for w in words if w not in self.stop_words]
            
            # Count frequency and create keyword entries
            word_counts = Counter(words)
            for word, count in word_counts.most_common(5):  # Top 5 text keywords
                keywords.append({
                    'keyword': word,
                    'score': min(1.0, count * 0.3),  # Boost repeated words
                    'source': 'text'
                })
        
        return keywords
    
    def _detect_web_entities(self, image: vision.Image, min_score: float) -> List[Dict]:
        """Detect web entities (concepts found on the web)"""
        response = self.client.web_detection(image=image)
        entities = response.web_detection.web_entities
        
        keywords = []
        for entity in entities:
            if entity.score >= min_score and entity.description:
                keywords.append({
                    'keyword': entity.description.lower(),
                    'score': entity.score,
                    'source': 'web_entity'
                })
        
        return keywords
    
    def _detect_objects(self, image: vision.Image, min_score: float) -> List[Dict]:
        """Detect and localize objects in the image"""
        response = self.client.object_localization(image=image)
        objects = response.localized_object_annotations
        
        keywords = []
        for obj in objects:
            if obj.score >= min_score:
                keywords.append({
                    'keyword': obj.name.lower(),
                    'score': obj.score,
                    'source': 'object'
                })
        
        return keywords
    
    def _rank_keywords(self, keywords: List[Dict], max_keywords: int) -> List[Dict]:
        """
        Rank and deduplicate keywords
        
        Args:
            keywords: List of keyword dicts with 'keyword', 'score', 'source'
            max_keywords: Maximum number to return
            
        Returns:
            Ranked list of top keywords
        """
        # Group by keyword and calculate combined score
        keyword_map = {}
        
        for kw in keywords:
            word = kw['keyword']
            
            # Skip stop words and very short words
            if word in self.stop_words or len(word) < 3:
                continue
            
            if word not in keyword_map:
                keyword_map[word] = {
                    'keyword': word,
                    'score': 0,
                    'sources': [],
                    'count': 0
                }
            
            # Boost score based on source diversity
            keyword_map[word]['score'] += kw['score']
            keyword_map[word]['count'] += 1
            if kw['source'] not in keyword_map[word]['sources']:
                keyword_map[word]['sources'].append(kw['source'])
        
        # Calculate final scores (average * source diversity bonus)
        ranked = []
        for word, data in keyword_map.items():
            avg_score = data['score'] / data['count']
            source_bonus = len(data['sources']) * 0.1
            final_score = min(1.0, avg_score + source_bonus)
            
            ranked.append({
                'keyword': word,
                'score': round(final_score, 3),
                'sources': data['sources'],
                'occurrences': data['count']
            })
        
        # Sort by score and return top N
        ranked.sort(key=lambda x: x['score'], reverse=True)
        return ranked[:max_keywords]
    
    def generate_hashtags(self, keywords: List[Dict], max_hashtags: int = 10) -> List[str]:
        """
        Convert keywords to hashtags
        
        Args:
            keywords: List of keyword dicts
            max_hashtags: Maximum number of hashtags
            
        Returns:
            List of hashtags
        """
        hashtags = []
        
        for kw in keywords[:max_hashtags]:
            # Convert to hashtag format (remove spaces, capitalize words)
            keyword = kw['keyword']
            
            # Handle multi-word keywords
            if ' ' in keyword:
                hashtag = '#' + ''.join(word.capitalize() for word in keyword.split())
            else:
                hashtag = '#' + keyword.capitalize()
            
            hashtags.append(hashtag)
        
        return hashtags
    
    def extract_with_context(
        self,
        image_path: str,
        user_caption: Optional[str] = None,
        max_keywords: int = 10
    ) -> Dict:
        """
        Extract keywords with additional context from user caption
        
        Args:
            image_path: Path to image
            user_caption: Optional user-provided caption
            max_keywords: Maximum keywords to return
            
        Returns:
            Enhanced keyword results
        """
        # Get base keywords from image
        result = self.extract_keywords(image_path, max_keywords)
        
        # If user provided caption, extract additional keywords
        if user_caption:
            caption_keywords = self._extract_from_text(user_caption)
            result['caption_keywords'] = caption_keywords
            
            # Merge with image keywords
            combined = result['keywords'] + caption_keywords
            result['keywords'] = self._rank_keywords(combined, max_keywords)
        
        # Generate hashtags
        result['hashtags'] = self.generate_hashtags(result['keywords'])
        
        return result
    
    def _extract_from_text(self, text: str) -> List[Dict]:
        """Extract keywords from text caption"""
        # Simple extraction - remove hashtags, mentions, URLs
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'http\S+', '', text)
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.stop_words]
        
        # Count frequency
        word_counts = Counter(words)
        
        keywords = []
        for word, count in word_counts.most_common(5):
            keywords.append({
                'keyword': word,
                'score': min(1.0, count * 0.3),
                'source': 'caption',
                'occurrences': count
            })
        
        return keywords


# Example usage
if __name__ == "__main__":
    # Initialize with credentials
    extractor = KeywordExtractor(credentials_path="path/to/credentials.json")
    
    # Extract keywords from image
    result = extractor.extract_keywords(
        "sample_image.jpg",
        max_keywords=10,
        min_score=0.6
    )
    
    print("Top Keywords:")
    for kw in result['keywords']:
        print(f"  {kw['keyword']}: {kw['score']} (from {', '.join(kw['sources'])})")
    
    print(f"\nTotal detected: {result['total_detected']}")
    print(f"Sources breakdown: {result['sources']}")
    
    # Extract with user caption
    enhanced = extractor.extract_with_context(
        "sample_image.jpg",
        user_caption="Beautiful sunset at the beach! #vacation #travel",
        max_keywords=10
    )
    
    print("\nGenerated Hashtags:")
    print(' '.join(enhanced['hashtags']))
