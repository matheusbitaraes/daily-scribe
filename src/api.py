from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import time
import sys
import os
import shutil

from fastapi import FastAPI, Query, HTTPException, Path, Request, Depends, status, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials

from components.database import DatabaseService
from components.digest_service import DigestService
from components.security.token_manager import SecureTokenManager, TokenValidationResult
from middleware.auth import require_valid_token, require_valid_path_token, get_auth_middleware, security
from models.preferences import (
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    PreferenceResetResponse,
    ErrorResponse,
    AvailableOptionsResponse
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Metrics collection for monitoring
app_metrics = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "errors_total": 0,
    "database_queries_total": 0,
    "database_query_duration_total": 0.0,
    "articles_processed_total": 0,
    "digests_generated_total": 0,
    "start_time": time.time()
}

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    # Increment request counter
    app_metrics["requests_total"] += 1
    
    # Track requests by endpoint
    endpoint = f"{request.method} {request.url.path}"
    app_metrics["requests_by_endpoint"][endpoint] = app_metrics["requests_by_endpoint"].get(endpoint, 0) + 1
    
    try:
        response = await call_next(request)
        
        # Track errors
        if response.status_code >= 400:
            app_metrics["errors_total"] += 1
            
        return response
    except Exception as e:
        app_metrics["errors_total"] += 1
        raise

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_service = DatabaseService()


@app.get("/healthz")
def health_check() -> JSONResponse:
    """
    Health check endpoint for monitoring and load balancer integration.
    
    Returns:
        JSONResponse: HTTP 200 if healthy, HTTP 503 if unhealthy
    """
    start_time = time.time()
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "daily-scribe-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    try:
        # Test database connectivity with a simple query
        db_start = time.time()
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] != 1:
                raise Exception("Database query returned unexpected result")
        
        db_time = time.time() - db_start
        health_data["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time * 1000, 2)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        
        # Return 503 Service Unavailable when database is down
        response_time = round((time.time() - start_time) * 1000, 2)
        health_data["response_time_ms"] = response_time
        return JSONResponse(
            status_code=503,
            content=health_data
        )
    
    # Add basic system information
    health_data["system"] = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "pid": os.getpid()
    }
    
    # Calculate total response time
    response_time = round((time.time() - start_time) * 1000, 2)
    health_data["response_time_ms"] = response_time
    
    return JSONResponse(
        status_code=200,
        content=health_data
    )


@app.get("/metrics", response_class=PlainTextResponse)
def get_metrics():
    """
    Prometheus metrics endpoint for monitoring.
    
    Returns metrics in Prometheus exposition format.
    """
    try:
        # Calculate uptime
        uptime_seconds = time.time() - app_metrics["start_time"]
        
        # Get system metrics
        disk_usage = shutil.disk_usage(".")
        disk_total = disk_usage.total
        disk_free = disk_usage.free
        disk_used = disk_total - disk_free
        disk_usage_percent = (disk_used / disk_total) * 100 if disk_total > 0 else 0
        
        # Build Prometheus metrics
        metrics_lines = [
            "# HELP daily_scribe_requests_total Total number of HTTP requests",
            "# TYPE daily_scribe_requests_total counter",
            f"daily_scribe_requests_total {app_metrics['requests_total']}",
            "",
            "# HELP daily_scribe_errors_total Total number of HTTP errors",
            "# TYPE daily_scribe_errors_total counter", 
            f"daily_scribe_errors_total {app_metrics['errors_total']}",
            "",
            "# HELP daily_scribe_database_queries_total Total number of database queries",
            "# TYPE daily_scribe_database_queries_total counter",
            f"daily_scribe_database_queries_total {app_metrics['database_queries_total']}",
            "",
            "# HELP daily_scribe_database_query_duration_seconds Total time spent on database queries",
            "# TYPE daily_scribe_database_query_duration_seconds counter",
            f"daily_scribe_database_query_duration_seconds {app_metrics['database_query_duration_total']:.2f}",
            "",
            "# HELP daily_scribe_articles_processed_total Total number of articles processed",
            "# TYPE daily_scribe_articles_processed_total counter",
            f"daily_scribe_articles_processed_total {app_metrics['articles_processed_total']}",
            "",
            "# HELP daily_scribe_digests_generated_total Total number of digests generated",
            "# TYPE daily_scribe_digests_generated_total counter",
            f"daily_scribe_digests_generated_total {app_metrics['digests_generated_total']}",
            "",
            "# HELP daily_scribe_uptime_seconds Application uptime in seconds",
            "# TYPE daily_scribe_uptime_seconds gauge",
            f"daily_scribe_uptime_seconds {uptime_seconds:.2f}",
            "",
            "# HELP daily_scribe_disk_usage_percent Disk usage percentage",
            "# TYPE daily_scribe_disk_usage_percent gauge",
            f"daily_scribe_disk_usage_percent {disk_usage_percent:.2f}",
            "",
            "# HELP daily_scribe_disk_free_bytes Free disk space in bytes",
            "# TYPE daily_scribe_disk_free_bytes gauge",
            f"daily_scribe_disk_free_bytes {disk_free}",
            "",
            "# HELP daily_scribe_info Application information",
            "# TYPE daily_scribe_info gauge",
            f'daily_scribe_info{{version="1.0.0",python_version="{sys.version.split()[0]}",platform="{sys.platform}"}} 1',
            ""
        ]
        
        # Add per-endpoint request metrics
        if app_metrics["requests_by_endpoint"]:
            metrics_lines.extend([
                "# HELP daily_scribe_requests_by_endpoint_total Requests by endpoint",
                "# TYPE daily_scribe_requests_by_endpoint_total counter"
            ])
            for endpoint, count in app_metrics["requests_by_endpoint"].items():
                method, path = endpoint.split(" ", 1)
                metrics_lines.append(f'daily_scribe_requests_by_endpoint_total{{method="{method}",path="{path}"}} {count}')
            metrics_lines.append("")
        
        # Check database health for metrics
        try:
            db_start = time.time()
            with db_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_query_time = time.time() - db_start
            
            app_metrics["database_queries_total"] += 1
            app_metrics["database_query_duration_total"] += db_query_time
            
            metrics_lines.extend([
                "# HELP daily_scribe_database_health Database connectivity status",
                "# TYPE daily_scribe_database_health gauge",
                "daily_scribe_database_health 1",
                "",
                "# HELP daily_scribe_database_last_query_duration_seconds Last database query duration",
                "# TYPE daily_scribe_database_last_query_duration_seconds gauge",
                f"daily_scribe_database_last_query_duration_seconds {db_query_time:.4f}",
                ""
            ])
        except Exception as e:
            logger.warning(f"Database health check failed in metrics: {e}")
            metrics_lines.extend([
                "# HELP daily_scribe_database_health Database connectivity status",
                "# TYPE daily_scribe_database_health gauge",
                "daily_scribe_database_health 0",
                ""
            ])
        
        return "\n".join(metrics_lines)
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"# Error generating metrics: {e}\n"

@api_router.get("/articles")
def get_articles(
    category: Optional[str] = Query(None),
    source_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Get all articles, with optional filtering by category and source_id.
    """
    categories = [category] if category else None
    source_ids = [source_id] if source_id else None
    articles = db_service.get_articles(
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        categories=categories,
        source_ids=source_ids,
        limit=limit,
        offset=offset,
    )
    return articles

@api_router.get("/articles/{article_id}")
def get_article(article_id: int):
    """
    Get details for a single article by ID.
    """
    article = db_service.get_article_by_id(article_id)
    if not article:
        return {"error": "Article not found"}
    return article

@api_router.get("/categories")
def get_categories():
    """
    Get all unique categories from articles.
    """
    articles = db_service.get_articles()
    categories = sorted(set(a.get('category') for a in articles if a.get('category')))
    return categories

@api_router.get("/sources")
def get_sources():
    """
    Get all unique source IDs from articles.
    """
    articles = db_service.get_articles()
    sources = sorted(set(str(a.get('source_id')) for a in articles if a.get('source_id') is not None))
    return sources


@api_router.get("/user/preferences")
def get_user_preferences(
    user_email: str = Query(..., description="User email address to get preferences for")
):
    """
    Get user preferences including enabled categories, sources, and settings.
    Returns default preferences if none are set for the user.
    """
    try:
        preferences = db_service.get_user_preferences(user_email)

        print(preferences)
        
        # If no preferences are found, return sensible defaults
        if not preferences:
            # Get available categories and sources to provide defaults
            articles = db_service.get_articles()
            all_categories = sorted(set(a.get('category') for a in articles if a.get('category')))
            all_sources = sorted(set(str(a.get('source_id')) for a in articles if a.get('source_id') is not None))
            
            # Default to enabling some common categories
            default_categories = []
            for cat in ['technology', 'business', 'science', 'health']:
                if cat in all_categories:
                    default_categories.append(cat)
            
            return {
                "user_email": user_email,
                "enabled_categories": default_categories,
                "enabled_sources": all_sources,  # Enable all sources by default
                "max_news_per_category": 10,
                "keywords": [],
                "is_default": True
            }
        
        return {
            "user_email": user_email,
            "enabled_categories": preferences.get('enabled_categories', []),
            "enabled_sources": preferences.get('enabled_sources', []),
            "max_news_per_category": preferences.get('max_news_per_category', 10),
            "keywords": preferences.get('keywords', []),
            "is_default": False
        }
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while getting user preferences: {str(e)}"
        )


@api_router.get("/digest/simulate")
def simulate_digest(
    user_email: str = Query(..., description="User email address for personalization"),
):
    """
    Simulate the generation of a digest for a user.
    Returns HTML content identical to what would be sent via email.
    """
    try:
        # Use the existing DigestService to generate digest for user
        digest_service = DigestService()
        result = digest_service.generate_digest_for_user(user_email)
        
        if not result["success"]:
            return {
                "success": False,
                "html_content": "",
                "metadata": {
                    "user_email": user_email,
                    "article_count": 0,
                    "clusters": 0
                },
                "message": result["message"]
            }
        
        return {
            "success": True,
            "html_content": result["html_content"],
            "metadata": result["metadata"],
            "message": result["message"]
        }
        
    except Exception as e:
        logger.error(f"Error generating digest simulation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating digest: {str(e)}"
        )


@api_router.get("/digest/available-dates")
def get_available_dates(
    start_date: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    """
    Get all dates that have articles available for digest generation.
    Returns dates in descending order (newest first).
    """
    try:
        # Build SQL query to get distinct dates with articles
        query = """
            SELECT DISTINCT DATE(published_at) as article_date, COUNT(*) as article_count
            FROM articles 
            WHERE summary IS NOT NULL 
            AND published_at IS NOT NULL
        """
        params = []
        
        # Add optional date range filters
        if start_date:
            query += " AND DATE(published_at) >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND DATE(published_at) <= ?"
            params.append(end_date.isoformat())
        
        query += " GROUP BY DATE(published_at) ORDER BY article_date DESC"
        
        # Execute query
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
        
        # Format results
        available_dates = []
        for row in results:
            article_date, article_count = row
            if article_date:  # Ensure date is not None
                available_dates.append({
                    "date": article_date,
                    "article_count": article_count
                })
        
        return {
            "success": True,
            "dates": available_dates,
            "total_dates": len(available_dates),
            "message": f"Found {len(available_dates)} dates with available articles."
        }
        
    except Exception as e:
        logger.error(f"Error fetching available dates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching available dates: {str(e)}"
        )


@api_router.get("/digest/metadata/{target_date}")
def get_digest_metadata(
    target_date: str = Path(..., description="Target date in YYYY-MM-DD format"),
):
    """
    Get metadata about articles available for a specific date.
    Returns article counts, category distribution, and source breakdown.
    """
    try:
        # Validate date format
        try:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD format."
            )
        
        # Create date range for the target date (full day)
        start_date = date_obj.isoformat()
        end_date = (date_obj + timedelta(days=1)).isoformat()
        
        # Get articles for the target date
        articles = db_service.get_articles(
            start_date=start_date,
            end_date=end_date,
            limit=10000  # High limit to get all articles for the date
        )
        
        if not articles:
            return {
                "success": True,
                "target_date": target_date,
                "total_articles": 0,
                "categories": {},
                "sources": {},
                "message": f"No articles found for date {target_date}."
            }
        
        # Calculate category distribution
        category_counts = {}
        for article in articles:
            category = article.get('category', 'Other') or 'Other'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate source distribution
        source_counts = {}
        for article in articles:
            source_name = article.get('source_name', 'Unknown') or 'Unknown'
            source_id = article.get('source_id')
            source_key = f"{source_name} (ID: {source_id})" if source_id else source_name
            source_counts[source_key] = source_counts.get(source_key, 0) + 1
        
        # Get processing timestamps (min and max)
        processed_times = [article.get('processed_at') for article in articles if article.get('processed_at')]
        published_times = [article.get('published_at') for article in articles if article.get('published_at')]
        
        metadata = {
            "success": True,
            "target_date": target_date,
            "total_articles": len(articles),
            "categories": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)),
            "sources": dict(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)),
            "timestamps": {
                "earliest_published": min(published_times) if published_times else None,
                "latest_published": max(published_times) if published_times else None,
                "earliest_processed": min(processed_times) if processed_times else None,
                "latest_processed": max(processed_times) if processed_times else None,
            },
            "message": f"Found {len(articles)} articles for {target_date} across {len(category_counts)} categories and {len(source_counts)} sources."
        }
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching digest metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching digest metadata: {str(e)}"
        )

# =============================================================================
# PREFERENCE MANAGEMENT ENDPOINTS
# =============================================================================

@api_router.get(
    "/preferences/{token}",
    response_model=UserPreferencesResponse,
    responses={
        200: {"description": "User preferences retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or missing token"},
        403: {"model": ErrorResponse, "description": "Token expired or exhausted"},
        404: {"model": ErrorResponse, "description": "User preferences not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get User Preferences",
    description="Retrieve user's email preference configuration using a secure token."
)
async def get_user_preferences(
    token: str = Path(..., description="Secure preference access token"),
    request: Request = None,
    token_validation: TokenValidationResult = Depends(require_valid_path_token)
) -> UserPreferencesResponse:
    """
    Retrieve user preferences with token validation.
    
    Args:
        token: Secure preference access token
        request: FastAPI request object
        token_validation: Token validation result from middleware
        
    Returns:
        UserPreferencesResponse: User's current preferences
        
    Raises:
        HTTPException: If user preferences not found or other errors
    """
    try:
        # Get user preferences from database
        user_prefs = db_service.get_user_preferences_by_email(token_validation.user_email)
        
        if not user_prefs:
            logger.error(f"User preferences not found for email: {token_validation.user_email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="PREFERENCES_NOT_FOUND",
                    message="User preferences not found"
                ).dict()
            )
        
        # Parse comma-separated fields
        enabled_sources = []
        if user_prefs.get('enabled_sources'):
            enabled_sources = [int(s.strip()) for s in user_prefs['enabled_sources'].split(',') if s.strip()]
        
        enabled_categories = []
        if user_prefs.get('enabled_categories'):
            enabled_categories = [c.strip() for c in user_prefs['enabled_categories'].split(',') if c.strip()]
        
        keywords = []
        if user_prefs.get('keywords'):
            keywords = [k.strip() for k in user_prefs['keywords'].split(',') if k.strip()]
        
        return UserPreferencesResponse(
            email_address=user_prefs['email_address'],
            enabled_sources=enabled_sources,
            enabled_categories=enabled_categories,
            keywords=keywords,
            max_news_per_category=user_prefs.get('max_news_per_category', 10),
            updated_at=user_prefs.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="RETRIEVAL_ERROR",
                message="Unable to retrieve user preferences"
            ).dict()
        )


@api_router.put(
    "/preferences/{token}",
    response_model=UserPreferencesResponse,
    responses={
        200: {"description": "User preferences updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Invalid or missing token"},
        403: {"model": ErrorResponse, "description": "Token expired or exhausted"},
        404: {"model": ErrorResponse, "description": "User preferences not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Update User Preferences",
    description="Update user's email preference configuration using a secure token."
)
async def update_user_preferences(
    token: str = Path(..., description="Secure preference access token"),
    preferences: UserPreferencesUpdateRequest = Body(..., description="Updated preference values"),
    request: Request = None,
    token_validation: TokenValidationResult = Depends(require_valid_path_token)
) -> UserPreferencesResponse:
    """
    Update user preferences with token validation.
    
    Args:
        token: Secure preference access token
        preferences: Updated preference values
        request: FastAPI request object
        token_validation: Token validation result from middleware
        
    Returns:
        UserPreferencesResponse: Updated user preferences
        
    Raises:
        HTTPException: If update fails or validation errors
    """
    try:
        # Get current preferences
        current_prefs = db_service.get_user_preferences_by_email(token_validation.user_email)
        
        if not current_prefs:
            logger.error(f"User preferences not found for email: {token_validation.user_email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="PREFERENCES_NOT_FOUND",
                    message="User preferences not found"
                ).dict()
            )
        
        # Prepare update data
        update_data = {}
        
        if preferences.enabled_sources is not None:
            update_data['enabled_sources'] = ','.join(str(source_id) for source_id in preferences.enabled_sources)
        
        if preferences.enabled_categories is not None:
            update_data['enabled_categories'] = ','.join(preferences.enabled_categories)
        
        if preferences.keywords is not None:
            update_data['keywords'] = ','.join(preferences.keywords)
        
        if preferences.max_news_per_category is not None:
            update_data['max_news_per_category'] = preferences.max_news_per_category
        
        # Update preferences in database
        success = db_service.update_user_preferences(
            current_prefs['id'],
            **update_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error="UPDATE_FAILED",
                    message="Failed to update user preferences"
                ).dict()
            )
        
        # Return updated preferences
        return await get_user_preferences(token, request, token_validation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="UPDATE_ERROR",
                message="Unable to update user preferences"
            ).dict()
        )


@api_router.post(
    "/preferences/{token}/reset",
    response_model=PreferenceResetResponse,
    responses={
        200: {"description": "User preferences reset successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or missing token"},
        403: {"model": ErrorResponse, "description": "Token expired or exhausted"},
        404: {"model": ErrorResponse, "description": "User preferences not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Reset User Preferences",
    description="Reset user's email preferences to default values using a secure token."
)
async def reset_user_preferences(
    token: str = Path(..., description="Secure preference access token"),
    request: Request = None,
    token_validation: TokenValidationResult = Depends(require_valid_path_token)
) -> PreferenceResetResponse:
    """
    Reset user preferences to defaults with token validation.
    
    Args:
        token: Secure preference access token
        request: FastAPI request object
        token_validation: Token validation result from middleware
        
    Returns:
        PreferenceResetResponse: Reset operation result and new preferences
        
    Raises:
        HTTPException: If reset fails or validation errors
    """
    try:
        # Get current preferences
        current_prefs = db_service.get_user_preferences_by_email(token_validation.user_email)
        
        if not current_prefs:
            logger.error(f"User preferences not found for email: {token_validation.user_email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="PREFERENCES_NOT_FOUND",
                    message="User preferences not found"
                ).dict()
            )
        
        # Reset to default values
        default_preferences = {
            'enabled_sources': '',
            'enabled_categories': '',
            'keywords': '',
            'max_news_per_category': 10
        }
        
        # Update preferences in database
        success = db_service.update_user_preferences(
            current_prefs['id'],
            **default_preferences
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error="RESET_FAILED",
                    message="Failed to reset user preferences"
                ).dict()
            )
        
        # Get updated preferences
        updated_prefs = await get_user_preferences(token, request, token_validation)
        
        return PreferenceResetResponse(
            message="Preferences reset to defaults successfully",
            preferences=updated_prefs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="RESET_ERROR",
                message="Unable to reset user preferences"
            ).dict()
        )

@api_router.get(
    "/preferences-options/",
    response_model=AvailableOptionsResponse,
    responses={
        200: {"description": "Available options retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Available Options",
    description="Retrieve available news sources and categories for preference configuration."
)
async def get_available_options() -> AvailableOptionsResponse:
    """
    Get available sources and categories for preference configuration.
    This is a public endpoint that doesn't require authentication.
    """
    try:
        # Get available sources from database
        sources = db_service.get_all_sources()
        
        # For now, just return default categories
        category_list = ['Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports', 'Other']
        
        return {
            "sources": sources,
            "categories": category_list
        }
        
    except Exception as e:
        logger.error(f"Error retrieving available options: {e}")
        return {"error": str(e)}
        
    except Exception as e:
        logger.error(f"Error retrieving available options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="OPTIONS_ERROR",
                message="Unable to retrieve available options"
            ).dict()
        )

# Include the API router
app.include_router(api_router)
