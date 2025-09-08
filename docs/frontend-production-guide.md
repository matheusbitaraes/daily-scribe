# Frontend Production Deployment Guide

This guide covers the production deployment of the Daily Scribe React frontend using the automated deployment script and Docker Compose integration.

## Quick Deployment

### Using the Automated Deployment Script

**Yes, the deployment script will work to get the frontend running:**

```bash
./scripts/deploy-to-server.sh --production
```

**What this command does:**

1. **Copies frontend files** - The rsync command includes the entire `frontend/` directory
2. **Builds frontend Docker image** - Runs `docker-compose build frontend`
3. **Starts frontend service** - Includes frontend in `docker-compose up -d`
4. **Configures reverse proxy** - Caddy routes traffic to both frontend and backend

## Deployment Process Overview

### What Gets Deployed

The deployment script will:

✅ **Frontend files copied to server:**
- `frontend/` directory with all React source code
- `frontend/Dockerfile` (multi-stage build configuration)
- `frontend/nginx.conf` (custom Nginx configuration)
- `frontend/.env.production` (production environment variables)
- `frontend/package.json` and dependencies

✅ **Docker services started:**
- Frontend service (React app + Nginx)
- Backend service (FastAPI)
- Caddy reverse proxy
- Supporting services (Litestream, DDNS, etc.)

✅ **Network configuration:**
- Caddy routes traffic between frontend and API
- Frontend accessible at `http://daily-scribe.duckdns.org/`
- API accessible at `http://daily-scribe.duckdns.org/api/`

### Prerequisites

Before running the deployment script:

1. **Environment Variables** - Ensure these are set on the server:
   ```bash
   export DOMAIN=daily-scribe.duckdns.org
   export GEMINI_API_KEY=your_key_here
   # ... other required environment variables
   ```

2. **Frontend Environment** - Verify `frontend/.env.production` contains:
   ```bash
   REACT_APP_API_URL=http://daily-scribe.duckdns.org/
   ```

3. **Node.js Dependencies** - The Docker build will handle npm installation

## Deployment Steps

### 1. Run the Deployment Script

```bash
# From your local machine
./scripts/deploy-to-server.sh --production
```

### 2. Monitor the Deployment

The script will show progress for:
- File synchronization to server
- Docker image builds (including frontend)
- Service startup
- Health checks

### 3. Verify Deployment

After deployment completes:

```bash
# Check all services are running
docker-compose ps

# Specific frontend checks
docker-compose ps frontend
docker-compose logs frontend

# Test frontend accessibility (note: direct port is 3001, but use domain)
curl -I http://daily-scribe.duckdns.org/
curl -I http://daily-scribe.duckdns.org/health

# Internal port check (if needed for debugging)
curl -I http://192.168.15.55:3001/health
```

## Access Points After Deployment

Once deployed, you can access:

- **Frontend Application**: http://daily-scribe.duckdns.org/
- **API Documentation**: http://daily-scribe.duckdns.org/docs
- **API Health Check**: http://daily-scribe.duckdns.org/healthz
- **Frontend Health Check**: http://daily-scribe.duckdns.org/health

## Architecture in Production

### Service Stack

```
Internet → Caddy (Port 80/443) → Frontend (Port 80) + Backend (Port 8000)
                                      ↓
                                   Database & Supporting Services
```

### Traffic Routing

1. **Frontend Routes** (`/`, `/preferences`, etc.) → Frontend service
2. **API Routes** (`/api/*`, `/docs`, `/healthz`) → Backend service
3. **Static Assets** (`.js`, `.css`, etc.) → Frontend service with caching

## Troubleshooting Production Issues

### Frontend Not Loading

```bash
# Check frontend service status
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend

# Check Caddy routing
docker-compose logs caddy

# Test internal connectivity
docker-compose exec caddy wget -qO- http://frontend:80/health
```

### API Calls Failing

```bash
# Verify environment variables
docker-compose exec frontend env | grep REACT_APP

# Test backend connectivity
docker-compose exec frontend wget -qO- http://app:8000/healthz

# Check network connectivity
docker network ls
docker network inspect daily-scribe_daily_scribe_internal
```

### Build Failures

```bash
# Rebuild frontend specifically
docker-compose build --no-cache frontend

# Check build logs
docker-compose build frontend 2>&1 | tee frontend-build.log

# Verify Node.js dependencies
docker-compose run --rm frontend npm list
```

## Production Monitoring

### Health Checks

The deployment includes automatic health checks:

- **Frontend**: HTTP GET to `/health` every 30 seconds
- **Caddy**: Service version check every 30 seconds
- **Backend**: HTTP GET to `/healthz` every 30 seconds

### Log Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Frontend-specific logs
docker-compose logs -f frontend

# Real-time monitoring
watch docker-compose ps
```

### Performance Monitoring

```bash
# Container resource usage
docker stats

# Service-specific stats
docker stats daily-scribe-frontend

# Disk usage
docker system df
```

## Production Maintenance

### Updates and Redeployment

To update the frontend:

```bash
# Full redeployment
./scripts/deploy-to-server.sh --production

# Frontend-only update
rsync -av frontend/ user@server:/path/to/daily-scribe/frontend/
ssh user@server "cd /path/to/daily-scribe && docker-compose build frontend && docker-compose up -d frontend"
```

### Backup and Recovery

The deployment script handles:
- Database backups via Litestream
- Configuration file preservation
- Docker image management

### Scaling Considerations

For high-traffic scenarios:
- Add load balancing in Caddy
- Consider CDN integration
- Monitor container resource usage
- Implement horizontal scaling

## Security in Production

### HTTPS Configuration

Caddy automatically handles:
- Let's Encrypt certificate generation
- HTTP to HTTPS redirects
- Security headers (HSTS, CSP, etc.)

### Network Security

- Services isolated in Docker networks
- Frontend and backend communication via internal network
- Only Caddy exposed to external traffic

### Content Security

- Nginx security headers in frontend
- Content-Type protection
- XSS protection headers

## Performance Optimization

### Caching Strategy

- Static assets cached for 1 year
- Gzip compression enabled
- Browser caching headers set

### Build Optimization

- Multi-stage Docker builds reduce image size
- npm ci for reproducible builds
- Alpine Linux base images

### Network Optimization

- Caddy automatic compression
- HTTP/2 support
- Connection keep-alive