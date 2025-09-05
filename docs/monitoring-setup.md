# Daily Scribe Monitoring and Alerting Setup

This document provides a comprehensive guide for setting up monitoring and alerting for your Daily Scribe deployment.

## Overview

The monitoring solution includes:
- **Internal Health Checks**: Application and service health monitoring
- **External Uptime Monitoring**: Third-party service monitoring
- **Log Aggregation**: Centralized logging with rotation
- **Metrics Collection**: System and application metrics
- **Alerting**: Email and webhook notifications
- **Dashboard**: Visual system status overview

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  External       │    │  Internal       │    │  Log            │
│  Monitoring     │    │  Health Checks  │    │  Aggregation    │
│  (UptimeRobot)  │    │  (Healthchecks) │    │  (Promtail/     │
│                 │    │                 │    │   Loki)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Notification Hub                         │
│                     (Email + Webhooks)                         │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Grafana      │    │     Alert       │    │   Dashboard     │
│   Dashboard     │    │   Manager       │    │   (Optional)    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

1. **Enable Internal Monitoring**:
   ```bash
   ./scripts/setup-monitoring.sh --internal
   ```

2. **Configure External Monitoring**:
   ```bash
   ./scripts/setup-monitoring.sh --external
   ```

3. **Start All Monitoring Services**:
   ```bash
   docker-compose up -d monitoring
   ```

4. **Verify Setup**:
   ```bash
   ./scripts/test-monitoring.sh
   ```

## Internal Health Checks

### Application Health Endpoint

Daily Scribe includes a comprehensive health check endpoint at `/healthz` that monitors:
- Application status
- Database connectivity
- Disk space usage
- Memory usage
- Service dependencies

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-05T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "last_check": "2025-09-05T10:30:00Z"
    },
    "disk_space": {
      "status": "healthy",
      "usage_percent": 45,
      "available_gb": 12.5
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 62,
      "available_mb": 1024
    }
  }
}
```

### Docker Health Checks

All services include Docker health checks:

```yaml
# In docker-compose.yml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Service Monitoring

Monitor individual services:
- **Application Server**: HTTP endpoint monitoring
- **Caddy Proxy**: HTTP/HTTPS proxy health
- **Cron Service**: Scheduled task execution
- **Litestream**: Database backup status
- **DDNS**: Dynamic DNS update status

## External Uptime Monitoring

### UptimeRobot Setup

1. **Create Account**: Sign up at [uptimerobot.com](https://uptimerobot.com)

2. **Add Monitor**:
   - Type: HTTP(S)
   - URL: `https://yourdomain.duckdns.org/healthz`
   - Interval: 5 minutes
   - Timeout: 30 seconds

3. **Configure Alerts**:
   - Email notifications
   - Webhook notifications (optional)
   - SMS notifications (premium)

4. **Environment Configuration**:
   ```bash
   # In .env file
   UPTIMEROBOT_API_KEY=ur123456789-abcdef123456789
   UPTIMEROBOT_MONITOR_URL=https://yourdomain.duckdns.org/healthz
   ```

### Alternative External Monitors

#### Healthchecks.io
```bash
# Configure in .env
HEALTHCHECKS_UUID=12345678-1234-5678-9012-123456789abc
HEALTHCHECKS_URL=https://hc-ping.com/12345678-1234-5678-9012-123456789abc
```

#### StatusCake
```bash
# Configure in .env
STATUSCAKE_API_KEY=your-api-key
STATUSCAKE_TEST_ID=123456
```

## Log Aggregation and Rotation

### Docker Logging Configuration

Configure structured logging for all services:

```yaml
# docker-compose.yml logging configuration
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,environment"
    labels:
      - "service=daily-scribe-app"
      - "environment=production"
```

### Log Rotation

Automatic log rotation is configured for:
- Application logs: 10MB max, 3 files retained
- System logs: 50MB max, 5 files retained
- Backup logs: 20MB max, 7 files retained

### Centralized Logging (Optional)

For advanced setups, use Loki + Promtail:

```yaml
# docker-compose.monitoring.yml
services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    
  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml
```

## Metrics Collection

### Basic System Metrics

Monitor key system metrics:
- CPU usage
- Memory usage
- Disk space
- Network I/O
- Container status

### Application Metrics

Track application-specific metrics:
- Request count and latency
- Error rates
- Database query performance
- Feed processing statistics
- Article processing metrics

### Metrics Endpoint

Access metrics at `/metrics` (Prometheus format):
```
# HELP daily_scribe_articles_processed_total Total articles processed
# TYPE daily_scribe_articles_processed_total counter
daily_scribe_articles_processed_total 1234

# HELP daily_scribe_feeds_fetched_total Total feeds fetched
# TYPE daily_scribe_feeds_fetched_total counter
daily_scribe_feeds_fetched_total 56

# HELP daily_scribe_digest_generation_duration_seconds Time to generate digest
# TYPE daily_scribe_digest_generation_duration_seconds histogram
daily_scribe_digest_generation_duration_seconds_bucket{le="1"} 12
daily_scribe_digest_generation_duration_seconds_bucket{le="5"} 45
daily_scribe_digest_generation_duration_seconds_bucket{le="10"} 50
```

## Alerting Configuration

### Email Alerts

Configure SMTP for email notifications:

```bash
# In .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=daily-scribe@yourdomain.com
SMTP_TO=admin@yourdomain.com
```

### Alert Rules

Pre-configured alert conditions:

1. **Service Down**: Service unavailable for > 2 minutes
2. **High Error Rate**: > 10% error rate for > 5 minutes
3. **Disk Space Low**: < 10% free space
4. **Memory High**: > 90% memory usage for > 10 minutes
5. **Database Issues**: Database connectivity problems
6. **Backup Failures**: Litestream backup failures
7. **DDNS Failures**: Dynamic DNS update failures

### Webhook Notifications

Send alerts to external services:

```bash
# Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Discord webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK

# Custom webhook
CUSTOM_WEBHOOK_URL=https://your-service.com/webhook/daily-scribe
```

## Dashboard Setup

### Grafana Dashboard (Optional)

For comprehensive visualization:

```yaml
# docker-compose.monitoring.yml
services:
  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
```

### Simple HTML Dashboard

A lightweight status page:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Daily Scribe Status</title>
    <meta http-equiv="refresh" content="30">
</head>
<body>
    <h1>Daily Scribe System Status</h1>
    <div id="status-container">
        <!-- Auto-populated via JavaScript -->
    </div>
    <script src="/static/status.js"></script>
</body>
</html>
```

## Alert Fatigue Prevention

### Smart Alerting Rules

1. **Escalation Policy**: 
   - Warning: Email after 5 minutes
   - Critical: Email + SMS after 2 minutes
   - Emergency: Immediate all channels

2. **Grouping**: Related alerts grouped together

3. **Suppression**: Maintenance mode silencing

4. **Dependencies**: Don't alert downstream if upstream fails

### Alert Tuning

Adjust thresholds based on your environment:
- Start conservative, tune based on patterns
- Use percentile-based thresholds
- Consider time-of-day variations
- Account for expected maintenance windows

## Monitoring Best Practices

### What to Monitor

**Golden Signals**:
1. **Latency**: Response time for requests
2. **Traffic**: Request rate
3. **Errors**: Error rate
4. **Saturation**: Resource utilization

**Additional Metrics**:
- Business metrics (articles processed, digests sent)
- Infrastructure metrics (CPU, memory, disk)
- External dependencies (feed sources, email delivery)

### Alert Design

1. **Actionable**: Every alert should require human action
2. **Contextual**: Include relevant debugging information
3. **Prioritized**: Clear severity levels
4. **Documented**: Include runbook links

### Maintenance

1. **Regular Review**: Weekly alert review and tuning
2. **Runbook Updates**: Keep troubleshooting guides current
3. **Test Procedures**: Regular alert testing
4. **Capacity Planning**: Monitor trends for growth

## Troubleshooting

### Common Issues

1. **High False Positive Rate**:
   - Tune alert thresholds
   - Add hysteresis to prevent flapping
   - Consider time-based rules

2. **Missing Alerts**:
   - Verify notification delivery
   - Check alert rule syntax
   - Test with manual triggers

3. **Dashboard Not Loading**:
   - Check service connectivity
   - Verify API endpoints
   - Review browser console errors

### Debug Commands

```bash
# Check service health
./scripts/test-monitoring.sh --verbose

# View recent alerts
docker-compose logs alertmanager

# Test notification delivery
./scripts/test-notifications.sh

# Monitor resource usage
docker stats daily-scribe_app_1

# Check alert rules
./scripts/validate-alerts.sh
```

## Security Considerations

1. **Monitoring Access**: Secure dashboard access
2. **Alert Content**: Avoid sensitive data in alerts
3. **Webhook Security**: Use HTTPS and validate sources
4. **Credential Management**: Secure storage of API keys

## Next Steps

After completing basic monitoring setup:

1. **Tune Alerts**: Adjust based on actual usage patterns
2. **Expand Metrics**: Add business-specific metrics
3. **Custom Dashboards**: Create role-specific views
4. **Integration**: Connect with existing tools
5. **Documentation**: Update runbooks based on incidents

For detailed implementation steps, see:
- `scripts/setup-monitoring.sh` - Automated setup script
- `scripts/test-monitoring.sh` - Validation and testing
- `monitoring/` directory - Configuration files
- `docs/monitoring-runbook.md` - Operational procedures
