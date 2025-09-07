# Daily Scribe Security Guide

This guide covers security best practices, configuration, and procedures for Daily Scribe deployment and operation.

## 🔒 Security Overview

Daily Scribe implements multiple layers of security to protect user data, system integrity, and prevent unauthorized access. This guide covers all security aspects from deployment to ongoing operations.

### Security Principles
- **Defense in Depth:** Multiple security layers and controls
- **Least Privilege:** Minimal access rights and permissions
- **Secure by Default:** Secure configurations out of the box
- **Regular Updates:** Keep systems and dependencies current
- **Monitoring & Alerting:** Continuous security monitoring

## 🔐 Authentication & Authorization

### JWT Token Security

**Token Configuration:**
```bash
# Environment variables for token security
JWT_SECRET_KEY=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=168  # 7 days
JWT_MAX_REQUESTS=50
```

**Token Best Practices:**
1. **Strong Secret Keys:** Use cryptographically secure random keys (256-bit minimum)
2. **Limited Lifetime:** Tokens expire after 7 days or 50 requests
3. **Secure Transmission:** Always use HTTPS for token URLs
4. **No Logging:** Never log complete tokens in application logs
5. **Revocation:** Implement token blacklisting if needed

**Generating Secure Keys:**
```bash
# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

### User Access Control

**Email-Based Authentication:**
- Users receive secure token links via email
- No passwords stored in the system
- Token usage tracking and rate limiting
- Automatic token expiration

**Administrative Access:**
- Separate admin credentials for system management
- SSH key-based authentication (no passwords)
- Sudo access with logging
- Regular access review and rotation

## 🛡️ Network Security

### Firewall Configuration

**UFW (Ubuntu Firewall) Setup:**
```bash
# Reset and configure UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential services
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Restrict SSH to specific IPs (recommended)
sudo ufw delete allow 22/tcp
sudo ufw allow from YOUR_IP_ADDRESS to any port 22 comment 'SSH from admin IP'

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

**Advanced Firewall Rules:**
```bash
# Rate limiting for HTTP/HTTPS
sudo ufw limit 80/tcp
sudo ufw limit 443/tcp

# Block common attack ports
sudo ufw deny 3389 comment 'Block RDP'
sudo ufw deny 1433 comment 'Block MSSQL'
sudo ufw deny 3306 comment 'Block MySQL'

# Allow monitoring from internal network only
sudo ufw allow from 192.168.0.0/16 to any port 3000 comment 'Grafana internal'
sudo ufw allow from 192.168.0.0/16 to any port 9090 comment 'Prometheus internal'
```

### SSL/TLS Configuration

**Caddy TLS Settings:**
```caddyfile
# In Caddyfile - strong TLS configuration
{
    # Use only strong TLS versions
    protocols tls1.2 tls1.3
    
    # Strong cipher suites
    ciphers TLS_AES_256_GCM_SHA384 TLS_CHACHA20_POLY1305_SHA256 TLS_AES_128_GCM_SHA256
}

your-domain.com {
    # Security headers
    header {
        # HSTS with preload
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        
        # Prevent clickjacking
        X-Frame-Options "DENY"
        
        # Content type protection
        X-Content-Type-Options "nosniff"
        
        # XSS protection
        X-XSS-Protection "1; mode=block"
        
        # Referrer policy
        Referrer-Policy "strict-origin-when-cross-origin"
        
        # Content Security Policy
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; frame-ancestors 'none';"
        
        # Remove server information
        -Server
    }
    
    reverse_proxy app:8000
}
```

**Certificate Management:**
```bash
# Check certificate status
docker exec daily-scribe-caddy caddy list-certificates

# Force certificate renewal
docker exec daily-scribe-caddy caddy reload --config /etc/caddy/Caddyfile

# Check certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Network Hardening

**Router Security:**
- Change default admin passwords
- Disable WPS and UPnP
- Enable WPA3 or strong WPA2
- Hide SSID broadcast
- Regular firmware updates
- Enable firewall and intrusion detection

**Port Management:**
- Only forward required ports (80, 443)
- Use non-standard SSH port (e.g., 2222)
- Close unused services and ports
- Regular port scanning audits

## 🔒 Application Security

### FastAPI Security Configuration

**CORS Security:**
```python
# In production, restrict CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Input Validation:**
```python
# Example secure input validation
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional

class UserPreferencesUpdate(BaseModel):
    enabled_sources: Optional[List[int]] = None
    enabled_categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v:
            # Limit keyword length and count
            if len(v) > 10:
                raise ValueError('Maximum 10 keywords allowed')
            for keyword in v:
                if len(keyword) > 50:
                    raise ValueError('Keywords must be under 50 characters')
        return v
```

**Rate Limiting:**
```python
# Implement rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/data")
@limiter.limit("100/hour")
async def get_data(request: Request):
    return {"data": "example"}
```

### Database Security

**SQLite Security:**
```bash
# Set proper file permissions
chmod 600 data/digest_history.db
chown appuser:appuser data/digest_history.db

# Backup encryption
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
    data/digest_history.db
```

**SQL Injection Prevention:**
```python
# Always use parameterized queries
cursor.execute("SELECT * FROM articles WHERE category = ?", (category,))

# Never use string formatting
# BAD: cursor.execute(f"SELECT * FROM articles WHERE category = '{category}'")
```

## 🔍 Security Monitoring

### Log Security

**Security Event Logging:**
```python
import logging
import json
from datetime import datetime

security_logger = logging.getLogger('security')

def log_security_event(event_type, details, request=None):
    """Log security-relevant events"""
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'ip_address': request.client.host if request else None,
        'user_agent': request.headers.get('user-agent') if request else None
    }
    security_logger.warning(json.dumps(event))

# Usage examples
log_security_event('INVALID_TOKEN', {'token_prefix': token[:8]}, request)
log_security_event('RATE_LIMIT_EXCEEDED', {'endpoint': '/api/data'}, request)
log_security_event('ADMIN_LOGIN', {'user': 'admin'})
```

**Log Analysis:**
```bash
# Monitor for security events
tail -f /var/log/daily-scribe/security.log | grep -E "(INVALID_TOKEN|RATE_LIMIT|ADMIN_LOGIN)"

# Failed authentication attempts
grep "INVALID_TOKEN" /var/log/daily-scribe/security.log | wc -l

# Rate limiting events
grep "RATE_LIMIT_EXCEEDED" /var/log/daily-scribe/security.log | tail -10
```

### Intrusion Detection

**Fail2Ban Configuration:**
```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[daily-scribe-auth]
enabled = true
port = 80,443
filter = daily-scribe-auth
logpath = /var/log/daily-scribe/security.log
action = iptables-multiport[name=daily-scribe, port="http,https"]

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
```

**Custom Fail2Ban Filter:**
```ini
# /etc/fail2ban/filter.d/daily-scribe-auth.conf
[Definition]
failregex = .*"event_type": "INVALID_TOKEN".*"ip_address": "<HOST>"
            .*"event_type": "RATE_LIMIT_EXCEEDED".*"ip_address": "<HOST>"
ignoreregex =
```

### Security Alerts

**Email Alerts for Security Events:**
```bash
#!/bin/bash
# /usr/local/bin/security-alert.sh

ALERT_EMAIL="admin@yourdomain.com"
LOG_FILE="/var/log/daily-scribe/security.log"
TEMP_FILE="/tmp/security_events_$(date +%s).log"

# Check for security events in the last 5 minutes
grep "$(date -d '5 minutes ago' '+%Y-%m-%d %H:%M')" "$LOG_FILE" > "$TEMP_FILE"

if [ -s "$TEMP_FILE" ]; then
    {
        echo "Security Alert - Daily Scribe"
        echo "Time: $(date)"
        echo "Server: $(hostname)"
        echo ""
        echo "Recent security events:"
        cat "$TEMP_FILE"
    } | mail -s "Daily Scribe Security Alert" "$ALERT_EMAIL"
fi

rm -f "$TEMP_FILE"
```

**Cron Job for Security Monitoring:**
```bash
# Add to crontab
*/5 * * * * /usr/local/bin/security-alert.sh
```

## 🛠️ Security Procedures

### Regular Security Tasks

**Daily:**
- Monitor security logs
- Check system health and alerts
- Verify backup integrity
- Review access logs

**Weekly:**
- Update system packages
- Review user access
- Check certificate status
- Analyze security metrics

**Monthly:**
- Security patch updates
- Access control audit
- Password/key rotation
- Penetration testing
- Review security configurations

**Quarterly:**
- Full security audit
- Disaster recovery testing
- Security training update
- Third-party security assessment

### Incident Response

**Security Incident Procedure:**

1. **Detection & Analysis:**
   - Monitor alerts and logs
   - Assess threat severity
   - Document initial findings

2. **Containment:**
   - Isolate affected systems
   - Block malicious IP addresses
   - Preserve evidence

3. **Eradication:**
   - Remove malware/threats
   - Patch vulnerabilities
   - Update security controls

4. **Recovery:**
   - Restore from clean backups
   - Implement additional monitoring
   - Gradual system restoration

5. **Post-Incident:**
   - Document lessons learned
   - Update procedures
   - Implement improvements

**Emergency Contacts:**
```bash
# Security incident escalation
PRIMARY_CONTACT="admin@yourdomain.com"
SECONDARY_CONTACT="backup-admin@yourdomain.com"
SECURITY_TEAM="security@yourdomain.com"
```

### Backup Security

**Encrypted Backups:**
```bash
#!/bin/bash
# Secure backup script with encryption

BACKUP_SOURCE="/app/data"
BACKUP_DEST="/backups/encrypted"
GPG_RECIPIENT="admin@yourdomain.com"
DATE=$(date +%Y%m%d_%H%M%S)

# Create encrypted backup
tar czf - "$BACKUP_SOURCE" | \
gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" \
> "$BACKUP_DEST/daily_scribe_backup_$DATE.tar.gz.gpg"

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup created successfully: daily_scribe_backup_$DATE.tar.gz.gpg"
else
    echo "Backup failed!" | mail -s "Backup Failure Alert" admin@yourdomain.com
fi
```

**Backup Verification:**
```bash
# Test backup decryption and integrity
gpg --decrypt /backups/encrypted/daily_scribe_backup_20250907_120000.tar.gz.gpg | \
tar tzf - > /dev/null

if [ $? -eq 0 ]; then
    echo "Backup integrity verified"
else
    echo "Backup corruption detected!"
fi
```

## 🔧 Security Tools & Commands

### Security Scanning

**System Vulnerability Scanning:**
```bash
# Install and run Lynis security audit
sudo apt install lynis
sudo lynis audit system

# Check for rootkits
sudo apt install rkhunter
sudo rkhunter --check

# Network scanning
nmap -sS -O -p 1-65535 localhost
```

**Application Security Testing:**
```bash
# Check for dependency vulnerabilities
npm audit
pip-audit

# SSL/TLS testing
testssl.sh yourdomain.com

# HTTP header security
curl -I https://yourdomain.com | grep -E "(X-|Strict-Transport|Content-Security)"
```

### Access Control Commands

**User Management:**
```bash
# List active sessions
who
w

# Check sudo access logs
sudo tail /var/log/auth.log | grep sudo

# Review SSH connections
sudo tail /var/log/auth.log | grep sshd

# Check failed login attempts
sudo grep "Failed password" /var/log/auth.log | tail -10
```

**File Permissions Audit:**
```bash
# Check for world-writable files
find /app -type f -perm -002 -ls

# Check for SUID/SGID files
find /app -type f \( -perm -4000 -o -perm -2000 \) -ls

# Verify critical file permissions
ls -la /app/data/
ls -la /app/config.json
```

## 📋 Security Checklist

### Pre-Deployment Security

- [ ] Strong passwords/keys generated
- [ ] Firewall configured and enabled
- [ ] SSL certificates configured
- [ ] Security headers implemented
- [ ] Input validation implemented
- [ ] Rate limiting configured
- [ ] Logging and monitoring setup
- [ ] Backup encryption enabled
- [ ] Access controls configured
- [ ] Security scanning completed

### Post-Deployment Security

- [ ] All services running securely
- [ ] Monitoring alerts configured
- [ ] Security logs functioning
- [ ] Backup verification working
- [ ] Incident response plan tested
- [ ] Emergency contacts updated
- [ ] Documentation complete
- [ ] Team security training completed

### Ongoing Security Maintenance

- [ ] Regular security updates
- [ ] Log review and analysis
- [ ] Access control audits
- [ ] Backup testing
- [ ] Security metric review
- [ ] Threat intelligence monitoring
- [ ] Compliance verification
- [ ] Security training updates

## 🚨 Security Alerts Configuration

### Automated Monitoring

**Security Event Detection:**
```bash
#!/bin/bash
# /usr/local/bin/security-monitor.sh

LOG_FILES=(
    "/var/log/daily-scribe/security.log"
    "/var/log/auth.log"
    "/var/log/ufw.log"
)

ALERT_PATTERNS=(
    "INVALID_TOKEN"
    "RATE_LIMIT_EXCEEDED"
    "Failed password"
    "BLOCK"
)

for log_file in "${LOG_FILES[@]}"; do
    for pattern in "${ALERT_PATTERNS[@]}"; do
        recent_events=$(tail -n 100 "$log_file" | grep -c "$pattern")
        if [ "$recent_events" -gt 5 ]; then
            echo "ALERT: High frequency of $pattern events in $log_file ($recent_events occurrences)"
        fi
    done
done
```

---

**Important:** This security guide should be reviewed and updated regularly. Security is an ongoing process, not a one-time setup. Always test security measures in a safe environment before applying to production.

**Last Updated:** September 7, 2025  
**Next Security Review:** December 7, 2025
