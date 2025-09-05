from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import time
import sys
import os

from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from components.database import DatabaseService
from components.digest_service import DigestService

logger = logging.getLogger(__name__)

app = FastAPI()

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


@app.get("/articles")
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
    articles = db_service.get_articles(
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        categories=categories,
        source_id=source_id,
        limit=limit,
        offset=offset,
    )
    return articles

@app.get("/articles/{article_id}")
def get_article(article_id: int):
    """
    Get details for a single article by ID.
    """
    article = db_service.get_article_by_id(article_id)
    if not article:
        return {"error": "Article not found"}
    return article

@app.get("/categories")
def get_categories():
    """
    Get all unique categories from articles.
    """
    articles = db_service.get_articles()
    categories = sorted(set(a.get('category') for a in articles if a.get('category')))
    return categories

@app.get("/sources")
def get_sources():
    """
    Get all unique source IDs from articles.
    """
    articles = db_service.get_articles()
    sources = sorted(set(str(a.get('source_id')) for a in articles if a.get('source_id') is not None))
    return sources


@app.get("/digest/simulate")
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


@app.get("/digest/available-dates")
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


@app.get("/digest/metadata/{target_date}")
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
    
