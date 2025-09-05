# Daily Scribe Server Deployment Guide

This guide walks you through deploying Daily Scribe to your production server.

## Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+ (recommended)
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB, recommended 50GB+
- **CPU**: 2+ cores recommended
- **Network**: Static IP or DHCP reservation

### Required Software
- Docker 20.10+
- Docker Compose 2.x
- Git
- SSH access with sudo privileges

## Quick Deployment

### 1. Clone Repository
```bash
# On your server
git clone https://github.com/yourusername/daily-scribe.git
cd daily-scribe
```

### 2. Run Deployment Script
```bash
# Make deployment script executable
chmod +x scripts/deploy-to-server.sh

# Run deployment with your configuration
./scripts/deploy-to-server.sh --production
```

### 3. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

### 4. Start Services
```bash
# Start all services
docker-compose up -d

# Verify deployment
./scripts/validate-deployment.sh
```

## Detailed Deployment Steps

### Step 1: Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git ufw fail2ban

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for Docker group changes
```

### Step 2: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow monitoring ports (optional, for internal access only)
sudo ufw allow from 192.168.0.0/16 to any port 3000  # Grafana
sudo ufw allow from 192.168.0.0/16 to any port 9090  # Prometheus

# Enable firewall
sudo ufw enable
```

### Step 3: Application Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/daily-scribe.git
cd daily-scribe

# Create production environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# Database
DB_PATH=/app/data/digest_history.db
DB_TIMEOUT=30

# DDNS Configuration (choose one provider)
DDNS_PROVIDER=duckdns
DDNS_DOMAIN=yourdomain.duckdns.org
DDNS_TOKEN=your-duckdns-token

# Email Alerts (optional but recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=daily-scribe@yourdomain.com
ALERT_EMAIL=admin@yourdomain.com

# Monitoring (optional)
GRAFANA_ADMIN_PASSWORD=secure-password

# Backup Configuration
GCS_BUCKET=your-backup-bucket  # Optional: for cloud backups
```

### Step 4: Start Services

```bash
# Create Docker network
docker network create daily-scribe-network

# Start core services
docker-compose up -d

# Wait for services to start
sleep 30

# Verify services are running
docker-compose ps
```

### Step 5: Setup Monitoring (Optional)

```bash
# Setup monitoring stack
./scripts/setup-monitoring.sh --all

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Test monitoring
./scripts/test-monitoring.sh
```

### Step 6: Configure DDNS and SSL

```bash
# Test DDNS update
./scripts/ddns-update.sh --test

# Start DDNS service
docker-compose up -d ddns

# Wait for SSL certificate generation (may take a few minutes)
docker-compose logs -f caddy
```

### Step 7: Validation

```bash
# Run comprehensive deployment validation
./scripts/validate-deployment.sh

# Test external connectivity
./scripts/validate-port-forwarding.sh

# Check health endpoint
curl -s https://yourdomain.duckdns.org/healthz | jq .
```

## Post-Deployment Configuration

### Router Configuration

1. **Port Forwarding**: Forward ports 80 and 443 to your server IP (192.168.15.55)
2. **Static IP**: Configure DHCP reservation for your server
3. **Security**: Follow the router security checklist in `docs/router-configuration-checklist.md`

### External Monitoring Setup

1. **UptimeRobot**: Create account and monitor `https://yourdomain.duckdns.org/healthz`
2. **Email Alerts**: Test SMTP configuration
3. **Backup Monitoring**: Configure backup notifications

### Regular Maintenance

```bash
# Weekly maintenance script
./scripts/weekly-maintenance.sh

# Update containers
docker-compose pull && docker-compose up -d

# Backup verification
./scripts/backup-manager.sh verify
```

## Troubleshooting

### Common Issues

1. **Services won't start**:
   ```bash
   # Check logs
   docker-compose logs
   
   # Check disk space
   df -h
   
   # Check memory
   free -m
   ```

2. **SSL certificate issues**:
   ```bash
   # Restart Caddy
   docker-compose restart caddy
   
   # Check Caddy logs
   docker-compose logs caddy
   ```

3. **Database issues**:
   ```bash
   # Check database file permissions
   ls -la data/
   
   # Test database connectivity
   sqlite3 data/digest_history.db "SELECT COUNT(*) FROM articles;"
   ```

4. **DDNS not updating**:
   ```bash
   # Check DDNS logs
   docker-compose logs ddns
   
   # Test manual update
   ./scripts/ddns-update.sh --force
   ```

### Getting Help

- Check logs: `docker-compose logs [service-name]`
- Run health checks: `./scripts/test-monitoring.sh`
- Review monitoring runbook: `docs/monitoring-runbook.md`
- Check system resources: `docker stats`

## Security Considerations

1. **Regular Updates**: Keep system and Docker images updated
2. **Backup Verification**: Test backups regularly
3. **Monitor Logs**: Review access and error logs weekly
4. **Network Security**: Use VPN for admin access to monitoring tools
5. **SSL Certificates**: Monitor certificate expiration

## Performance Optimization

1. **Resource Monitoring**: Use Grafana dashboards to monitor resource usage
2. **Log Rotation**: Ensure log rotation is working properly
3. **Database Optimization**: Monitor database size and performance
4. **Container Limits**: Set appropriate resource limits in docker-compose.yml

---

For detailed operational procedures, see `docs/monitoring-runbook.md`
