# Daily Scribe Performance Tuning Guide

This guide covers performance optimization techniques, monitoring, and tuning for Daily Scribe to ensure optimal performance across all components.

## 🎯 Performance Overview

### Performance Targets
- **API Response Time:** < 500ms for 95% of requests
- **Frontend Load Time:** < 3 seconds initial load
- **Database Query Time:** < 100ms for typical queries
- **Memory Usage:** < 512MB per container
- **CPU Usage:** < 70% during normal operations
- **Digest Generation:** < 5 minutes for typical user base

### Performance Components
- **Database Performance:** SQLite optimization and query tuning
- **API Performance:** FastAPI and Python optimization
- **Frontend Performance:** React and asset optimization
- **System Performance:** Docker, networking, and resource management
- **Background Processing:** Cron job and batch operation optimization

## 🗄️ Database Performance Optimization

### SQLite Configuration

**Optimize SQLite Settings:**
```python
# In DatabaseService.__init__
def __init__(self, db_path: str = None, timeout: int = 30):
    self.db_path = db_path or os.getenv('DB_PATH', 'data/digest_history.db')
    self.timeout = timeout
    
    # Performance optimizations
    self.connection = sqlite3.connect(
        self.db_path,
        timeout=self.timeout,
        check_same_thread=False
    )
    
    # Enable WAL mode for better concurrency
    self.connection.execute("PRAGMA journal_mode=WAL")
    
    # Optimize SQLite performance
    self.connection.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL
    self.connection.execute("PRAGMA cache_size=10000")    # 10MB cache
    self.connection.execute("PRAGMA temp_store=MEMORY")   # Use memory for temp tables
    self.connection.execute("PRAGMA mmap_size=268435456") # 256MB memory map
    self.connection.execute("PRAGMA optimize")           # Auto-optimize
```

**Advanced SQLite Tuning:**
```sql
-- Run these optimizations periodically
PRAGMA analysis_limit=1000;
PRAGMA optimize;

-- Vacuum to reclaim space (run weekly)
VACUUM;

-- Analyze tables for query optimizer
ANALYZE;

-- Check database statistics
.stats on
```

### Database Indexing

**Critical Indexes for Performance:**
```sql
-- Articles table indexes
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(published_date);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_articles_date_category ON articles(published_date, category);
CREATE INDEX IF NOT EXISTS idx_articles_source_date ON articles(source_id, published_date);

-- User preferences indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_preferences_email ON user_preferences(user_email);

-- Digest history indexes
CREATE INDEX IF NOT EXISTS idx_digest_history_date ON digest_history(digest_date);
CREATE INDEX IF NOT EXISTS idx_digest_history_user ON digest_history(user_email);
```

### Query Optimization

**Optimized Query Patterns:**
```python
class DatabaseService:
    def get_articles_optimized(self, limit=50, offset=0, category=None, 
                              source_id=None, date_from=None, date_to=None):
        """Optimized article retrieval with proper indexing"""
        
        # Build query with proper index usage
        base_query = """
        SELECT a.*, s.name as source_name
        FROM articles a
        JOIN sources s ON a.source_id = s.id
        """
        
        conditions = []
        params = []
        
        # Use indexed columns for filtering
        if category:
            conditions.append("a.category = ?")
            params.append(category)
            
        if source_id:
            conditions.append("a.source_id = ?")
            params.append(source_id)
            
        if date_from:
            conditions.append("a.published_date >= ?")
            params.append(date_from)
            
        if date_to:
            conditions.append("a.published_date <= ?")
            params.append(date_to)
        
        # Combine conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Order by indexed column
        base_query += " ORDER BY a.published_date DESC"
        
        # Limit and offset for pagination
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return self.execute_query(base_query, params)
    
    def get_digest_articles_optimized(self, user_email, target_date):
        """Optimized digest article retrieval"""
        
        # Get user preferences first
        prefs = self.get_user_preferences_by_email(user_email)
        
        # Build optimized query using indexes
        query = """
        SELECT a.*, s.name as source_name
        FROM articles a
        JOIN sources s ON a.source_id = s.id
        WHERE a.published_date >= date(?, '-1 day')
          AND a.published_date < date(?, '+1 day')
        """
        
        params = [target_date, target_date]
        
        # Filter by enabled sources (use IN for index efficiency)
        if prefs and prefs.get('enabled_sources'):
            placeholders = ','.join('?' * len(prefs['enabled_sources']))
            query += f" AND a.source_id IN ({placeholders})"
            params.extend(prefs['enabled_sources'])
        
        # Filter by enabled categories
        if prefs and prefs.get('enabled_categories'):
            placeholders = ','.join('?' * len(prefs['enabled_categories']))
            query += f" AND a.category IN ({placeholders})"
            params.extend(prefs['enabled_categories'])
        
        query += " ORDER BY a.published_date DESC"
        
        return self.execute_query(query, params)
```

### Connection Pooling

**SQLite Connection Management:**
```python
import threading
from contextlib import contextmanager

class DatabaseService:
    def __init__(self):
        self._local = threading.local()
        self.db_path = os.getenv('DB_PATH', 'data/digest_history.db')
        self.timeout = int(os.getenv('DB_TIMEOUT', 30))
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False
            )
            # Apply optimizations to each connection
            self._optimize_connection(self._local.connection)
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database operations"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
```

## ⚡ API Performance Optimization

### FastAPI Configuration

**Production FastAPI Settings:**
```python
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Optimized FastAPI configuration
app = FastAPI(
    title="Daily Scribe API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENV") != "production" else None,
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Optimize CORS for production
if os.getenv("ENV") == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
```

### Response Optimization

**Efficient Response Handling:**
```python
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
import orjson

class ORJSONResponse(JSONResponse):
    """Faster JSON response using orjson"""
    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS)

# Use in endpoints
@app.get("/articles", response_class=ORJSONResponse)
async def get_articles(limit: int = 50, offset: int = 0):
    articles = db_service.get_articles_optimized(limit=limit, offset=offset)
    return articles

# Streaming response for large data
@app.get("/articles/export")
async def export_articles():
    def generate_csv():
        yield "id,title,category,published_date\n"
        for article in db_service.get_all_articles_iterator():
            yield f"{article['id']},{article['title']},{article['category']},{article['published_date']}\n"
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles.csv"}
    )
```

### Caching Implementation

**Redis Caching for API Responses:**
```python
import redis
import json
from functools import wraps

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

def cache_response(expiration=300):
    """Decorator for caching API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage in endpoints
@app.get("/categories")
@cache_response(expiration=3600)  # Cache for 1 hour
async def get_categories():
    return db_service.get_categories()

@app.get("/sources")
@cache_response(expiration=1800)  # Cache for 30 minutes
async def get_sources():
    return db_service.get_sources()
```

### Async Database Operations

**Async Database Wrapper:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

class AsyncDatabaseService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def run_in_executor(self, func, *args):
        """Run database operation in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            functools.partial(func, *args)
        )
    
    async def get_articles_async(self, **kwargs):
        return await self.run_in_executor(
            self.db_service.get_articles_optimized, 
            **kwargs
        )
    
    async def get_digest_articles_async(self, user_email, target_date):
        return await self.run_in_executor(
            self.db_service.get_digest_articles_optimized,
            user_email,
            target_date
        )

# Use in endpoints
async_db = AsyncDatabaseService()

@app.get("/articles")
async def get_articles_endpoint(limit: int = 50, offset: int = 0):
    articles = await async_db.get_articles_async(limit=limit, offset=offset)
    return articles
```

## 🎨 Frontend Performance Optimization

### React Optimization

**Component Optimization:**
```javascript
import React, { memo, useMemo, useCallback, lazy, Suspense } from 'react';

// Memoized components
const ArticleCard = memo(({ article }) => {
  return (
    <div className="article-card">
      <h3>{article.title}</h3>
      <p>{article.summary}</p>
    </div>
  );
});

// Lazy loading for non-critical components
const DigestSimulator = lazy(() => import('./DigestSimulator'));
const PreferencePage = lazy(() => import('./PreferencePage'));

// Optimized main component
const ArticleList = () => {
  const [articles, setArticles] = useState([]);
  const [filters, setFilters] = useState({});
  
  // Memoized calculations
  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      if (filters.category && article.category !== filters.category) return false;
      if (filters.source && article.source_id !== filters.source) return false;
      return true;
    });
  }, [articles, filters]);
  
  // Memoized callbacks
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);
  
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        {filteredArticles.map(article => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </Suspense>
    </div>
  );
};
```

### Asset Optimization

**Webpack/Build Optimization:**
```javascript
// In package.json, optimize build
{
  "scripts": {
    "build": "react-scripts build",
    "build:analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"
  }
}

// Code splitting and lazy loading
const loadComponent = (componentName) => {
  return lazy(() => 
    import(`./components/${componentName}`).catch(err => {
      console.error(`Failed to load component ${componentName}:`, err);
      return { default: () => <div>Component failed to load</div> };
    })
  );
};

// Image optimization
const OptimizedImage = ({ src, alt, ...props }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  
  return (
    <div className="image-container">
      {isLoading && <div className="image-placeholder">Loading...</div>}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
        style={{ display: isLoading ? 'none' : 'block' }}
        {...props}
      />
      {hasError && <div className="image-error">Failed to load image</div>}
    </div>
  );
};
```

### API Call Optimization

**Efficient API Management:**
```javascript
import { useCallback, useRef } from 'react';

// Request deduplication
const requestCache = new Map();

const useDedupedFetch = () => {
  const abortControllerRef = useRef();
  
  const fetchData = useCallback(async (url, options = {}) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    // Check cache
    const cacheKey = `${url}${JSON.stringify(options)}`;
    if (requestCache.has(cacheKey)) {
      return requestCache.get(cacheKey);
    }
    
    // Make request
    const request = fetch(url, {
      ...options,
      signal: abortControllerRef.current.signal
    }).then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    }).finally(() => {
      // Remove from cache after 5 minutes
      setTimeout(() => requestCache.delete(cacheKey), 300000);
    });
    
    requestCache.set(cacheKey, request);
    return request;
  }, []);
  
  return fetchData;
};

// Debounced search
const useDebounceSearch = (searchFunction, delay = 300) => {
  const timeoutRef = useRef();
  
  const debouncedSearch = useCallback((query) => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      searchFunction(query);
    }, delay);
  }, [searchFunction, delay]);
  
  return debouncedSearch;
};
```

## 🐳 System Performance Optimization

### Docker Optimization

**Optimized Docker Configuration:**
```dockerfile
# Multi-stage build for smaller images
FROM node:18-alpine as frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim as production

# Install only necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Use non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Copy optimized Python requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --no-deps -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Copy application and frontend
COPY --chown=appuser:appuser src/ /app/src/
COPY --from=frontend-builder --chown=appuser:appuser /frontend/build /app/frontend/build

USER appuser
WORKDIR /app

# Optimize Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Docker Compose Performance:**
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: daily-scribe-app
    restart: unless-stopped
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    
    # Environment optimizations
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - WORKERS=2
      - MAX_REQUESTS=1000
      - MAX_REQUESTS_JITTER=100
    
    # Volume optimizations
    volumes:
      - ./data:/data:Z,rshared
      - daily_scribe_logs:/var/log/daily-scribe:Z
    
    # Health check optimization
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis for caching (optional)
  redis:
    image: redis:7-alpine
    container_name: daily-scribe-redis
    restart: unless-stopped
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.2'
```

### Nginx/Caddy Optimization

**Optimized Caddy Configuration:**
```caddyfile
{
    # Global optimizations
    admin {$CADDY_ADMIN:off}
    
    # Connection limits
    servers {
        max_header_size 16KB
        read_timeout 10s
        write_timeout 10s
        idle_timeout 120s
    }
}

{$DOMAIN:localhost} {
    # Enable compression
    encode {
        gzip 6
        zstd
        minimum_length 512
        match {
            header Content-Type text/*
            header Content-Type application/json*
            header Content-Type application/javascript*
            header Content-Type application/xml*
        }
    }
    
    # Static file optimizations
    @static {
        path /static/*
        path *.css *.js *.png *.jpg *.jpeg *.gif *.ico *.svg *.woff *.woff2
    }
    
    handle @static {
        header Cache-Control "public, max-age=31536000, immutable"
        header X-Content-Type-Options "nosniff"
        file_server
    }
    
    # API routes
    handle /api/* {
        header Cache-Control "no-cache, no-store, must-revalidate"
        reverse_proxy app:8000 {
            # Connection pooling
            transport http {
                max_conns_per_host 10
                dial_timeout 5s
                response_header_timeout 30s
            }
        }
    }
    
    # Health check (no logging)
    handle /healthz {
        reverse_proxy app:8000
        log {
            output discard
        }
    }
    
    # SPA routing
    handle {
        try_files {path} /index.html
        file_server {
            root /app/frontend/build
        }
    }
    
    # Security and performance headers
    header {
        # Performance
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        
        # Remove server info
        -Server
        -X-Powered-By
    }
}
```

## 📊 Performance Monitoring

### Application Metrics

**Performance Metrics Collection:**
```python
import time
import psutil
from collections import defaultdict
from fastapi import Request, Response

# Global metrics storage
metrics = {
    "requests_total": 0,
    "requests_by_endpoint": defaultdict(int),
    "response_times": defaultdict(list),
    "errors_total": 0,
    "database_query_count": 0,
    "database_query_time": 0.0,
}

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Get endpoint
    endpoint = f"{request.method} {request.url.path}"
    
    # Process request
    response = await call_next(request)
    
    # Calculate metrics
    duration = time.time() - start_time
    
    # Update metrics
    metrics["requests_total"] += 1
    metrics["requests_by_endpoint"][endpoint] += 1
    metrics["response_times"][endpoint].append(duration)
    
    # Keep only last 1000 response times
    if len(metrics["response_times"][endpoint]) > 1000:
        metrics["response_times"][endpoint] = metrics["response_times"][endpoint][-1000:]
    
    if response.status_code >= 400:
        metrics["errors_total"] += 1
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response

@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get application performance metrics"""
    
    # Calculate averages
    avg_response_times = {}
    for endpoint, times in metrics["response_times"].items():
        if times:
            avg_response_times[endpoint] = sum(times) / len(times)
    
    # System metrics
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
    
    return {
        "requests_total": metrics["requests_total"],
        "errors_total": metrics["errors_total"],
        "error_rate": metrics["errors_total"] / max(metrics["requests_total"], 1),
        "avg_response_times": avg_response_times,
        "system": system_metrics,
        "database": {
            "query_count": metrics["database_query_count"],
            "avg_query_time": metrics["database_query_time"] / max(metrics["database_query_count"], 1)
        }
    }
```

### Database Performance Monitoring

**Database Query Performance:**
```python
import time
import functools

def monitor_query_performance(func):
    """Decorator to monitor database query performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            metrics["database_query_count"] += 1
            metrics["database_query_time"] += duration
            
            # Log slow queries
            if duration > 0.1:  # Queries over 100ms
                logging.warning(f"Slow query detected: {func.__name__} took {duration:.3f}s")
    
    return wrapper

# Apply to database methods
class DatabaseService:
    @monitor_query_performance
    def get_articles(self, **kwargs):
        # Implementation
        pass
    
    @monitor_query_performance
    def execute_query(self, query, params=None):
        # Implementation
        pass
```

### Performance Testing Scripts

**Load Testing Script:**
```bash
#!/bin/bash
# load-test.sh

API_BASE_URL="https://yourdomain.com"
CONCURRENT_USERS=10
DURATION=60

echo "Starting load test..."
echo "URL: $API_BASE_URL"
echo "Concurrent users: $CONCURRENT_USERS"
echo "Duration: ${DURATION}s"

# Install dependencies
if ! command -v wrk &> /dev/null; then
    echo "Installing wrk..."
    sudo apt-get update && sudo apt-get install -y wrk
fi

# Test different endpoints
endpoints=(
    "/healthz"
    "/articles?limit=10"
    "/categories"
    "/sources"
    "/digest/available-dates"
)

for endpoint in "${endpoints[@]}"; do
    echo ""
    echo "Testing: $endpoint"
    wrk -t4 -c$CONCURRENT_USERS -d${DURATION}s \
        --timeout 30s \
        "${API_BASE_URL}${endpoint}"
done

echo ""
echo "Load test completed"
```

**Performance Monitoring Script:**
```bash
#!/bin/bash
# monitor-performance.sh

API_BASE_URL="http://localhost:8000"
LOG_FILE="/var/log/performance-monitor.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get performance metrics
    RESPONSE=$(curl -s "$API_BASE_URL/metrics/performance" || echo '{}')
    
    # Extract key metrics
    REQUESTS_TOTAL=$(echo "$RESPONSE" | jq -r '.requests_total // 0')
    ERROR_RATE=$(echo "$RESPONSE" | jq -r '.error_rate // 0')
    CPU_PERCENT=$(echo "$RESPONSE" | jq -r '.system.cpu_percent // 0')
    MEMORY_PERCENT=$(echo "$RESPONSE" | jq -r '.system.memory_percent // 0')
    
    # Log metrics
    echo "$TIMESTAMP,requests_total,$REQUESTS_TOTAL,error_rate,$ERROR_RATE,cpu_percent,$CPU_PERCENT,memory_percent,$MEMORY_PERCENT" >> "$LOG_FILE"
    
    # Alert on high resource usage
    if (( $(echo "$CPU_PERCENT > 80" | bc -l) )); then
        echo "HIGH CPU USAGE: $CPU_PERCENT%" | mail -s "Performance Alert" admin@yourdomain.com
    fi
    
    if (( $(echo "$MEMORY_PERCENT > 90" | bc -l) )); then
        echo "HIGH MEMORY USAGE: $MEMORY_PERCENT%" | mail -s "Performance Alert" admin@yourdomain.com
    fi
    
    sleep 60
done
```

## 🔧 Performance Troubleshooting

### Common Performance Issues

**Slow Database Queries:**
```bash
# Enable query logging
sqlite3 /app/data/digest_history.db ".timer on"

# Analyze query plans
sqlite3 /app/data/digest_history.db "EXPLAIN QUERY PLAN SELECT * FROM articles WHERE category = 'technology'"

# Check for missing indexes
sqlite3 /app/data/digest_history.db ".schema articles"
```

**High Memory Usage:**
```bash
# Monitor container memory
docker stats daily-scribe-app

# Check Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Profile memory usage
pip install memory-profiler
python -m memory_profiler your_script.py
```

**Slow API Responses:**
```python
# Add timing to specific functions
import time
import logging

def time_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        if duration > 0.5:  # Log slow operations
            logging.warning(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper

# Apply to suspected slow functions
@time_function
def generate_digest(user_email, target_date):
    # Implementation
    pass
```

---

**Performance Tuning Checklist:**
- [ ] Database indexes optimized
- [ ] Query patterns analyzed
- [ ] API responses cached appropriately
- [ ] Frontend assets optimized
- [ ] Docker containers resource-limited
- [ ] Monitoring in place
- [ ] Load testing completed

**Last Updated:** September 7, 2025  
**Next Review:** December 7, 2025
