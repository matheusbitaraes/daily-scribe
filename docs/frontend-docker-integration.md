# Frontend Docker Integration Guide

This guide explains how the Daily Scribe frontend is integrated into the Docker Compose setup for deployment at http://daily-scribe.duckdns.org/.

## Architecture Overview

The frontend is now fully integrated into the Docker Compose stack with the following components:

- **Frontend Service**: React app served via Nginx
- **Backend Service**: FastAPI application
- **Caddy Reverse Proxy**: Routes traffic between frontend and API
- **Database & Supporting Services**: Litestream, DDNS, etc.

## Service Configuration

### Frontend Service

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    target: production
  image: daily-scribe-frontend:latest
  container_name: daily-scribe-frontend
  restart: unless-stopped
  environment:
    - NODE_ENV=production
  volumes:
    - ./frontend/.env.production:/app/.env.production:ro
  networks:
    - daily_scribe_internal
  ports:
    - "3001:80"
  depends_on:
    - app
```

### Multi-Stage Docker Build

The frontend uses a multi-stage build process:

1. **Build Stage**: Node.js environment to build React app
2. **Production Stage**: Nginx Alpine to serve the built static files

### Nginx Configuration

The frontend includes a custom Nginx configuration that:

- Serves static files with proper caching headers
- Handles React Router (SPA) routing with `try_files`
- Proxies API calls to the backend service
- Includes security headers
- Provides health check endpoint

## Caddy Reverse Proxy Configuration

Caddy routes traffic as follows:

### API Routes
- `/api/*`, `/healthz`, `/docs`, `/openapi.json` → Backend (app:8000)
- Includes CORS headers for API endpoints

### Static Assets
- `*.css`, `*.js`, `*.png`, etc. → Frontend (frontend:80) with caching headers

### Frontend Routes
- All other routes → Frontend (frontend:80) for React Router handling

## Environment Configuration

### Production Environment Variables

The frontend uses `.env.production` with:
```bash
REACT_APP_API_URL=http://daily-scribe.duckdns.org/
```

This is built into the React app at build time and allows the frontend to communicate with the API.

## Deployment Instructions

### 1. Build and Start Services

```bash
# Build and start all services
docker-compose up -d

# Or rebuild frontend specifically
docker-compose build frontend
docker-compose up -d frontend
```

### 2. Verify Services

```bash
# Check all services are running
docker-compose ps

# Check frontend logs
docker-compose logs frontend

# Check Caddy logs
docker-compose logs caddy
```

### 3. Access the Application

- **Frontend**: http://daily-scribe.duckdns.org/
- **API Documentation**: http://daily-scribe.duckdns.org/docs
- **API Health Check**: http://daily-scribe.duckdns.org/healthz

## Development vs Production

### Development
```bash
# Start frontend in development mode
cd frontend
npm start
# Runs on http://localhost:3000
```

### Production
```bash
# Frontend runs in Docker container via Nginx
docker-compose up -d frontend
# Accessible via Caddy reverse proxy
```

## Monitoring and Health Checks

### Frontend Health Check
- Endpoint: `/health`
- Nginx responds with "healthy" status
- Docker health check uses `wget` to verify service

### Caddy Health Check
- Monitors both frontend and backend services
- Automatic failover and load balancing capabilities

## Security Features

### Headers Applied by Nginx
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

### Headers Applied by Caddy
- Strict-Transport-Security (HSTS)
- Content-Security-Policy
- Additional security headers

## File Structure

```
frontend/
├── Dockerfile              # Multi-stage build configuration
├── nginx.conf              # Custom Nginx configuration
├── .env.production         # Production environment variables
├── package.json            # Node.js dependencies
├── build/                  # Built React app (generated)
├── src/                    # React source code
└── public/                 # Static assets
```

## Troubleshooting

### Common Issues

1. **Frontend not accessible**
   - Check if frontend service is running: `docker-compose ps frontend`
   - Check Caddy logs: `docker-compose logs caddy`

2. **API calls failing**
   - Verify REACT_APP_API_URL in .env.production
   - Check network connectivity between services

3. **Build failures**
   - Ensure Node.js dependencies are available
   - Check Docker build logs: `docker-compose build frontend`

### Debugging Commands

```bash
# Access frontend container
docker-compose exec frontend sh

# Test internal network connectivity
docker-compose exec frontend wget -qO- http://app:8000/healthz

# Check Nginx configuration
docker-compose exec frontend nginx -t
```

## Performance Considerations

### Caching Strategy
- Static assets cached for 1 year
- Nginx gzip compression enabled
- Caddy automatic compression

### Build Optimization
- Multi-stage build reduces final image size
- npm ci for faster, reproducible builds
- Alpine Linux base images for smaller footprint

## Future Enhancements

1. **CDN Integration**: Consider adding CloudFlare or similar CDN
2. **Service Worker**: Add offline capabilities and caching
3. **Bundle Analysis**: Monitor and optimize bundle size
4. **Hot Reloading**: Development environment improvements
