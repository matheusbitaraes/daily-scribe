# Daily Scribe Deployment Checklist

This comprehensive checklist ensures reliable and secure Daily Scribe deployments. Follow all steps to prevent common deployment issues and ensure system reliability.

## 📋 Pre-Deployment Checklist

### System Requirements Verification

#### Hardware Requirements
- [ ] **CPU:** Minimum 2 cores confirmed
- [ ] **RAM:** Minimum 2GB available (4GB recommended)
- [ ] **Storage:** Minimum 20GB free space (50GB recommended)
- [ ] **Network:** Stable internet connection confirmed
- [ ] **Backup storage:** Cloud or external storage configured

#### Software Prerequisites
- [ ] **Operating System:** Ubuntu 20.04+ or Debian 11+ confirmed
- [ ] **Docker:** Version 20.10+ installed and tested
- [ ] **Docker Compose:** Version 2.x installed and tested
- [ ] **Git:** Latest version installed
- [ ] **SSH:** Secure access configured

#### Network Prerequisites
- [ ] **Domain/DDNS:** Domain name configured and resolving
- [ ] **DNS:** A/AAAA records pointing to server
- [ ] **Ports:** 80 and 443 accessible from internet
- [ ] **Router:** Port forwarding configured (if home server)
- [ ] **Firewall:** UFW or iptables configured

### Environment Configuration

#### Repository Setup
- [ ] **Repository cloned:** `git clone` completed successfully
- [ ] **Branch verified:** On correct branch (main/production)
- [ ] **Permissions set:** Correct file ownership and permissions
- [ ] **Submodules:** All submodules initialized (if any)

#### Environment Files
- [ ] **`.env` created:** Copied from `.env.example`
- [ ] **Database path:** `DB_PATH` correctly configured
- [ ] **API keys:** `GEMINI_API_KEY` and/or `OPENAI_API_KEY` set
- [ ] **Email settings:** SMTP configuration completed
- [ ] **Domain configuration:** `DOMAIN` variable set correctly
- [ ] **Security keys:** `JWT_SECRET_KEY` generated and set

#### Configuration Files
- [ ] **`config.json`:** Copied and customized from example
- [ ] **RSS sources:** All desired feeds configured
- [ ] **User emails:** Initial users added
- [ ] **Categories:** Default categories configured
- [ ] **Scheduling:** Cron settings verified

### Security Configuration

#### Access Control
- [ ] **SSH keys:** Key-based authentication configured
- [ ] **User accounts:** Non-root user created for application
- [ ] **Sudo access:** Limited sudo rights configured
- [ ] **Password policies:** Strong passwords enforced

#### Firewall Setup
- [ ] **UFW enabled:** Firewall active and configured
- [ ] **Required ports:** 22, 80, 443 allowed
- [ ] **SSH restrictions:** SSH access limited to specific IPs (if possible)
- [ ] **Service ports:** Internal ports restricted to local network

#### SSL/TLS Configuration
- [ ] **Certificate authority:** Let's Encrypt or valid CA configured
- [ ] **Domain validation:** Domain ownership verified
- [ ] **Certificate paths:** SSL certificate paths configured in Caddy
- [ ] **Security headers:** HSTS and security headers configured

## 🚀 Deployment Execution

### Pre-Deployment Testing

#### Local Testing
- [ ] **Frontend build:** `npm run build` completes successfully
- [ ] **Docker build:** `docker build` completes without errors
- [ ] **Configuration validation:** All config files valid JSON/YAML
- [ ] **Database migration:** Schema updates applied (if any)

#### Service Dependencies
- [ ] **External APIs:** Gemini/OpenAI API keys tested
- [ ] **SMTP server:** Email sending tested
- [ ] **DNS resolution:** Domain resolves correctly
- [ ] **Network connectivity:** All external services reachable

### Deployment Steps

#### Initial Deployment
- [ ] **Stop existing services:** `docker-compose down` (if updating)
- [ ] **Pull latest images:** `docker-compose pull`
- [ ] **Build new images:** `docker-compose build`
- [ ] **Start services:** `docker-compose up -d`
- [ ] **Check container health:** All containers running and healthy

#### Service Verification
- [ ] **Application container:** `daily-scribe-app` running
- [ ] **Cron container:** `daily-scribe-cron` running
- [ ] **Proxy container:** `caddy` running (if used)
- [ ] **Database:** SQLite file accessible and locked properly
- [ ] **Logs:** No error messages in startup logs

### Post-Deployment Verification

#### Health Checks
- [ ] **Health endpoint:** `/healthz` returns 200 OK
- [ ] **Database connectivity:** Database check passes
- [ ] **API endpoints:** All critical endpoints responding
- [ ] **Frontend loading:** React application loads correctly
- [ ] **Static files:** CSS/JS files loading from `/static/`

#### Functionality Testing
- [ ] **Article fetching:** RSS feeds being processed
- [ ] **Summarization:** AI summarization working
- [ ] **Email delivery:** Test digest email sent successfully
- [ ] **User preferences:** Preference management working
- [ ] **Token authentication:** Token validation working

#### Security Verification
- [ ] **HTTPS working:** SSL certificate active and valid
- [ ] **Security headers:** All security headers present
- [ ] **Firewall active:** UFW status shows active rules
- [ ] **Access logs:** Security logging functioning
- [ ] **Rate limiting:** API rate limits working

## 🔍 Testing Procedures

### Automated Testing

#### Health Check Validation
```bash
# Test health endpoint
curl -f https://yourdomain.com/healthz

# Verify response format
curl -s https://yourdomain.com/healthz | jq '.status'

# Check database connectivity
curl -s https://yourdomain.com/healthz | jq '.checks.database.status'
```

#### API Endpoint Testing
```bash
# Test article endpoint
curl -f https://yourdomain.com/articles?limit=5

# Test available dates
curl -f https://yourdomain.com/digest/available-dates

# Test categories
curl -f https://yourdomain.com/categories

# Test sources
curl -f https://yourdomain.com/sources
```

#### Frontend Testing
```bash
# Test main page load
curl -f https://yourdomain.com/

# Test SPA routing
curl -f https://yourdomain.com/digest-simulator

# Test static assets
curl -f https://yourdomain.com/static/css/main.css
curl -f https://yourdomain.com/static/js/main.js
```

### Manual Testing

#### User Journey Testing
- [ ] **Home page access:** Main page loads without errors
- [ ] **Navigation:** All menu items work correctly
- [ ] **Digest simulator:** Can generate preview digest
- [ ] **Date picker:** Available dates load correctly
- [ ] **Preference page:** Token-based access works
- [ ] **Preference updates:** Changes save successfully

#### Email Testing
- [ ] **SMTP connectivity:** Connection to email server successful
- [ ] **Test email:** Send test digest to admin email
- [ ] **Email formatting:** HTML formatting displays correctly
- [ ] **Links working:** All links in email functional
- [ ] **Unsubscribe:** Preference links work correctly

#### Performance Testing
- [ ] **Response times:** API responses under 500ms
- [ ] **Page load times:** Frontend loads under 3 seconds
- [ ] **Memory usage:** Containers using reasonable memory
- [ ] **CPU usage:** System not under excessive load

## 📊 Monitoring Setup

### Log Verification
```bash
# Check application logs
docker logs daily-scribe-app --tail 50

# Check cron logs
docker logs daily-scribe-cron --tail 50

# Check proxy logs
docker logs daily-scribe-caddy --tail 50

# Check system logs
tail -f /var/log/syslog | grep daily-scribe
```

### Metrics Collection
- [ ] **Health metrics:** `/healthz` endpoint monitoring
- [ ] **Prometheus metrics:** `/metrics` endpoint active (if configured)
- [ ] **System metrics:** CPU, memory, disk monitoring
- [ ] **Application metrics:** Request counts, response times
- [ ] **Error tracking:** Error rates and patterns

### Alerting Configuration
- [ ] **Email alerts:** Critical error notifications
- [ ] **Uptime monitoring:** External uptime checker configured
- [ ] **Disk space alerts:** Low disk space warnings
- [ ] **SSL expiration:** Certificate expiration monitoring
- [ ] **Service health:** Container health monitoring

## 🛠️ Rollback Procedures

### Rollback Checklist
- [ ] **Previous version identified:** Know which version to rollback to
- [ ] **Database backup:** Current database backed up
- [ ] **Configuration backup:** Current config files saved
- [ ] **Rollback procedure tested:** Rollback steps verified

### Emergency Rollback
```bash
# Quick rollback procedure
cd /path/to/daily-scribe

# Stop current services
docker-compose down

# Checkout previous version
git checkout previous-release-tag

# Restore previous configuration (if needed)
cp config.json.backup config.json

# Start previous version
docker-compose up -d

# Verify rollback success
curl -f https://yourdomain.com/healthz
```

## 📋 Environment-Specific Checklists

### Development Environment
- [ ] **Local database:** SQLite file in `dev_data/`
- [ ] **API URLs:** Pointing to localhost:8000
- [ ] **Debug logging:** Verbose logging enabled
- [ ] **Hot reloading:** Frontend and backend auto-reload working
- [ ] **Test data:** Sample data populated

### Staging Environment
- [ ] **Production-like config:** Similar to production setup
- [ ] **Test users:** Test email addresses configured
- [ ] **External services:** Using test/sandbox APIs
- [ ] **SSL certificate:** Valid certificate installed
- [ ] **Monitoring:** Basic monitoring configured

### Production Environment
- [ ] **Production APIs:** Using production Gemini/OpenAI keys
- [ ] **Real users:** Actual user email addresses
- [ ] **Backup systems:** All backup procedures active
- [ ] **Monitoring:** Full monitoring and alerting
- [ ] **Security hardening:** All security measures implemented

## 🔄 Post-Deployment Tasks

### Immediate Tasks (First 24 hours)
- [ ] **Monitor logs:** Check for any errors or warnings
- [ ] **Test all features:** Complete user journey testing
- [ ] **Verify backups:** Ensure backup systems working
- [ ] **Check performance:** Monitor resource usage
- [ ] **User communication:** Notify users of any changes

### Short-term Tasks (First week)
- [ ] **Performance optimization:** Tune based on usage patterns
- [ ] **User feedback:** Collect and address user issues
- [ ] **Security audit:** Review security logs and events
- [ ] **Backup verification:** Test backup restoration
- [ ] **Documentation updates:** Update deployment docs with lessons learned

### Long-term Tasks (First month)
- [ ] **Capacity planning:** Assess resource needs
- [ ] **Monitoring refinement:** Improve alerting and metrics
- [ ] **Security review:** Complete security assessment
- [ ] **Disaster recovery test:** Test full disaster recovery procedures
- [ ] **Team training:** Train team on new deployment

## ✅ Deployment Sign-off

### Technical Validation
- [ ] **All tests passed:** Automated and manual tests successful
- [ ] **Performance acceptable:** Response times within limits
- [ ] **Security verified:** All security measures active
- [ ] **Monitoring active:** All monitoring and alerting working
- [ ] **Backup verified:** Backup and recovery procedures tested

### Stakeholder Approval
- [ ] **Technical lead approval:** Technical requirements met
- [ ] **Security team approval:** Security requirements satisfied
- [ ] **Operations approval:** Operational procedures verified
- [ ] **User acceptance:** Key users have tested and approved
- [ ] **Go-live authorization:** Final approval for production use

### Documentation Complete
- [ ] **Deployment notes:** Deployment process documented
- [ ] **Configuration changes:** All changes documented
- [ ] **Known issues:** Any known issues documented
- [ ] **Support procedures:** Support escalation procedures updated
- [ ] **Rollback plan:** Rollback procedures verified and documented

---

## 📞 Emergency Contacts

### Technical Contacts
- **Primary Administrator:** `admin@yourdomain.com`
- **Secondary Administrator:** `backup-admin@yourdomain.com`
- **Development Team:** `dev-team@yourdomain.com`

### Service Contacts
- **Domain Registrar:** Contact information and account details
- **Hosting Provider:** Support contact and account information
- **DNS Provider:** Support contact and account details

### Emergency Procedures
- **Service outage:** Contact primary administrator immediately
- **Security incident:** Follow security incident response procedure
- **Data loss:** Initiate backup recovery procedure immediately
- **SSL expiration:** Emergency certificate renewal procedure

---

**Deployment Checklist Version:** 1.0  
**Last Updated:** September 7, 2025  
**Next Review:** December 7, 2025

**Note:** This checklist should be customized for your specific environment and updated based on lessons learned from each deployment.
