# Social Media Automation API - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Image Processing](#image-processing)
6. [OAuth Flow](#oauth-flow)
7. [Rate Limits](#rate-limits)
8. [Error Handling](#error-handling)
9. [Meta App Review Guide](#meta-app-review-guide)
10. [Best Practices](#best-practices)

---

## Overview

The Social Media Automation API is a commercial-grade platform for automated content posting to Facebook and Instagram with AI-powered keyword extraction and intelligent image optimization.

### Key Features
- ✅ Multi-platform posting (Facebook & Instagram)
- ✅ AI-powered keyword extraction (Google Vision API)
- ✅ Automatic image optimization for each platform
- ✅ OAuth 2.0 authentication with PKCE
- ✅ Scheduled posting
- ✅ Batch processing
- ✅ Comprehensive analytics

### Base URL
```
Production: https://api.yourdomain.com
Staging: https://staging-api.yourdomain.com
```

---

## Getting Started

### 1. Create an Account
```bash
POST /api/v1/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### 2. Get Your API Key
After registration, retrieve your API key from the dashboard or via:
```bash
POST /api/v1/auth/login
```

### 3. Make Your First Request
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.yourdomain.com/api/v1/accounts
```

---

## Authentication

### API Key Authentication
All API requests require authentication using Bearer tokens:

```http
Authorization: Bearer YOUR_API_KEY
```

### OAuth 2.0 for Social Accounts
To connect Facebook/Instagram accounts, users must complete OAuth flow:

1. **Initiate OAuth**: `GET /api/v1/auth/connect/facebook`
2. **User authorizes** on Meta's platform
3. **Callback handled**: `GET /api/v1/auth/callback?code=...&state=...`
4. **Store tokens** securely in database

---

## API Endpoints

### Image Management

#### Upload Image
```http
POST /api/v1/upload
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

file: [image file]
```

**Response:**
```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "sunset.jpg",
  "file_size_mb": 2.5,
  "dimensions": [1920, 1080],
  "upload_timestamp": "2025-01-15T10:30:00Z"
}
```

**Supported Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)

**Size Limits:**
- Maximum: 10MB
- Recommended: 5MB or less

#### Extract Keywords
```http
GET /api/v1/keywords/{image_id}?max_keywords=10
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": [
    {
      "keyword": "sunset",
      "score": 0.95,
      "sources": ["label", "web_entity"],
      "occurrences": 2
    },
    {
      "keyword": "beach",
      "score": 0.88,
      "sources": ["label", "object"]
    }
  ],
  "hashtags": ["#Sunset", "#Beach", "#Ocean", "#Travel"],
  "total_detected": 15
}
```

### Post Management

#### Create Post
```http
POST /api/v1/posts
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "platforms": ["facebook", "instagram"],
  "post_types": {
    "facebook": "feed",
    "instagram": "feed_square"
  },
  "caption": "Amazing sunset at the beach! #sunset #beach",
  "image_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "scheduled_for": "2025-01-20T18:00:00Z",
  "auto_hashtags": true
}
```

**Post Types:**

**Facebook:**
- `feed` - Regular feed post (1200x630)
- `story` - Story post (1080x1920)

**Instagram:**
- `feed_square` - Square feed post (1080x1080)
- `feed_portrait` - Portrait feed post (1080x1350)
- `story` - Story post (1080x1920)
- `carousel` - Multiple images (requires multiple image_ids)

**Response:**
```json
{
  "post_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "scheduled",
  "platforms": ["facebook", "instagram"],
  "scheduled_for": "2025-01-20T18:00:00Z",
  "created_at": "2025-01-15T10:35:00Z"
}
```

#### Get Post Status
```http
GET /api/v1/posts/{post_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "post_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "posted",
  "platform_results": {
    "facebook": {
      "status": "success",
      "post_id": "123456789_987654321",
      "url": "https://facebook.com/123456789/posts/987654321",
      "posted_at": "2025-01-20T18:00:05Z"
    },
    "instagram": {
      "status": "success",
      "post_id": "18123456789012345",
      "url": "https://instagram.com/p/ABC123xyz",
      "posted_at": "2025-01-20T18:00:08Z"
    }
  },
  "created_at": "2025-01-15T10:35:00Z",
  "updated_at": "2025-01-20T18:00:10Z"
}
```

**Status Values:**
- `draft` - Post created but not scheduled
- `scheduled` - Scheduled for future posting
- `processing` - Currently being posted
- `posted` - Successfully posted to all platforms
- `failed` - Failed to post (check error_message)
- `cancelled` - Cancelled by user

#### Cancel Scheduled Post
```http
DELETE /api/v1/posts/{post_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "message": "Post cancelled successfully",
  "post_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Account Management

#### Connect Social Account
```http
POST /api/v1/auth/connect
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "platform": "facebook",
  "account_id": "123456789",
  "account_name": "My Business Page",
  "access_token": "EAAxxxxx...",
  "expires_at": "2025-03-15T00:00:00Z"
}
```

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "platform": "facebook",
  "account_name": "My Business Page",
  "connected_at": "2025-01-15T10:40:00Z",
  "status": "active"
}
```

#### List Connected Accounts
```http
GET /api/v1/accounts
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "platform": "facebook",
    "account_name": "My Business Page",
    "connected_at": "2025-01-15T10:40:00Z",
    "status": "active"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "platform": "instagram",
    "account_name": "@mybusiness",
    "connected_at": "2025-01-15T10:45:00Z",
    "status": "active"
  }
]
```

---

## Image Processing

### Platform-Specific Requirements

#### Facebook
| Post Type | Dimensions | Aspect Ratio | Max Size |
|-----------|------------|--------------|----------|
| Feed      | 1200x630   | 1.91:1       | 4MB      |
| Story     | 1080x1920  | 9:16         | 4MB      |
| Profile   | 180x180    | 1:1          | 4MB      |

#### Instagram
| Post Type      | Dimensions | Aspect Ratio | Max Size |
|----------------|------------|--------------|----------|
| Feed (Square)  | 1080x1080  | 1:1          | 8MB      |
| Feed (Portrait)| 1080x1350  | 4:5          | 8MB      |
| Story          | 1080x1920  | 9:16         | 8MB      |
| Reels          | 1080x1920  | 9:16         | 8MB      |

### Automatic Processing
The API automatically:
1. Resizes images to platform requirements
2. Crops with content-aware algorithms
3. Optimizes quality (72 DPI web standard)
4. Compresses to stay within size limits
5. Converts formats if needed

---

## OAuth Flow

### Step-by-Step Guide

#### 1. Initiate OAuth
```javascript
// Frontend code
window.location.href = `https://api.yourdomain.com/api/v1/auth/connect/facebook?user_id=${userId}`;
```

#### 2. User Authorizes
User is redirected to Facebook's authorization page and grants permissions.

#### 3. Handle Callback
```http
GET /api/v1/auth/callback?code=AUTH_CODE&state=STATE_TOKEN
```

The API automatically:
- Validates the state parameter (CSRF protection)
- Exchanges code for access token
- Retrieves user's Facebook pages
- Fetches connected Instagram accounts
- Stores encrypted tokens in database

#### 4. Tokens Stored
Long-lived tokens (60 days) are automatically stored and refreshed.

### Required Permissions

**Facebook:**
- `pages_show_list` - View pages
- `pages_read_engagement` - Read engagement
- `pages_manage_posts` - Create posts
- `pages_manage_engagement` - Manage interactions

**Instagram:**
- `instagram_basic` - Basic access
- `instagram_content_publish` - Publish content

---

## Rate Limits

### API Rate Limits

| Tier       | Requests/Minute | Requests/Hour | Posts/Month |
|------------|-----------------|---------------|-------------|
| Free       | 10              | 100           | 10          |
| Basic      | 30              | 500           | 100         |
| Pro        | 60              | 2000          | 1000        |
| Enterprise | Unlimited       | Unlimited     | Unlimited   |

### Platform Rate Limits

**Facebook:**
- 200 calls per hour per user
- 4800 calls per day per app

**Instagram:**
- 200 API calls per hour per user
- 25 posts per day per account

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642253400
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_IMAGE_FORMAT",
    "message": "Only JPEG, PNG, and GIF formats are supported",
    "details": {
      "received_format": "BMP",
      "supported_formats": ["JPEG", "PNG", "GIF"]
    }
  },
  "timestamp": "2025-01-15T10:50:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `PLATFORM_ERROR` | 502 | Social platform API error |
| `PROCESSING_ERROR` | 500 | Internal processing error |

---

## Meta App Review Guide

### Prerequisites

1. **Business Verification**
   - Complete Meta Business verification
   - Provide business documents
   - Verify business phone and address

2. **App Configuration**
   - Add privacy policy URL
   - Add terms of service URL
   - Configure data deletion callback
   - Set up webhook endpoints

### Required Documentation

#### 1. Privacy Policy
Must include:
- What data you collect
- How data is used
- How data is stored
- Data retention policy
- User rights (access, deletion)
- Contact information

#### 2. Terms of Service
Must include:
- Service description
- User responsibilities
- Acceptable use policy
- Termination conditions
- Liability limitations

#### 3. Data Deletion Instructions
Provide URL that handles data deletion requests:
```
https://yourdomain.com/data-deletion
```

### App Review Submission

#### Required Materials

1. **Screen Recording** (2-3 minutes)
   - Show complete OAuth flow
   - Demonstrate posting functionality
   - Show permission usage
   - Include audio narration

2. **Step-by-Step Instructions**
   ```
   1. Click "Connect Facebook Account"
   2. Log in with provided test account
   3. Authorize all requested permissions
   4. Upload an image
   5. Create a post to Facebook page
   6. View posted content on Facebook
   ```

3. **Test Credentials**
   - Test Facebook account email
   - Test account password
   - Test page name/ID

4. **Permission Justifications**
   
   **pages_manage_posts:**
   > "This permission is required to create and publish posts on behalf of the user's Facebook pages. Our service automates social media posting, and users explicitly choose when and what content to post."
   
   **instagram_content_publish:**
   > "This permission allows our service to publish content to users' Instagram Business accounts. Users maintain full control over content, scheduling, and can cancel posts at any time."

#### Review Process Timeline
- **Submission**: 1 day
- **Review**: 3-5 business days
- **Revisions** (if needed): 2-3 days
- **Total**: ~1-2 weeks

### Common Rejection Reasons

1. ❌ **Insufficient demonstration**
   - Solution: Provide clear, complete screen recording

2. ❌ **Missing business verification**
   - Solution: Complete Business Manager verification first

3. ❌ **Vague