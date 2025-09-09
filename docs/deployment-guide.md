# Daily Scribe Deployment Guide

## Overview
This guide covers deploying Daily Scribe with the new AWS SES email service and custom domain configuration.

## Prerequisites

### 1. Domain and DNS Setup
- ✅ Domain registered: `dailyscribe.news`
- ✅ AWS SES domain verification completed
- ✅ DKIM records configured in DNS
- ⚠️ SPF record needs to be added (see DNS Configuration section)

### 2. AWS SES Configuration
- ✅ AWS SES account set up
- ✅ Domain verified in AWS SES
- ✅ SMTP credentials generated
- ✅ Sending rate limits configured (14 emails/minute)

### 3. Environment Variables
Required environment variables for production deployment:

```bash
# Email Service Configuration
EMAIL_PROVIDER=aws_ses
EMAIL_SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your_aws_ses_smtp_username
EMAIL_SMTP_PASSWORD=your_aws_ses_smtp_password
EMAIL_AWS_REGION=us-east-1

# Email Addresses
EMAIL_FROM_EDITOR=editor@dailyscribe.news
EMAIL_FROM_ADMIN=admin@dailyscribe.news
EMAIL_FROM_SUPPORT=support@dailyscribe.news

# Email Settings
EMAIL_RATE_LIMIT=14
EMAIL_RETRY_ATTEMPTS=3
EMAIL_TIMEOUT=30

# API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Database
DB_PATH=/data/digest_history.db
DB_TIMEOUT=30
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Production Deployment
1. **Prepare Environment File**:
   ```bash
   cp .env.production .env
   # Edit .env with your actual credentials
   ```

2. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Verify Health Status**:
   ```bash
   curl http://localhost:8000/healthz
   ```

#### Development Deployment
1. **Use Development Environment**:
   ```bash
   cp .env.example .env
   # Configure your development credentials
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

### Method 2: Manual Deployment

#### System Requirements
- Python 3.11+
- SQLite 3
- 2GB RAM minimum
- 10GB disk space

#### Installation Steps
1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/daily-scribe.git
   cd daily-scribe
   ```

2. **Setup Python Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize Database**:
   ```bash
   python -c "from src.db.database import DatabaseService; DatabaseService().initialize_database()"
   ```

5. **Start Application**:
   ```bash
   uvicorn src.api:app --host 0.0.0.0 --port 8000
   ```

## DNS Configuration

### Required DNS Records
Add these records to your domain DNS (GoDaddy):

```dns
# SPF Record (MISSING - NEEDS TO BE ADDED)
Type: TXT
Name: dailyscribe.news
Value: v=spf1 include:amazonses.com ~all
TTL: 1800

# Domain Verification (ALREADY CONFIGURED)
Type: TXT
Name: _amazonses.dailyscribe.news
Value: 9uNIc/rdVzhyz2L7566syOPDYso66+/07kzcfwcPioA=
TTL: 1800

# DKIM Records (ALREADY CONFIGURED)
Type: CNAME
Name: tnrpt4g4zdbklssfl6g2rhjs5k5li677._domainkey.dailyscribe.news
Value: tnrpt4g4zdbklssfl6g2rhjs5k5li677.dkim.amazonses.com
TTL: 1800

# Additional DKIM records...
```

## Health Monitoring

### Health Check Endpoints
- **API Health**: `GET /healthz`
- **Metrics**: `GET /metrics`
- **Email Health**: `python scripts/email-health-check.py`

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-09-09T17:04:50.253860Z",
  "service": "daily-scribe-api",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 2.34
    },
    "email_service": {
      "status": "healthy",
      "provider": "aws_ses",
      "response_time_ms": 145.67
    }
  },
  "response_time_ms": 152.45
}
```

## Backup and Disaster Recovery

### Email Service Backup Strategy
Daily Scribe includes automatic fallback to Gmail if AWS SES fails:

1. **Primary**: AWS SES (`editor@dailyscribe.news`)
2. **Fallback**: Gmail (configured in `legacy` section)

### Database Backup
- **Litestream**: Continuous replication to Google Cloud Storage
- **Manual Backup**: Use `scripts/backup-manager.sh`

## Security Considerations

### Environment Variables
- ✅ Never commit credentials to version control
- ✅ Use Docker secrets in production
- ✅ Rotate credentials regularly
- ✅ Monitor AWS SES usage and costs

### Email Security
- ✅ DKIM signing enabled
- ✅ SPF record configured
- ✅ DMARC policy set to quarantine
- ✅ Reply-To headers configured for proper email routing

## Troubleshooting

### Common Issues

#### Email Delivery Failures
1. **Check AWS SES Status**:
   ```bash
   aws ses get-identity-verification-attributes --identities dailyscribe.news
   ```

2. **Verify DNS Records**:
   ```bash
   dig TXT dailyscribe.news
   dig CNAME tnrpt4g4zdbklssfl6g2rhjs5k5li677._domainkey.dailyscribe.news
   ```

3. **Test Email Health**:
   ```bash
   python scripts/email-health-check.py
   ```

#### Database Connection Issues
1. **Check Database Path**:
   ```bash
   ls -la /data/digest_history.db
   ```

2. **Verify Permissions**:
   ```bash
   docker exec daily-scribe-app ls -la /data/
   ```

### Monitoring Commands
```bash
# View application logs
docker logs daily-scribe-app -f

# Check email service status
docker exec daily-scribe-app python scripts/email-health-check.py

# Monitor database size
docker exec daily-scribe-app ls -lh /data/digest_history.db

# Check health endpoint
curl -s http://localhost:8000/healthz | jq
```

## Performance Tuning

### Email Rate Limiting
- Current limit: 14 emails/minute (AWS SES default)
- Retry attempts: 3 with exponential backoff
- Connection timeout: 30 seconds

### Database Optimization
- SQLite WAL mode enabled
- Connection pooling implemented
- Automatic vacuum scheduling

## Production Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] DNS records verified
- [ ] AWS SES domain verified
- [ ] SSL certificates configured
- [ ] Backup strategy tested

### Post-Deployment
- [ ] Health checks passing
- [ ] Email delivery tested
- [ ] Monitoring alerts configured
- [ ] Backup verification completed
- [ ] Performance baselines established

### Ongoing Maintenance
- [ ] Monitor AWS SES usage and costs
- [ ] Regular security updates
- [ ] Database backup verification
- [ ] Email deliverability monitoring
- [ ] Log rotation and cleanup

## Support

For deployment issues:
1. Check health endpoint: `/healthz`
2. Review application logs
3. Verify email health: `scripts/email-health-check.py`
4. Consult troubleshooting section above

## Version History
- **v1.0.0**: Initial deployment with Gmail
- **v2.0.0**: AWS SES integration with custom domain
- **v2.1.0**: Enhanced health monitoring and fallback strategies
