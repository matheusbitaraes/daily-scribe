# Daily Scribe API Reference

This document provides comprehensive documentation for the Daily Scribe REST API, including endpoints, authentication, request/response formats, and integration examples.

## Base URL

**Development:** `http://localhost:8000`  
**Production:** `http://daily-scribe.duckdns.org/`

## Authentication

Daily Scribe uses JWT-based token authentication for user-specific operations. Tokens are generated server-side and provided to users via secure email links.

### Token Format
- **Type:** JSON Web Token (JWT)
- **Structure:** Three base64-encoded parts separated by dots
- **Lifetime:** Configurable (default: 50 requests or 7 days)
- **Scope:** User-specific preferences and data

### Authentication Methods

#### 1. Header-based Authentication (Recommended)
```http
Authorization: Bearer <token>
```

#### 2. Path Parameter Authentication
```http
GET /preferences/{token}
```

## Error Handling

### Standard Error Response
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {
    "field": "Additional context when applicable"
  }
}
```

### Common Error Codes
- `INVALID_TOKEN` - Token format is invalid
- `TOKEN_EXPIRED` - Token has expired or been exhausted
- `TOKEN_NOT_FOUND` - Token doesn't exist in the system
- `VALIDATION_ERROR` - Request data validation failed
- `DATABASE_ERROR` - Internal database error
- `NOT_FOUND` - Requested resource not found

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid authentication)
- `403` - Forbidden (token expired/exhausted)
- `404` - Not Found
- `500` - Internal Server Error

## API Endpoints

### Health & Monitoring

#### GET /healthz
**Purpose:** Application health check with system status

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-07T10:30:00Z",
  "service": "daily-scribe-api",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    }
  },
  "system": {
    "uptime_seconds": 86400,
    "memory_usage_mb": 256
  },
  "response_time_ms": 12
}
```

**Status Codes:**
- `200` - System healthy
- `503` - System unhealthy (database issues, etc.)

#### GET /metrics
**Purpose:** Prometheus-compatible metrics for monitoring

**Authentication:** None required

**Response Format:** Plain text (Prometheus format)
```
# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total 1234

# HELP database_queries_total Total database queries
# TYPE database_queries_total counter
database_queries_total 5678
```

### Articles & Content

#### GET /articles
**Purpose:** List articles with filtering and pagination

**Authentication:** None required

**Query Parameters:**
- `limit` (integer, optional): Number of articles to return (default: 50, max: 200)
- `offset` (integer, optional): Number of articles to skip (default: 0)
- `category` (string, optional): Filter by category
- `source_id` (integer, optional): Filter by source ID
- `date_from` (string, optional): Filter articles from date (YYYY-MM-DD)
- `date_to` (string, optional): Filter articles to date (YYYY-MM-DD)

**Example Request:**
```http
GET /articles?limit=10&category=technology&date_from=2025-09-01
```

**Response:**
```json
{
  "articles": [
    {
      "id": 123,
      "title": "Example Article Title",
      "summary": "Article summary in Portuguese...",
      "summary_en": "Article summary in English...",
      "url": "https://example.com/article",
      "published_date": "2025-09-07T08:00:00Z",
      "created_at": "2025-09-07T08:30:00Z",
      "category": "technology",
      "source_id": 1,
      "source_name": "TechCrunch"
    }
  ],
  "total": 150,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

#### GET /articles/{article_id}
**Purpose:** Get specific article details

**Authentication:** None required

**Path Parameters:**
- `article_id` (integer): Article ID

**Response:**
```json
{
  "id": 123,
  "title": "Example Article Title",
  "summary": "Detailed article summary...",
  "summary_en": "English summary...",
  "content": "Full article content...",
  "url": "https://example.com/article",
  "published_date": "2025-09-07T08:00:00Z",
  "created_at": "2025-09-07T08:30:00Z",
  "category": "technology",
  "source": {
    "id": 1,
    "name": "TechCrunch",
    "url": "https://techcrunch.com/feed"
  }
}
```

#### GET /categories
**Purpose:** List available article categories

**Authentication:** None required

**Response:**
```json
{
  "categories": [
    {
      "name": "technology",
      "display_name": "Technology",
      "article_count": 45
    },
    {
      "name": "business",
      "display_name": "Business",
      "article_count": 32
    }
  ]
}
```

#### GET /sources
**Purpose:** List RSS feed sources

**Authentication:** None required

**Response:**
```json
{
  "sources": [
    {
      "id": 1,
      "name": "TechCrunch",
      "url": "https://techcrunch.com/feed",
      "category": "technology",
      "enabled": true,
      "article_count": 25,
      "last_updated": "2025-09-07T09:00:00Z"
    }
  ]
}
```

### Digest Management

#### GET /digest/simulate
**Purpose:** Generate digest preview for specified user

**Authentication:** None required (uses user_email parameter)

**Query Parameters:**
- `user_email` (string, required): User email address
- `date` (string, optional): Target date for digest (YYYY-MM-DD, defaults to today)
- `categories` (array, optional): Filter by categories
- `source_ids` (array, optional): Filter by source IDs

**Example Request:**
```http
GET /digest/simulate?user_email=user@example.com&date=2025-09-07&categories=technology,business
```

**Response:**
```json
{
  "success": true,
  "digest_html": "<html>...</html>",
  "metadata": {
    "date": "2025-09-07",
    "user_email": "user@example.com",
    "total_articles": 25,
    "total_clusters": 8,
    "categories_included": ["technology", "business"],
    "sources_included": [1, 2, 3],
    "generation_time_ms": 1234
  }
}
```

#### GET /digest/available-dates
**Purpose:** Get dates with available articles for digest generation

**Authentication:** None required

**Query Parameters:**
- `start_date` (string, optional): Filter from date (YYYY-MM-DD)
- `end_date` (string, optional): Filter to date (YYYY-MM-DD)
- `limit` (integer, optional): Maximum dates to return (default: 30)

**Response:**
```json
{
  "success": true,
  "dates": [
    {
      "date": "2025-09-07",
      "article_count": 25,
      "category_count": 6
    },
    {
      "date": "2025-09-06",
      "article_count": 18,
      "category_count": 4
    }
  ],
  "total": 150,
  "oldest_date": "2025-01-01",
  "newest_date": "2025-09-07"
}
```

#### GET /digest/metadata/{target_date}
**Purpose:** Get digest metadata for specific date

**Authentication:** None required

**Path Parameters:**
- `target_date` (string): Date in YYYY-MM-DD format

**Response:**
```json
{
  "success": true,
  "date": "2025-09-07",
  "total_articles": 25,
  "categories": {
    "technology": 10,
    "business": 8,
    "science": 7
  },
  "sources": {
    "TechCrunch": 12,
    "BBC News": 8,
    "Reuters": 5
  },
  "clusters": [
    {
      "main_topic": "AI Development",
      "article_count": 4,
      "representative_title": "New AI Model Breakthrough"
    }
  ]
}
```

### User Preferences

#### GET /preferences/{token}
**Purpose:** Retrieve user preferences

**Authentication:** Token required (path parameter)

**Response:**
```json
{
  "user_email": "user@example.com",
  "enabled_sources": [1, 2, 3],
  "enabled_categories": ["technology", "business"],
  "keywords": ["AI", "blockchain", "startup"],
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-07T08:00:00Z",
  "token_usage": {
    "requests_made": 5,
    "requests_remaining": 45,
    "expires_at": "2025-09-14T10:00:00Z"
  }
}
```

#### PUT /preferences/{token}
**Purpose:** Update user preferences

**Authentication:** Token required (path parameter)

**Request Body:**
```json
{
  "enabled_sources": [1, 2, 4],
  "enabled_categories": ["technology", "science"],
  "keywords": ["AI", "machine learning"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preferences updated successfully",
  "updated_fields": ["enabled_sources", "keywords"],
  "user_email": "user@example.com",
  "updated_at": "2025-09-07T10:30:00Z"
}
```

#### POST /preferences/{token}/reset
**Purpose:** Reset user preferences to defaults

**Authentication:** Token required (path parameter)

**Response:**
```json
{
  "success": true,
  "message": "Preferences reset to defaults",
  "reset_at": "2025-09-07T10:30:00Z",
  "default_preferences": {
    "enabled_sources": [1, 2, 3, 4, 5],
    "enabled_categories": ["technology", "business", "science"],
    "keywords": []
  }
}
```

#### GET /preferences/{token}/available-options
**Purpose:** Get available sources and categories for preference configuration

**Authentication:** Token required (path parameter)

**Response:**
```json
{
  "sources": [
    {
      "id": 1,
      "name": "TechCrunch",
      "category": "technology",
      "article_count": 25
    }
  ],
  "categories": [
    {
      "name": "technology",
      "display_name": "Technology",
      "source_count": 3,
      "article_count": 45
    }
  ]
}
```

## Rate Limiting

### Token-based Rate Limiting
- **Default Limit:** 50 requests per token
- **Time Window:** 7 days from token creation
- **Headers:** Token usage information included in response headers

**Response Headers:**
```http
X-Token-Requests-Remaining: 45
X-Token-Expires-At: 2025-09-14T10:00:00Z
```

### IP-based Rate Limiting (Future)
- **Limit:** 1000 requests per hour per IP
- **Burst:** 50 requests per minute per IP

## Integration Examples

### JavaScript/Axios Example
```javascript
const API_BASE_URL = 'https://your-domain.com';

// Get available dates
async function getAvailableDates() {
  try {
    const response = await axios.get(`${API_BASE_URL}/digest/available-dates`);
    return response.data;
  } catch (error) {
    console.error('API Error:', error.response?.data);
    throw error;
  }
}

// Update user preferences with token
async function updatePreferences(token, preferences) {
  try {
    const response = await axios.put(
      `${API_BASE_URL}/preferences/${token}`,
      preferences,
      {
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      throw new Error('Token expired or exhausted');
    }
    throw error;
  }
}
```

### Python/Requests Example
```python
import requests

API_BASE_URL = 'https://your-domain.com'

def get_user_preferences(token):
    """Get user preferences with error handling."""
    try:
        response = requests.get(f'{API_BASE_URL}/preferences/{token}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            raise Exception('Token expired or exhausted')
        elif e.response.status_code == 404:
            raise Exception('Token not found')
        else:
            raise Exception(f'API error: {e.response.text}')

def simulate_digest(user_email, date=None):
    """Generate digest simulation."""
    params = {'user_email': user_email}
    if date:
        params['date'] = date
    
    response = requests.get(f'{API_BASE_URL}/digest/simulate', params=params)
    response.raise_for_status()
    return response.json()
```

### cURL Examples
```bash
# Health check
curl -X GET "https://your-domain.com/healthz"

# Get articles with filtering
curl -X GET "https://your-domain.com/articles?category=technology&limit=5"

# Simulate digest
curl -X GET "https://your-domain.com/digest/simulate?user_email=user@example.com&date=2025-09-07"

# Get user preferences
curl -X GET "https://your-domain.com/preferences/your-token-here"

# Update preferences
curl -X PUT "https://your-domain.com/preferences/your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"enabled_categories": ["technology", "business"]}'
```

## Webhooks (Future Feature)

### Digest Generated Webhook
**Purpose:** Notify external systems when a digest is generated

**Payload:**
```json
{
  "event": "digest.generated",
  "timestamp": "2025-09-07T10:00:00Z",
  "data": {
    "user_email": "user@example.com",
    "date": "2025-09-07",
    "article_count": 25,
    "digest_id": "digest-123"
  }
}
```

## API Versioning

Currently, the API is unversioned (v1 implicit). Future versions will use URL-based versioning:
- `/v1/articles` (current)
- `/v2/articles` (future)

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI Spec:** `/openapi.json`

## Support and Troubleshooting

### Common Issues

1. **CORS Errors:** Ensure your domain is properly configured in the CORS settings
2. **Token Validation:** Verify token format (JWT with 3 parts) and expiration
3. **Rate Limiting:** Check token usage in response headers
4. **Date Formats:** Use ISO format (YYYY-MM-DD) for all date parameters

### Getting Help

- **GitHub Issues:** Create an issue for bugs or feature requests
- **API Status:** Check `/healthz` endpoint for system status
- **Logs:** Enable debug logging for detailed error information

---

**Last Updated:** September 7, 2025  
**API Version:** 1.0.0
