# Daily Scribe Backup and Recovery Guide

This guide covers comprehensive backup strategies, disaster recovery procedures, and data protection for Daily Scribe deployments.

## 📦 Backup Strategy Overview

### Backup Components
- **Database:** SQLite database with all user data and articles
- **Configuration:** Application configuration files and secrets
- **Application Code:** Source code and customizations
- **System Configuration:** Server settings and environment configuration
- **SSL Certificates:** TLS certificates and keys

### Backup Types
- **Continuous Backups:** Real-time database replication with Litestream
- **Scheduled Backups:** Daily full system backups
- **Configuration Backups:** On-demand backups before changes
- **Emergency Backups:** Quick manual backups before maintenance

### Recovery Objectives
- **RTO (Recovery Time Objective):** 15 minutes for database, 1 hour for full system
- **RPO (Recovery Point Objective):** Maximum 5 minutes data loss
- **Data Integrity:** 100% data consistency verification
- **Service Availability:** 99.9% uptime target

## 🗄️ Database Backup (SQLite + Litestream)

### Litestream Configuration

**Setup Litestream for Continuous Backup:**
```yaml
# litestream.yml
dbs:
  - path: /data/digest_history.db
    replicas:
      - type: gcs
        bucket: your-daily-scribe-backups
        path: database
        retention: 720h  # 30 days
        sync-interval: 1s
        snapshot-interval: 1h
      - type: file
        path: /backups/local
        retention: 168h  # 7 days
        sync-interval: 10s
        snapshot-interval: 6h
```

**Docker Compose Integration:**
```yaml
# docker-compose.yml excerpt
services:
  litestream:
    image: litestream/litestream:latest
    container_name: daily-scribe-litestream
    restart: unless-stopped
    volumes:
      - ./data:/data:ro
      - ./backups:/backups
      - ./litestream.yml:/etc/litestream.yml:ro
      - ./gcs-service-account.json:/gcs-service-account.json:ro
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/gcs-service-account.json
    command: replicate
    depends_on:
      - app
```

### Manual Database Backup

**Create Immediate Backup:**
```bash
#!/bin/bash
# backup-database.sh

DB_PATH="/app/data/digest_history.db"
BACKUP_DIR="/backups/manual"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="digest_history_backup_${TIMESTAMP}.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create SQLite backup using .backup command (safe for active databases)
sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/$BACKUP_FILE"

# Verify backup integrity
if sqlite3 "$BACKUP_DIR/$BACKUP_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database backup created: $BACKUP_FILE"
    echo "Size: $(du -h $BACKUP_DIR/$BACKUP_FILE | cut -f1)"
else
    echo "❌ Database backup failed integrity check!"
    exit 1
fi

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"
echo "✅ Backup compressed: ${BACKUP_FILE}.gz"
```

**Automated Backup Script:**
```bash
#!/bin/bash
# automated-backup.sh

set -e

# Configuration
BACKUP_ROOT="/backups"
RETENTION_DAYS=30
ALERT_EMAIL="admin@yourdomain.com"

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/automated/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

# Database backup
echo "Creating database backup..."
sqlite3 /app/data/digest_history.db ".backup $BACKUP_DIR/digest_history.db"

# Configuration backup
echo "Backing up configuration..."
cp /app/config.json "$BACKUP_DIR/"
cp /app/.env "$BACKUP_DIR/env.backup"

# System configuration
echo "Backing up system configuration..."
cp -r /etc/caddy "$BACKUP_DIR/caddy_config"
cp /etc/crontab "$BACKUP_DIR/system_crontab"

# Docker configuration
echo "Backing up Docker configuration..."
cp /app/docker-compose.yml "$BACKUP_DIR/"
cp /app/Dockerfile "$BACKUP_DIR/"

# Create archive
echo "Creating archive..."
tar -czf "$BACKUP_ROOT/daily_scribe_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_ROOT/automated" "$TIMESTAMP"

# Verify archive
if tar -tzf "$BACKUP_ROOT/daily_scribe_backup_$TIMESTAMP.tar.gz" > /dev/null; then
    echo "✅ Backup archive created successfully"
    rm -rf "$BACKUP_DIR"  # Remove uncompressed backup
else
    echo "❌ Backup archive verification failed!" | mail -s "Backup Failure" "$ALERT_EMAIL"
    exit 1
fi

# Cleanup old backups
find "$BACKUP_ROOT" -name "daily_scribe_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Automated backup completed: daily_scribe_backup_$TIMESTAMP.tar.gz"
```

### Database Integrity Verification

**Verify Database Health:**
```bash
#!/bin/bash
# verify-database.sh

DB_PATH="/app/data/digest_history.db"

echo "Verifying database integrity..."

# Check database integrity
INTEGRITY_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
if [ "$INTEGRITY_CHECK" = "ok" ]; then
    echo "✅ Database integrity check passed"
else
    echo "❌ Database integrity check failed: $INTEGRITY_CHECK"
    exit 1
fi

# Check foreign key constraints
FOREIGN_KEY_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA foreign_key_check;")
if [ -z "$FOREIGN_KEY_CHECK" ]; then
    echo "✅ Foreign key constraints verified"
else
    echo "❌ Foreign key constraint violations found: $FOREIGN_KEY_CHECK"
fi

# Check database statistics
echo "Database statistics:"
sqlite3 "$DB_PATH" "SELECT 
    'Articles: ' || COUNT(*) FROM articles UNION ALL
    SELECT 'Users: ' || COUNT(*) FROM users UNION ALL
    SELECT 'Sources: ' || COUNT(*) FROM sources;"

# Check database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "Database size: $DB_SIZE"

# Check WAL file size (if exists)
if [ -f "${DB_PATH}-wal" ]; then
    WAL_SIZE=$(du -h "${DB_PATH}-wal" | cut -f1)
    echo "WAL file size: $WAL_SIZE"
fi
```

## 💾 Configuration Backup

### Application Configuration

**Backup Configuration Files:**
```bash
#!/bin/bash
# backup-config.sh

CONFIG_BACKUP_DIR="/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONFIG_ARCHIVE="config_backup_$TIMESTAMP.tar.gz"

mkdir -p "$CONFIG_BACKUP_DIR"

# Application configuration
tar -czf "$CONFIG_BACKUP_DIR/$CONFIG_ARCHIVE" \
    -C /app \
    config.json \
    .env \
    docker-compose.yml \
    Dockerfile \
    litestream.yml \
    Caddyfile

# System configuration
tar -czf "$CONFIG_BACKUP_DIR/system_config_$TIMESTAMP.tar.gz" \
    /etc/caddy \
    /etc/cron.d/daily-scribe-cron \
    /etc/systemd/system/daily-scribe* \
    /etc/ufw/user.rules

echo "✅ Configuration backup created: $CONFIG_ARCHIVE"
```

### Secrets and Credentials Backup

**Secure Secrets Backup:**
```bash
#!/bin/bash
# backup-secrets.sh

SECRETS_BACKUP_DIR="/backups/secrets"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
GPG_RECIPIENT="admin@yourdomain.com"

mkdir -p "$SECRETS_BACKUP_DIR"

# Create encrypted secrets backup
{
    echo "# Daily Scribe Secrets Backup - $TIMESTAMP"
    echo "GEMINI_API_KEY=$(grep GEMINI_API_KEY /app/.env | cut -d= -f2)"
    echo "OPENAI_API_KEY=$(grep OPENAI_API_KEY /app/.env | cut -d= -f2)"
    echo "SMTP_PASSWORD=$(grep SMTP_PASSWORD /app/.env | cut -d= -f2)"
    echo "JWT_SECRET_KEY=$(grep JWT_SECRET_KEY /app/.env | cut -d= -f2)"
} | gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" \
    > "$SECRETS_BACKUP_DIR/secrets_$TIMESTAMP.gpg"

# Backup SSL certificates (if self-managed)
if [ -d "/etc/ssl/daily-scribe" ]; then
    tar -czf - /etc/ssl/daily-scribe | \
    gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" \
    > "$SECRETS_BACKUP_DIR/ssl_certs_$TIMESTAMP.tar.gz.gpg"
fi

echo "✅ Encrypted secrets backup created"
```

## 🔄 Recovery Procedures

### Database Recovery

**Restore from Litestream:**
```bash
#!/bin/bash
# restore-from-litestream.sh

set -e

RESTORE_PATH="/app/data/digest_history.db"
BACKUP_PATH="/backups/recovery"
TIMESTAMP="${1:-$(date -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')}"

echo "Restoring database from Litestream backup..."

# Stop application to prevent database access
docker-compose stop app cron

# Backup current database (if exists)
if [ -f "$RESTORE_PATH" ]; then
    mv "$RESTORE_PATH" "${RESTORE_PATH}.backup.$(date +%s)"
    echo "Current database backed up"
fi

# Restore from Litestream
docker run --rm \
    -v $(pwd)/litestream.yml:/etc/litestream.yml:ro \
    -v $(pwd)/gcs-service-account.json:/gcs-service-account.json:ro \
    -v $(dirname $RESTORE_PATH):/data \
    -e GOOGLE_APPLICATION_CREDENTIALS=/gcs-service-account.json \
    litestream/litestream:latest \
    restore -if-replica-exists -timestamp "$TIMESTAMP" /data/digest_history.db

# Verify restored database
if sqlite3 "$RESTORE_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database restored and verified"
    
    # Restart application
    docker-compose start app cron
    echo "✅ Application restarted"
else
    echo "❌ Restored database failed integrity check!"
    exit 1
fi
```

**Restore from Manual Backup:**
```bash
#!/bin/bash
# restore-manual-backup.sh

BACKUP_FILE="$1"
RESTORE_PATH="/app/data/digest_history.db"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.db.gz>"
    exit 1
fi

echo "Restoring from manual backup: $BACKUP_FILE"

# Stop application
docker-compose stop app cron

# Backup current database
if [ -f "$RESTORE_PATH" ]; then
    mv "$RESTORE_PATH" "${RESTORE_PATH}.backup.$(date +%s)"
fi

# Restore from backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > "$RESTORE_PATH"
else
    cp "$BACKUP_FILE" "$RESTORE_PATH"
fi

# Set correct permissions
chown appuser:appuser "$RESTORE_PATH"
chmod 640 "$RESTORE_PATH"

# Verify and restart
if sqlite3 "$RESTORE_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database restored successfully"
    docker-compose start app cron
else
    echo "❌ Database restore failed!"
    exit 1
fi
```

### Full System Recovery

**Complete System Restoration:**
```bash
#!/bin/bash
# full-system-recovery.sh

set -e

BACKUP_ARCHIVE="$1"
TEMP_DIR="/tmp/daily_scribe_recovery"

if [ -z "$BACKUP_ARCHIVE" ]; then
    echo "Usage: $0 <backup_archive.tar.gz>"
    exit 1
fi

echo "Starting full system recovery from: $BACKUP_ARCHIVE"

# Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Extract backup
echo "Extracting backup archive..."
tar -xzf "$BACKUP_ARCHIVE"

# Stop all services
echo "Stopping services..."
docker-compose down

# Restore database
echo "Restoring database..."
cp */digest_history.db /app/data/

# Restore configuration
echo "Restoring configuration..."
cp */config.json /app/
cp */env.backup /app/.env
cp */docker-compose.yml /app/
cp */Dockerfile /app/

# Restore system configuration
if [ -d "*/caddy_config" ]; then
    echo "Restoring Caddy configuration..."
    sudo cp -r */caddy_config/* /etc/caddy/
fi

# Set correct permissions
echo "Setting permissions..."
sudo chown -R appuser:appuser /app/data
chmod 640 /app/data/digest_history.db

# Restart services
echo "Starting services..."
cd /app
docker-compose up -d

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 30

# Verify recovery
echo "Verifying recovery..."
if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Full system recovery completed successfully"
else
    echo "❌ System recovery verification failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"
```

### Configuration Recovery

**Restore Configuration Only:**
```bash
#!/bin/bash
# restore-config.sh

CONFIG_BACKUP="$1"
TEMP_DIR="/tmp/config_recovery"

if [ -z "$CONFIG_BACKUP" ]; then
    echo "Usage: $0 <config_backup.tar.gz>"
    exit 1
fi

# Extract configuration backup
mkdir -p "$TEMP_DIR"
tar -xzf "$CONFIG_BACKUP" -C "$TEMP_DIR"

# Backup current configuration
cp /app/config.json /app/config.json.backup.$(date +%s)
cp /app/.env /app/.env.backup.$(date +%s)

# Restore configuration files
cp "$TEMP_DIR"/config.json /app/
cp "$TEMP_DIR"/env.backup /app/.env

# Restart application to apply changes
docker-compose restart app

echo "✅ Configuration restored successfully"
rm -rf "$TEMP_DIR"
```

## 🧪 Recovery Testing

### Automated Recovery Testing

**Test Recovery Procedures:**
```bash
#!/bin/bash
# test-recovery.sh

set -e

TEST_DIR="/tmp/recovery_test"
ORIGINAL_DB="/app/data/digest_history.db"
TEST_BACKUP="/backups/test_recovery_backup.db"

echo "Starting recovery procedure test..."

# Create test backup
echo "Creating test backup..."
sqlite3 "$ORIGINAL_DB" ".backup $TEST_BACKUP"

# Create test environment
mkdir -p "$TEST_DIR/data"
cp "$TEST_BACKUP" "$TEST_DIR/data/digest_history.db"

# Test database integrity
echo "Testing database integrity..."
if sqlite3 "$TEST_DIR/data/digest_history.db" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database integrity test passed"
else
    echo "❌ Database integrity test failed"
    exit 1
fi

# Test data retrieval
echo "Testing data retrieval..."
ARTICLE_COUNT=$(sqlite3 "$TEST_DIR/data/digest_history.db" "SELECT COUNT(*) FROM articles;")
USER_COUNT=$(sqlite3 "$TEST_DIR/data/digest_history.db" "SELECT COUNT(*) FROM users;")

echo "Articles found: $ARTICLE_COUNT"
echo "Users found: $USER_COUNT"

if [ "$ARTICLE_COUNT" -gt 0 ] && [ "$USER_COUNT" -gt 0 ]; then
    echo "✅ Data retrieval test passed"
else
    echo "❌ Data retrieval test failed - no data found"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"
rm "$TEST_BACKUP"

echo "✅ All recovery tests passed"
```

### Disaster Recovery Simulation

**Full Disaster Recovery Test:**
```bash
#!/bin/bash
# disaster-recovery-test.sh

set -e

echo "🚨 Starting Disaster Recovery Simulation"
echo "This will test the complete recovery process"

# Step 1: Create current state backup
echo "Step 1: Creating baseline backup..."
./backup-database.sh
./backup-config.sh

# Step 2: Simulate data loss
echo "Step 2: Simulating catastrophic failure..."
docker-compose down
sudo mv /app/data/digest_history.db /app/data/digest_history.db.disaster_test
sudo mv /app/config.json /app/config.json.disaster_test

# Step 3: Restore from backup
echo "Step 3: Restoring from latest backup..."
LATEST_BACKUP=$(ls -t /backups/manual/digest_history_backup_*.db.gz | head -1)
./restore-manual-backup.sh "$LATEST_BACKUP"

# Step 4: Restore configuration
LATEST_CONFIG=$(ls -t /backups/config/config_backup_*.tar.gz | head -1)
./restore-config.sh "$LATEST_CONFIG"

# Step 5: Verify recovery
echo "Step 5: Verifying complete recovery..."
sleep 30  # Wait for services to stabilize

if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Disaster recovery test PASSED"
    
    # Restore original files (this was just a test)
    docker-compose down
    sudo mv /app/data/digest_history.db.disaster_test /app/data/digest_history.db
    sudo mv /app/config.json.disaster_test /app/config.json
    docker-compose up -d
    
    echo "✅ Original system state restored"
else
    echo "❌ Disaster recovery test FAILED"
    
    # Emergency restore
    sudo mv /app/data/digest_history.db.disaster_test /app/data/digest_history.db
    sudo mv /app/config.json.disaster_test /app/config.json
    docker-compose up -d
    
    exit 1
fi
```

## 📊 Backup Monitoring

### Backup Health Monitoring

**Monitor Backup Systems:**
```bash
#!/bin/bash
# monitor-backups.sh

ALERT_EMAIL="admin@yourdomain.com"
BACKUP_DIR="/backups"
MAX_AGE_HOURS=25  # Alert if no backup in 25 hours

echo "Monitoring backup health..."

# Check Litestream health
if docker ps | grep -q daily-scribe-litestream; then
    echo "✅ Litestream container running"
else
    echo "❌ Litestream container not running" | mail -s "Backup Alert: Litestream Down" "$ALERT_EMAIL"
fi

# Check recent backups
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "daily_scribe_backup_*.tar.gz" -mmin -$(($MAX_AGE_HOURS * 60)) | wc -l)
if [ "$LATEST_BACKUP" -gt 0 ]; then
    echo "✅ Recent backup found"
else
    echo "❌ No recent backups found" | mail -s "Backup Alert: No Recent Backups" "$ALERT_EMAIL"
fi

# Check backup storage space
BACKUP_USAGE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$BACKUP_USAGE" -lt 90 ]; then
    echo "✅ Backup storage usage: ${BACKUP_USAGE}%"
else
    echo "❌ Backup storage critically low: ${BACKUP_USAGE}%" | mail -s "Backup Alert: Low Storage" "$ALERT_EMAIL"
fi

# Check cloud backup (if using GCS)
if command -v gsutil > /dev/null; then
    CLOUD_BACKUPS=$(gsutil ls gs://your-daily-scribe-backups/database/ | wc -l)
    echo "Cloud backups found: $CLOUD_BACKUPS"
fi
```

### Backup Metrics

**Collect Backup Metrics:**
```bash
#!/bin/bash
# backup-metrics.sh

METRICS_FILE="/var/log/backup-metrics.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Database size
DB_SIZE=$(stat -c%s /app/data/digest_history.db)

# Backup directory size
BACKUP_SIZE=$(du -sb /backups | cut -f1)

# Number of backups
BACKUP_COUNT=$(find /backups -name "daily_scribe_backup_*.tar.gz" | wc -l)

# Latest backup age
LATEST_BACKUP=$(find /backups -name "daily_scribe_backup_*.tar.gz" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f1)
CURRENT_TIME=$(date +%s)
BACKUP_AGE=$((CURRENT_TIME - ${LATEST_BACKUP%.*}))

# Log metrics
{
    echo "$TIMESTAMP,database_size,$DB_SIZE"
    echo "$TIMESTAMP,backup_directory_size,$BACKUP_SIZE"
    echo "$TIMESTAMP,backup_count,$BACKUP_COUNT"
    echo "$TIMESTAMP,latest_backup_age_seconds,$BACKUP_AGE"
} >> "$METRICS_FILE"
```

## 📋 Backup Schedule

### Automated Backup Cron Jobs

**Configure Backup Schedule:**
```bash
# Add to crontab (crontab -e)

# Daily full backup at 2 AM
0 2 * * * /usr/local/bin/automated-backup.sh >> /var/log/backup.log 2>&1

# Database backup every 6 hours
0 */6 * * * /usr/local/bin/backup-database.sh >> /var/log/backup.log 2>&1

# Configuration backup before any changes (manual trigger)
# Weekly backup verification
0 3 * * 0 /usr/local/bin/test-recovery.sh >> /var/log/backup-test.log 2>&1

# Backup monitoring every hour
0 * * * * /usr/local/bin/monitor-backups.sh

# Backup metrics collection every 15 minutes
*/15 * * * * /usr/local/bin/backup-metrics.sh
```

### Backup Retention Policy

**Retention Schedule:**
- **Hourly database snapshots:** 24 hours (via Litestream)
- **Daily full backups:** 30 days
- **Weekly backups:** 12 weeks
- **Monthly backups:** 12 months
- **Yearly backups:** 5 years (configuration only)

**Cleanup Script:**
```bash
#!/bin/bash
# cleanup-old-backups.sh

BACKUP_ROOT="/backups"

# Clean up daily backups older than 30 days
find "$BACKUP_ROOT" -name "daily_scribe_backup_*.tar.gz" -mtime +30 -delete

# Clean up manual database backups older than 7 days
find "$BACKUP_ROOT/manual" -name "digest_history_backup_*.db.gz" -mtime +7 -delete

# Clean up configuration backups older than 60 days
find "$BACKUP_ROOT/config" -name "config_backup_*.tar.gz" -mtime +60 -delete

echo "Backup cleanup completed"
```

---

**Recovery Time Objectives:**
- **Database Recovery:** 15 minutes
- **Configuration Recovery:** 5 minutes
- **Full System Recovery:** 1 hour
- **Disaster Recovery:** 4 hours

**Last Updated:** September 7, 2025  
**Next Review:** December 7, 2025
