# Daily Scribe Monitoring Runbook

This runbook provides operational procedures for monitoring and maintaining your Daily Scribe deployment.

## Quick Reference

### Emergency Contacts
- **Primary Admin**: [Your email/phone]
- **Secondary Admin**: [Backup contact]
- **ISP Support**: [ISP contact info]
- **Domain Provider**: [Domain support]

### Critical URLs
- **Application**: https://yourdomain.duckdns.org
- **Health Check**: https://yourdomain.duckdns.org/healthz
- **Status Page**: https://yourdomain.duckdns.org/static/status.html
- **Grafana**: http://localhost:3000 (if configured)
- **Prometheus**: http://localhost:9090 (if configured)

### Common Commands
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs app
docker-compose logs caddy

# Restart services
docker-compose restart app
docker-compose restart caddy

# Full restart
docker-compose down && docker-compose up -d

# Test monitoring
./scripts/test-monitoring.sh
```

## Alert Response Procedures

### Service Down Alert

**Symptoms**: Application not responding, health check fails
**Severity**: Critical
**Response Time**: Immediate (< 5 minutes)

**Investigation Steps**:
1. Check if containers are running:
   ```bash
   docker-compose ps
   ```

2. Check application logs:
   ```bash
   docker-compose logs --tail=50 app
   ```

3. Check system resources:
   ```bash
   df -h
   free -m
   docker stats --no-stream
   ```

**Resolution Steps**:
1. **If container stopped**: Restart the service
   ```bash
   docker-compose up -d app
   ```

2. **If out of disk space**: Clean up logs and data
   ```bash
   # Clean Docker
   docker system prune -f
   
   # Clean old logs
   sudo journalctl --vacuum-time=7d
   
   # Check large files
   du -sh /* | sort -hr | head -10
   ```

3. **If out of memory**: Restart services
   ```bash
   docker-compose restart app
   ```

4. **If database corruption**: Restore from backup
   ```bash
   # Stop services
   docker-compose down
   
   # Restore database (see Database Issues section)
   ./scripts/backup-manager.sh restore latest
   
   # Start services
   docker-compose up -d
   ```

**Escalation**: If service cannot be restored within 15 minutes, contact ISP/hosting provider.

### High Error Rate Alert

**Symptoms**: Many HTTP 5xx errors, slow responses
**Severity**: Warning
**Response Time**: 10 minutes

**Investigation Steps**:
1. Check error logs:
   ```bash
   docker-compose logs app | grep -i error
   ```

2. Check system load:
   ```bash
   uptime
   top
   ```

3. Verify external dependencies:
   ```bash
   # Test feed sources
   curl -I https://feeds.example.com/rss
   
   # Test DNS
   nslookup yourdomain.duckdns.org
   ```

**Resolution Steps**:
1. **If high load**: Scale down or restart
   ```bash
   docker-compose restart app
   ```

2. **If external dependency issues**: Wait or configure fallbacks

3. **If persistent errors**: Check application configuration
   ```bash
   # Verify environment variables
   docker-compose config
   
   # Check config files
   cat config.json
   ```

### Database Issues Alert

**Symptoms**: Database connectivity failures, slow queries
**Severity**: Critical
**Response Time**: Immediate

**Investigation Steps**:
1. Check database file:
   ```bash
   ls -la data/digest_history.db*
   ```

2. Check Litestream status:
   ```bash
   docker-compose logs litestream
   ```

3. Test database manually:
   ```bash
   sqlite3 data/digest_history.db "SELECT COUNT(*) FROM articles;"
   ```

**Resolution Steps**:
1. **If database locked**: Restart application
   ```bash
   docker-compose restart app
   ```

2. **If database corrupted**: Restore from backup
   ```bash
   # Stop all services
   docker-compose down
   
   # List available backups
   ./scripts/backup-manager.sh list
   
   # Restore latest backup
   ./scripts/backup-manager.sh restore latest
   
   # Verify restoration
   ./scripts/backup-manager.sh verify
   
   # Start services
   docker-compose up -d
   ```

3. **If Litestream issues**: Reconfigure backup
   ```bash
   # Check configuration
   cat litestream.yml
   
   # Test backup manually
   docker-compose exec litestream litestream snapshots data/digest_history.db
   ```

### DDNS Update Failure

**Symptoms**: Domain not resolving to current IP
**Severity**: Warning
**Response Time**: 30 minutes

**Investigation Steps**:
1. Check current public IP:
   ```bash
   curl -s https://ipv4.icanhazip.com
   ```

2. Check DNS resolution:
   ```bash
   nslookup yourdomain.duckdns.org
   dig yourdomain.duckdns.org
   ```

3. Check DDNS logs:
   ```bash
   docker-compose logs ddns
   ```

**Resolution Steps**:
1. **Manual DDNS update**:
   ```bash
   # Update DuckDNS manually
   curl "https://www.duckdns.org/update?domains=yourdomain&token=YOUR_TOKEN&ip="
   
   # Or restart DDNS service
   docker-compose restart ddns
   ```

2. **If authentication fails**: Check credentials
   ```bash
   # Verify environment variables
   echo $DDNS_TOKEN
   echo $DDNS_DOMAIN
   ```

3. **If provider issues**: Switch to backup provider or wait

### Backup Failure Alert

**Symptoms**: Litestream backup has not succeeded recently
**Severity**: Warning
**Response Time**: 1 hour

**Investigation Steps**:
1. Check Litestream logs:
   ```bash
   docker-compose logs litestream
   ```

2. Test backup manually:
   ```bash
   # Force a backup
   docker-compose exec litestream litestream snapshots -s data/digest_history.db
   ```

3. Check GCS credentials and permissions:
   ```bash
   # Verify service account file
   ls -la gcs-service-account.json
   
   # Test GCS access
   docker-compose exec litestream gsutil ls gs://your-bucket/
   ```

**Resolution Steps**:
1. **Fix authentication**: Update service account key
2. **Fix permissions**: Update GCS bucket permissions
3. **Fix configuration**: Update litestream.yml
4. **Manual backup**: Create manual backup as fallback

### SSL Certificate Issues

**Symptoms**: HTTPS not working, certificate expired
**Severity**: Warning
**Response Time**: 2 hours

**Investigation Steps**:
1. Check certificate status:
   ```bash
   echo | openssl s_client -servername yourdomain.duckdns.org -connect yourdomain.duckdns.org:443 2>/dev/null | openssl x509 -noout -dates
   ```

2. Check Caddy logs:
   ```bash
   docker-compose logs caddy
   ```

**Resolution Steps**:
1. **Restart Caddy**: Usually resolves certificate renewal issues
   ```bash
   docker-compose restart caddy
   ```

2. **Force certificate renewal**: Clear Caddy data
   ```bash
   docker-compose down
   sudo rm -rf caddy_data/
   docker-compose up -d caddy
   ```

3. **Check domain configuration**: Verify Caddyfile syntax

## Maintenance Procedures

### Weekly Maintenance

Run every Sunday at a low-traffic time:

1. **System Update Check**:
   ```bash
   # Check for system updates
   sudo apt update && sudo apt list --upgradable
   
   # Check Docker updates
   docker-compose pull
   ```

2. **Log Cleanup**:
   ```bash
   # Clean Docker logs
   docker system prune -f
   
   # Clean system logs
   sudo journalctl --vacuum-time=30d
   ```

3. **Backup Verification**:
   ```bash
   ./scripts/backup-manager.sh verify
   ./scripts/backup-manager.sh list | head -5
   ```

4. **Monitoring Test**:
   ```bash
   ./scripts/test-monitoring.sh
   ```

5. **Security Check**:
   ```bash
   # Check for unauthorized access
   sudo grep "Failed password" /var/log/auth.log | tail -10
   
   # Check open ports
   nmap -sT localhost
   ```

### Monthly Maintenance

Run on the first Sunday of each month:

1. **Full System Backup**:
   ```bash
   # Create full backup
   tar -czf daily-scribe-backup-$(date +%Y%m%d).tar.gz \
     --exclude='*.log' \
     --exclude='caddy_data' \
     /home/user/daily-scribe/
   ```

2. **Performance Review**:
   - Review Grafana dashboards (if configured)
   - Check resource usage trends
   - Review alert frequency and accuracy

3. **Security Updates**:
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose pull && docker-compose up -d
   ```

4. **Configuration Review**:
   - Review and update monitoring thresholds
   - Update contact information
   - Review and test disaster recovery procedures

### Quarterly Maintenance

Run every 3 months:

1. **Disaster Recovery Test**: Full restore from backup to test environment
2. **Security Audit**: Review access logs, update passwords
3. **Capacity Planning**: Review growth trends and resource needs
4. **Documentation Update**: Update this runbook with lessons learned

## Monitoring Tools Usage

### Prometheus Queries

Access Prometheus at http://localhost:9090

**Useful queries**:
```promql
# Request rate
rate(daily_scribe_requests_total[5m])

# Error rate
rate(daily_scribe_errors_total[5m]) / rate(daily_scribe_requests_total[5m])

# Database health
daily_scribe_database_health

# Disk usage
daily_scribe_disk_usage_percent

# Memory usage (if node-exporter running)
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

**Key panels to monitor**:
- Service uptime percentage
- Request rate and response times
- Error rate trends
- Resource utilization (CPU, memory, disk)
- Database performance metrics

### Log Analysis

**Common log analysis commands**:
```bash
# Find errors in application logs
docker-compose logs app | grep -i error | tail -20

# Monitor real-time logs
docker-compose logs -f app

# Search for specific patterns
docker-compose logs app | grep "digest generated"

# Count requests by endpoint
docker-compose logs caddy | grep "GET" | awk '{print $7}' | sort | uniq -c
```

## Troubleshooting Guide

### Application Won't Start

1. Check environment variables:
   ```bash
   docker-compose config
   ```

2. Check file permissions:
   ```bash
   ls -la data/
   ls -la config.json
   ```

3. Check port conflicts:
   ```bash
   netstat -tlnp | grep :8000
   ```

### High Memory Usage

1. Check container memory usage:
   ```bash
   docker stats --no-stream
   ```

2. Restart memory-intensive services:
   ```bash
   docker-compose restart app
   ```

3. Check for memory leaks in logs

### Slow Performance

1. Check system load:
   ```bash
   uptime
   iostat -x 1 5
   ```

2. Check database query performance in logs

3. Review feed processing times

### Network Connectivity Issues

1. Test external connectivity:
   ```bash
   ping 8.8.8.8
   curl -I https://www.google.com
   ```

2. Test DNS resolution:
   ```bash
   nslookup yourdomain.duckdns.org
   ```

3. Check firewall rules:
   ```bash
   sudo ufw status
   ```

## Contact Information and Escalation

### Internal Escalation
1. **Level 1**: Automated restart procedures
2. **Level 2**: Manual intervention by admin
3. **Level 3**: Contact secondary admin or external support

### External Support
- **ISP Support**: For network connectivity issues
- **Domain Provider**: For DNS resolution problems
- **Cloud Provider**: For backup/storage issues (if using cloud)
- **Community Support**: Daily Scribe GitHub issues

## Document Maintenance

- **Last Updated**: [Date]
- **Next Review**: [Date + 3 months]
- **Version**: 1.0
- **Owner**: [Your name/team]

### Change Log
- v1.0: Initial version created during Task 11 implementation

---

*This runbook should be regularly updated based on operational experience and incidents.*
