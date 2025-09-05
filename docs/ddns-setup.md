# Dynamic DNS Setup Guide

This document provides comprehensive instructions for setting up Dynamic DNS (DDNS) for the Daily Scribe home server deployment. DDNS automatically updates your domain name to point to your changing home IP address.

## Overview

The Daily Scribe DDNS solution provides:
- **Automatic IP detection and updates**
- **Multiple DDNS provider support** (DuckDNS, Cloudflare, No-IP)
- **Redundancy** through multiple providers
- **Docker integration** for containerized deployment
- **Comprehensive monitoring** and health checks
- **Robust error handling** and retry mechanisms

## Quick Start

### 1. Choose a DDNS Provider

**Recommended: DuckDNS (Free and Simple)**
1. Visit [DuckDNS.org](https://www.duckdns.org/)
2. Sign in with your preferred account (Google, GitHub, etc.)
3. Create a subdomain (e.g., `mydailyscribe.duckdns.org`)
4. Note your token from the dashboard

**Alternative: Cloudflare (If you have a domain)**
1. Ensure your domain uses Cloudflare nameservers
2. Create an API token with Zone:Edit permissions
3. Note your Zone ID and DNS record ID

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# DuckDNS Configuration (recommended)
DDNS_PROVIDERS="duckdns:mydailyscribe:your-duckdns-token-here"

# Multiple providers for redundancy
# DDNS_PROVIDERS="duckdns:mydailyscribe:token,noip:myhost.ddns.net:username:password"

# Update frequency (seconds) - 5 minutes recommended
DDNS_UPDATE_INTERVAL=300

# Optional advanced settings
DDNS_MAX_RETRIES=3
DDNS_TIMEOUT=30
DDNS_LOG_LEVEL=INFO
```

### 3. Deploy with Docker Compose

```bash
# Start DDNS service along with other services
docker-compose --profile ddns up -d

# Or start just the DDNS service
docker-compose up -d ddns

# Check service status
docker-compose logs ddns
```

### 4. Verify Operation

```bash
# Check DDNS health
docker-compose exec ddns /usr/local/bin/ddns-update.sh health

# View logs
docker-compose logs -f ddns

# Test configuration
docker-compose exec ddns /usr/local/bin/ddns-update.sh test
```

## Supported DDNS Providers

### DuckDNS (Recommended)

**Why DuckDNS:**
- Completely free
- No account required (just social login)
- Simple setup
- Reliable service
- 5-minute TTL for fast updates

**Configuration:**
```bash
DDNS_PROVIDERS="duckdns:yourdomain:yourtoken"
```

**Setup Steps:**
1. Go to [duckdns.org](https://www.duckdns.org/)
2. Sign in with Google/GitHub/Reddit/Twitter
3. Add a subdomain (e.g., `mydailyscribe`)
4. Copy your token
5. Your domain will be `mydailyscribe.duckdns.org`

### Cloudflare DNS

**Why Cloudflare:**
- Fast global DNS network
- Advanced security features
- Free tier available
- Requires existing domain

**Configuration:**
```bash
DDNS_PROVIDERS="cloudflare:zone_id:record_id:api_token:yourdomain.com"
```

**Setup Steps:**
1. Ensure your domain uses Cloudflare nameservers
2. Get Zone ID from Cloudflare dashboard
3. Create API token with Zone:Edit permissions
4. Find DNS record ID using Cloudflare API
5. Configure A record for your subdomain

### No-IP

**Why No-IP:**
- Long-established service
- Multiple hostname types
- Free tier with confirmation requirement

**Configuration:**
```bash
DDNS_PROVIDERS="noip:yourhost.ddns.net:username:password"
```

**Setup Steps:**
1. Create account at [no-ip.com](https://www.noip.com/)
2. Create a hostname
3. Note username and password
4. Free accounts require monthly confirmation

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DDNS_PROVIDERS` | *required* | Comma-separated list of provider configs |
| `DDNS_UPDATE_INTERVAL` | 300 | Update check interval in seconds |
| `DDNS_MAX_RETRIES` | 3 | Maximum retry attempts for failed updates |
| `DDNS_TIMEOUT` | 30 | HTTP request timeout in seconds |
| `DDNS_LOG_LEVEL` | INFO | Log level: DEBUG, INFO, WARN, ERROR |
| `DDNS_FORCE_UPDATE` | false | Force update even if IP hasn't changed |
| `DDNS_IP_CHECK_URLS` | *auto* | Custom IP check service URLs |

### Provider Configuration Formats

```bash
# DuckDNS
"duckdns:domain:token"

# Cloudflare
"cloudflare:zone_id:record_id:api_token:domain.example.com"

# No-IP
"noip:hostname:username:password"

# Multiple providers (recommended for redundancy)
"duckdns:mydomain:token,noip:myhost.ddns.net:user:pass"
```

### Advanced Configuration File

For non-Docker deployment, create `/etc/daily-scribe/ddns.conf`:

```bash
# Update interval (seconds)
UPDATE_INTERVAL=300

# Retry settings
MAX_RETRIES=3
TIMEOUT=30

# Logging
LOG_LEVEL=INFO

# Providers
DDNS_PROVIDERS="duckdns:mydomain:token"

# IP check services
IP_CHECK_URLS=(
    "https://ipv4.icanhazip.com"
    "https://api.ipify.org"
    "https://checkip.amazonaws.com"
    "https://ipinfo.io/ip"
)

# Notifications (optional)
ENABLE_EMAIL_NOTIFICATIONS=false
NOTIFICATION_EMAIL="admin@example.com"
```

## Deployment Options

### Docker Compose (Recommended)

The DDNS service is integrated into the main docker-compose.yml:

```yaml
services:
  ddns:
    build:
      context: .
      dockerfile: docker/Dockerfile.ddns
    environment:
      - DDNS_PROVIDERS=${DDNS_PROVIDERS}
      - UPDATE_INTERVAL=${DDNS_UPDATE_INTERVAL:-300}
    profiles:
      - ddns
      - production
```

**Commands:**
```bash
# Start with production profile
docker-compose --profile production up -d

# Start specific service
docker-compose up -d ddns

# View logs
docker-compose logs -f ddns

# Restart service
docker-compose restart ddns
```

### Standalone Docker

```bash
# Build the image
docker build -f docker/Dockerfile.ddns -t daily-scribe-ddns .

# Run the container
docker run -d \
  --name ddns-update \
  --restart unless-stopped \
  -e DDNS_PROVIDERS="duckdns:mydomain:token" \
  -e UPDATE_INTERVAL=300 \
  -v ddns_logs:/var/log/daily-scribe \
  daily-scribe-ddns
```

### Systemd Service

For bare metal deployment:

```bash
# Copy service file
sudo cp systemd/ddns-update.service /etc/systemd/system/

# Create configuration
sudo mkdir -p /etc/daily-scribe
sudo cp ddns.conf.example /etc/daily-scribe/ddns.conf
sudo nano /etc/daily-scribe/ddns.conf

# Enable and start service
sudo systemctl enable ddns-update.service
sudo systemctl start ddns-update.service

# Check status
sudo systemctl status ddns-update.service
```

### Cron Job

For simple scheduled updates:

```bash
# Add to crontab
# Update every 5 minutes
*/5 * * * * /path/to/ddns-update.sh update

# Or every 15 minutes for less frequent updates
*/15 * * * * /path/to/ddns-update.sh update
```

## Monitoring and Troubleshooting

### Health Checks

```bash
# Docker Compose
docker-compose exec ddns /usr/local/bin/ddns-update.sh health

# Direct script
./scripts/ddns-update.sh health

# Test configuration
./scripts/ddns-update.sh test
```

### Log Analysis

**Docker logs:**
```bash
# Real-time logs
docker-compose logs -f ddns

# Recent logs
docker-compose logs --tail 100 ddns

# Logs since timestamp
docker-compose logs --since 2024-01-01T00:00:00 ddns
```

**Log file locations:**
- Docker: `/var/log/daily-scribe/ddns.log` (in container)
- Systemd: `/var/log/daily-scribe/ddns.log`
- Manual: Configurable via `LOG_FILE` environment variable

### Common Issues and Solutions

**1. "Failed to retrieve public IP address"**
```
Cause: Network connectivity or IP check services down
Solution: 
- Check internet connectivity
- Verify firewall allows outbound HTTPS
- Wait for IP check services to recover
```

**2. "DDNS update failed"**
```
Cause: Invalid credentials or provider issues
Solution:
- Verify provider credentials
- Check token/password expiration
- Confirm domain exists
- Review provider status page
```

**3. "DNS propagation issues"**
```
Cause: DNS caching or propagation delays
Solution:
- Wait 5-15 minutes for propagation
- Check with multiple DNS servers
- Verify TTL settings
- Use DNS propagation checker tools
```

**4. "Container keeps restarting"**
```
Cause: Configuration errors or missing credentials
Solution:
- Check environment variables
- Review container logs
- Validate DDNS_PROVIDERS format
- Ensure network connectivity
```

### Monitoring Commands

```bash
# Check current IP and DNS resolution
./scripts/ddns-update.sh health

# Test IP detection only
curl https://ipv4.icanhazip.com

# Verify DNS resolution
dig +short yourdomain.duckdns.org

# Check service status
docker-compose ps ddns

# Monitor logs in real-time
docker-compose logs -f ddns
```

## Security Considerations

### Credential Protection

1. **Environment Variables**: Store sensitive tokens in `.env` file
2. **File Permissions**: Restrict config file access (`chmod 600`)
3. **Container Security**: Non-root user, minimal privileges
4. **Token Rotation**: Regularly rotate API tokens and passwords

### Network Security

1. **HTTPS Only**: All API calls use encrypted connections
2. **Firewall**: Only allow necessary outbound connections
3. **DNS Validation**: Verify DNS responses to prevent hijacking
4. **Monitoring**: Log all update attempts and failures

### Best Practices

1. **Multiple Providers**: Use redundant DDNS providers
2. **Regular Testing**: Automated health checks and monitoring
3. **Backup Access**: Maintain alternative access methods
4. **Documentation**: Keep credentials and procedures documented

## Performance Optimization

### Update Frequency

- **Recommended**: 5-15 minutes (300-900 seconds)
- **Aggressive**: 1-3 minutes (for critical services)
- **Conservative**: 15-30 minutes (for stable connections)

### Resource Usage

- **CPU**: Minimal (periodic HTTP requests only)
- **Memory**: ~10-20MB container footprint
- **Network**: ~1KB per update cycle
- **Storage**: ~1MB logs per month

### Scaling Considerations

- **Multiple Domains**: Configure multiple providers
- **Load Balancing**: Use round-robin DNS if supported
- **Geo-Distribution**: Consider multiple DDNS regions

## Integration with Daily Scribe

### Caddy Configuration

Update your Caddyfile to use the DDNS domain:

```caddyfile
yourdomain.duckdns.org {
    reverse_proxy app:8000
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }
    
    # Access logging
    log {
        output file /var/log/caddy/access.log
        format json
    }
}
```

### Firewall Configuration

Ensure your router forwards ports to the server:

```bash
# Required ports for Daily Scribe
Port 80  -> Server:80  (HTTP, redirects to HTTPS)
Port 443 -> Server:443 (HTTPS)

# Optional: SSH access
Port 2222 -> Server:22 (SSH, custom port recommended)
```

### Monitoring Integration

Add DDNS monitoring to your health checks:

```bash
# External monitoring (UptimeRobot, etc.)
Monitor: https://yourdomain.duckdns.org/healthz

# Internal monitoring
Check: DDNS health every 30 minutes
Alert: Failed updates after 3 attempts
```

## Troubleshooting Guide

### DNS Propagation Checker

Test your domain resolution from multiple locations:

```bash
# Command line tools
dig +short @8.8.8.8 yourdomain.duckdns.org
nslookup yourdomain.duckdns.org 1.1.1.1

# Online tools
- whatsmydns.net
- dnschecker.org
- dns-lookup.com
```

### Connection Testing

```bash
# Test external access
curl -I https://yourdomain.duckdns.org/healthz

# Test from different networks
# Use mobile hotspot or VPN to verify external access
```

### Log Analysis Examples

**Successful update:**
```
[2024-01-15 10:30:15] [INFO] Starting DDNS update check
[2024-01-15 10:30:16] [INFO] IP address changed: 192.168.1.100 -> 203.0.113.42
[2024-01-15 10:30:17] [INFO] DuckDNS update successful for mydomain.duckdns.org
[2024-01-15 10:30:17] [INFO] DDNS update completed: 1/1 providers successful
```

**Failed update with retry:**
```
[2024-01-15 10:35:15] [INFO] Starting DDNS update check
[2024-01-15 10:35:16] [ERROR] DuckDNS update failed for mydomain.duckdns.org: KO
[2024-01-15 10:35:16] [WARN] DDNS update failed, retrying in 30s (attempt 1/3)
[2024-01-15 10:35:46] [INFO] DuckDNS update successful for mydomain.duckdns.org
[2024-01-15 10:35:46] [INFO] DDNS update successful on attempt 2
```

## Advanced Configuration

### Custom IP Detection

If default IP check services are blocked or unreliable:

```bash
# Custom IP check URLs
DDNS_IP_CHECK_URLS="https://api.myisp.com/ip,https://custom-ip-service.com"

# Local router API (if supported)
DDNS_IP_CHECK_URLS="http://192.168.1.1/api/status"
```

### Webhook Notifications

For integration with monitoring systems:

```bash
# Configuration
ENABLE_WEBHOOK_NOTIFICATIONS=true
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Webhook payload example
{
  "service": "ddns-update",
  "status": "success",
  "message": "IP updated to 203.0.113.42",
  "domain": "mydomain.duckdns.org",
  "timestamp": "2024-01-15T10:30:17Z"
}
```

### Multiple Domain Management

For managing multiple domains or subdomains:

```bash
# Multiple DuckDNS domains
DDNS_PROVIDERS="duckdns:main:token1,duckdns:backup:token1,duckdns:api:token1"

# Mixed providers
DDNS_PROVIDERS="duckdns:main:token,cloudflare:zone:record:token:backup.example.com"
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
cp /etc/daily-scribe/ddns.conf /backup/ddns.conf.$(date +%Y%m%d)

# Backup environment variables
grep DDNS_ .env > /backup/ddns-env.$(date +%Y%m%d)
```

### Disaster Recovery

In case of complete failure:

1. **Restore Configuration**: Deploy new server with backed-up config
2. **Update DNS**: Manually update DNS records if needed
3. **Verify Access**: Test external connectivity
4. **Resume Monitoring**: Restart DDNS service

### Alternative Access Methods

Maintain backup access methods:

1. **Static IP Service**: Consider business internet with static IP
2. **VPN Access**: Set up VPN for management access
3. **Cloud Backup**: Deploy to cloud provider as fallback
4. **Mobile Hotspot**: Use mobile connection for emergency access

This comprehensive guide should help you set up and maintain a robust DDNS solution for your Daily Scribe home server deployment.
