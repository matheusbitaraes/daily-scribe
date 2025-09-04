from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from components.database import DatabaseService

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
