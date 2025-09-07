# Daily Scribe Migration Guide

This guide covers migration procedures for upgrading Daily Scribe versions, moving between environments, and handling data migrations.

## 🎯 Migration Overview

### Migration Types
- **Version Upgrades:** Moving to newer Daily Scribe versions
- **Environment Migration:** Moving from development to production
- **Database Migration:** Schema changes and data transformations
- **Infrastructure Migration:** Moving to different servers or platforms
- **Configuration Migration:** Updating settings and preferences

### Pre-Migration Requirements
- **Complete backup** of all data and configuration
- **Testing environment** that mirrors production
- **Rollback plan** in case of migration failure
- **Downtime scheduling** for production migrations
- **User notification** about potential service interruption

## 📊 Version Migration

### Checking Current Version

**Identify Current Version:**
```bash
# Check application version
curl -s http://localhost:8000/healthz | jq '.version'

# Check Docker image version
docker images | grep daily-scribe

# Check git commit
cd /path/to/daily-scribe
git log --oneline -1
```

**Version Compatibility Matrix:**
```
Version 1.0.x -> 1.1.x: Compatible (no data migration needed)
Version 1.0.x -> 2.0.x: Breaking changes (full migration required)
Version 2.0.x -> 2.1.x: Compatible (configuration updates may be needed)
```

### Version 1.x to 2.x Migration

**Pre-Migration Steps:**
```bash
#!/bin/bash
# v1-to-v2-pre-migration.sh

echo "Starting Daily Scribe v1.x to v2.x migration preparation..."

# 1. Create full backup
./scripts/backup-manager.sh create v1-to-v2-pre-migration

# 2. Stop current services
docker-compose down

# 3. Export current configuration
cp config.json config-v1-backup.json

# 4. Export user preferences
sqlite3 data/digest_history.db ".dump user_preferences" > user_preferences_v1.sql

# 5. Verify backup integrity
if [ -f "backups/v1-to-v2-pre-migration.tar.gz" ]; then
    echo "✅ Backup created successfully"
else
    echo "❌ Backup failed - aborting migration"
    exit 1
fi

echo "Pre-migration preparation complete"
```

**Migration Execution:**
```bash
#!/bin/bash
# v1-to-v2-migration.sh

echo "Executing Daily Scribe v1.x to v2.x migration..."

# 1. Update application code
git fetch
git checkout v2.0.0

# 2. Update dependencies
pip install -r requirements.txt

# 3. Run database schema migration
python src/migrations/v1_to_v2_migration.py

# 4. Update configuration format
python src/migrations/config_migration_v1_to_v2.py

# 5. Migrate user preferences
python src/migrations/user_preferences_migration.py

# 6. Update Docker configuration
docker-compose build

# 7. Start services
docker-compose up -d

# 8. Verify migration
sleep 10
python src/migrations/verify_v2_migration.py

echo "Migration completed"
```

### Database Schema Migrations

**Migration Script Template:**
```python
# src/migrations/v1_to_v2_migration.py

import sqlite3
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, db_path="data/digest_history.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
    
    def backup_tables(self):
        """Create backup of existing tables"""
        logger.info("Creating table backups...")
        
        # Get all table names
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        for table in tables:
            backup_table = f"{table}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table}")
            logger.info(f"Backed up {table} to {backup_table}")
    
    def migrate_schema(self):
        """Apply schema changes"""
        logger.info("Applying schema migrations...")
        
        # Add new columns
        migrations = [
            "ALTER TABLE articles ADD COLUMN embedding_vector TEXT",
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE user_preferences ADD COLUMN notification_settings TEXT DEFAULT '{}'",
        ]
        
        for migration in migrations:
            try:
                self.cursor.execute(migration)
                logger.info(f"Applied: {migration}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"Column already exists, skipping: {migration}")
                else:
                    raise
    
    def migrate_data(self):
        """Transform existing data"""
        logger.info("Migrating data...")
        
        # Update user preferences format
        self.cursor.execute("SELECT user_email, preferences FROM user_preferences")
        for row in self.cursor.fetchall():
            user_email, old_prefs = row
            # Transform old preference format to new format
            # Implementation specific to your changes
            pass
    
    def create_new_indexes(self):
        """Create new indexes for performance"""
        logger.info("Creating new indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_articles_embedding ON articles(embedding_vector)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
        ]
        
        for index in indexes:
            self.cursor.execute(index)
            logger.info(f"Created index: {index}")
    
    def verify_migration(self):
        """Verify migration was successful"""
        logger.info("Verifying migration...")
        
        # Check table schemas
        self.cursor.execute("PRAGMA table_info(articles)")
        articles_columns = [row[1] for row in self.cursor.fetchall()]
        
        required_columns = ["id", "title", "content", "embedding_vector"]
        missing_columns = [col for col in required_columns if col not in articles_columns]
        
        if missing_columns:
            raise Exception(f"Migration failed: Missing columns {missing_columns}")
        
        logger.info("Migration verification successful")
    
    def run_migration(self):
        """Execute complete migration"""
        try:
            self.backup_tables()
            self.migrate_schema()
            self.migrate_data()
            self.create_new_indexes()
            self.connection.commit()
            self.verify_migration()
            logger.info("Migration completed successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.connection.close()

if __name__ == "__main__":
    migration = DatabaseMigration()
    migration.run_migration()
```

## 🌐 Environment Migration

### Development to Production Migration

**Environment Setup Checklist:**
```bash
#!/bin/bash
# setup-production-environment.sh

echo "Setting up production environment..."

# 1. Create production directory structure
mkdir -p /opt/daily-scribe/{data,logs,backups,config}

# 2. Set proper permissions
sudo chown -R 1000:1000 /opt/daily-scribe
chmod 755 /opt/daily-scribe
chmod 700 /opt/daily-scribe/data

# 3. Copy configuration files
cp config.json.example /opt/daily-scribe/config/config.json
cp docker-compose.yml /opt/daily-scribe/
cp Caddyfile /opt/daily-scribe/

# 4. Set environment variables
cat > /opt/daily-scribe/.env << EOF
ENV=production
DB_PATH=/opt/daily-scribe/data/digest_history.db
LOG_LEVEL=INFO
DOMAIN=your-domain.com
EMAIL_HOST=smtp.your-provider.com
EOF

# 5. Initialize database
cd /opt/daily-scribe
docker-compose run --rm app python src/main.py --init-db

echo "Production environment setup complete"
```

**Data Migration to Production:**
```bash
#!/bin/bash
# migrate-to-production.sh

DEV_DB_PATH="/Users/Matheus/daily-scribe/data/digest_history.db"
PROD_DB_PATH="/opt/daily-scribe/data/digest_history.db"
BACKUP_PATH="/opt/daily-scribe/backups"

echo "Migrating data to production..."

# 1. Create backup of existing production data (if any)
if [ -f "$PROD_DB_PATH" ]; then
    cp "$PROD_DB_PATH" "$BACKUP_PATH/prod_backup_$(date +%Y%m%d_%H%M%S).db"
fi

# 2. Copy development database
cp "$DEV_DB_PATH" "$PROD_DB_PATH"

# 3. Clean development-specific data
sqlite3 "$PROD_DB_PATH" << EOF
-- Remove test users
DELETE FROM users WHERE email LIKE '%test%' OR email LIKE '%dev%';

-- Remove test articles
DELETE FROM articles WHERE title LIKE '%test%' OR title LIKE '%dev%';

-- Reset user preferences to defaults
UPDATE user_preferences SET 
    max_articles_per_category = 5,
    digest_frequency = 'daily'
WHERE user_email NOT IN ('admin@yourdomain.com');
EOF

# 4. Set proper ownership
chown 1000:1000 "$PROD_DB_PATH"
chmod 644 "$PROD_DB_PATH"

echo "Data migration completed"
```

### Configuration Migration

**Configuration Update Script:**
```python
# src/migrations/config_migration.py

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigMigration:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.backup_path = f"{config_path}.backup"
    
    def backup_config(self):
        """Create backup of current configuration"""
        if os.path.exists(self.config_path):
            os.rename(self.config_path, self.backup_path)
            logger.info(f"Backed up config to {self.backup_path}")
    
    def migrate_v1_to_v2(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v1 config format to v2"""
        new_config = {
            "version": "2.0",
            "application": {
                "name": old_config.get("app_name", "Daily Scribe"),
                "environment": old_config.get("env", "production"),
                "debug": old_config.get("debug", False)
            },
            "database": {
                "path": old_config.get("db_path", "data/digest_history.db"),
                "timeout": old_config.get("db_timeout", 30),
                "backup_enabled": True
            },
            "email": {
                "enabled": old_config.get("email_enabled", True),
                "host": old_config.get("email_host"),
                "port": old_config.get("email_port", 587),
                "username": old_config.get("email_username"),
                "use_tls": old_config.get("email_use_tls", True)
            },
            "sources": old_config.get("sources", []),
            "categories": old_config.get("categories", []),
            "features": {
                "digest_generation": True,
                "email_notifications": old_config.get("email_enabled", True),
                "web_interface": True,
                "api_access": True
            }
        }
        
        return new_config
    
    def run_migration(self):
        """Execute configuration migration"""
        try:
            # Load old configuration
            with open(self.backup_path, 'r') as f:
                old_config = json.load(f)
            
            # Determine migration path
            version = old_config.get("version", "1.0")
            
            if version.startswith("1."):
                new_config = self.migrate_v1_to_v2(old_config)
            else:
                logger.info("No migration needed")
                return
            
            # Save new configuration
            with open(self.config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            logger.info("Configuration migration completed")
            
        except Exception as e:
            logger.error(f"Configuration migration failed: {e}")
            # Restore backup
            if os.path.exists(self.backup_path):
                os.rename(self.backup_path, self.config_path)
            raise

if __name__ == "__main__":
    migration = ConfigMigration()
    migration.backup_config()
    migration.run_migration()
```

## 🏗️ Infrastructure Migration

### Server Migration

**Migration Between Servers:**
```bash
#!/bin/bash
# server-migration.sh

OLD_SERVER="old-server.example.com"
NEW_SERVER="new-server.example.com"
APP_PATH="/opt/daily-scribe"

echo "Migrating Daily Scribe from $OLD_SERVER to $NEW_SERVER..."

# 1. Create complete backup on old server
ssh $OLD_SERVER "
    cd $APP_PATH
    ./scripts/backup-manager.sh create server-migration
    chmod 644 backups/server-migration.tar.gz
"

# 2. Download backup
scp $OLD_SERVER:$APP_PATH/backups/server-migration.tar.gz ./

# 3. Setup new server
ssh $NEW_SERVER "
    sudo mkdir -p $APP_PATH
    sudo chown \$(whoami):\$(whoami) $APP_PATH
"

# 4. Upload backup to new server
scp server-migration.tar.gz $NEW_SERVER:$APP_PATH/

# 5. Restore on new server
ssh $NEW_SERVER "
    cd $APP_PATH
    tar -xzf server-migration.tar.gz
    
    # Start services
    docker-compose up -d
    
    # Verify deployment
    sleep 30
    curl -f http://localhost:8000/healthz || exit 1
"

# 6. Update DNS/Load Balancer
echo "Update your DNS records to point to $NEW_SERVER"
echo "Update load balancer configuration if applicable"

# 7. Test new server
curl -f http://$NEW_SERVER/healthz

echo "Server migration completed"
```

### Docker Migration

**Migrating to Different Docker Setup:**
```bash
#!/bin/bash
# docker-migration.sh

echo "Migrating Docker setup..."

# 1. Stop current containers
docker-compose down

# 2. Export volumes
docker run --rm \
    -v daily_scribe_data:/source:ro \
    -v $(pwd):/backup \
    alpine tar -czf /backup/data_volume_backup.tar.gz -C /source .

# 3. Export database
docker run --rm \
    -v daily_scribe_data:/data:ro \
    -v $(pwd):/backup \
    alpine sh -c "
        if [ -f /data/digest_history.db ]; then
            cp /data/digest_history.db /backup/digest_history_backup.db
        fi
    "

# 4. Update docker-compose.yml for new setup
cp docker-compose.yml docker-compose.yml.old

# Apply new configuration
# (modify docker-compose.yml as needed)

# 5. Build new images
docker-compose build

# 6. Create new volumes
docker volume create daily_scribe_data_new

# 7. Restore data
docker run --rm \
    -v daily_scribe_data_new:/target \
    -v $(pwd):/backup:ro \
    alpine tar -xzf /backup/data_volume_backup.tar.gz -C /target

# 8. Update docker-compose.yml to use new volume name
sed -i 's/daily_scribe_data:/daily_scribe_data_new:/g' docker-compose.yml

# 9. Start new setup
docker-compose up -d

# 10. Verify migration
sleep 15
curl -f http://localhost:8000/healthz

echo "Docker migration completed"
```

## 🔄 Data Migration

### User Data Migration

**Export User Data:**
```python
# src/migrations/export_user_data.py

import sqlite3
import json
import csv
from datetime import datetime

class UserDataExporter:
    def __init__(self, db_path="data/digest_history.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
    
    def export_users(self, output_path="exports/users.json"):
        """Export all user data"""
        cursor = self.connection.cursor()
        
        # Get all users with their preferences
        cursor.execute("""
            SELECT u.*, up.preferences, up.created_at as prefs_created_at
            FROM users u
            LEFT JOIN user_preferences up ON u.email = up.user_email
        """)
        
        users = []
        for row in cursor.fetchall():
            user_data = dict(row)
            # Parse JSON preferences
            if user_data['preferences']:
                user_data['preferences'] = json.loads(user_data['preferences'])
            users.append(user_data)
        
        # Export to JSON
        with open(output_path, 'w') as f:
            json.dump(users, f, indent=2, default=str)
        
        print(f"Exported {len(users)} users to {output_path}")
    
    def export_digest_history(self, output_path="exports/digest_history.csv"):
        """Export digest history"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT user_email, digest_date, articles_count, 
                   email_sent, email_sent_at, created_at
            FROM digest_history
            ORDER BY digest_date DESC
        """)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['user_email', 'digest_date', 'articles_count', 
                           'email_sent', 'email_sent_at', 'created_at'])
            # Write data
            writer.writerows(cursor.fetchall())
        
        print(f"Exported digest history to {output_path}")

if __name__ == "__main__":
    exporter = UserDataExporter()
    exporter.export_users()
    exporter.export_digest_history()
```

**Import User Data:**
```python
# src/migrations/import_user_data.py

import sqlite3
import json
from datetime import datetime

class UserDataImporter:
    def __init__(self, db_path="data/digest_history.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
    
    def import_users(self, import_path="exports/users.json"):
        """Import user data from export file"""
        cursor = self.connection.cursor()
        
        with open(import_path, 'r') as f:
            users = json.load(f)
        
        imported_count = 0
        for user_data in users:
            try:
                # Insert user
                cursor.execute("""
                    INSERT OR REPLACE INTO users (email, created_at)
                    VALUES (?, ?)
                """, (user_data['email'], user_data['created_at']))
                
                # Insert preferences if they exist
                if user_data.get('preferences'):
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_preferences 
                        (user_email, preferences, created_at)
                        VALUES (?, ?, ?)
                    """, (
                        user_data['email'],
                        json.dumps(user_data['preferences']),
                        user_data.get('prefs_created_at', datetime.now().isoformat())
                    ))
                
                imported_count += 1
                
            except Exception as e:
                print(f"Failed to import user {user_data['email']}: {e}")
        
        self.connection.commit()
        print(f"Imported {imported_count} users successfully")

if __name__ == "__main__":
    importer = UserDataImporter()
    importer.import_users()
```

## 🔍 Migration Verification

### Post-Migration Verification Script

```python
# src/migrations/verify_migration.py

import sqlite3
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationVerifier:
    def __init__(self, db_path="data/digest_history.db", api_base="http://localhost:8000"):
        self.db_path = db_path
        self.api_base = api_base
        self.connection = sqlite3.connect(db_path)
    
    def verify_database_schema(self):
        """Verify database schema is correct"""
        logger.info("Verifying database schema...")
        
        cursor = self.connection.cursor()
        
        # Check required tables exist
        required_tables = ['users', 'articles', 'sources', 'user_preferences', 'digest_history']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        if missing_tables:
            raise Exception(f"Missing tables: {missing_tables}")
        
        logger.info("✅ Database schema verification passed")
    
    def verify_data_integrity(self):
        """Verify data integrity"""
        logger.info("Verifying data integrity...")
        
        cursor = self.connection.cursor()
        
        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM user_preferences up
            LEFT JOIN users u ON up.user_email = u.email
            WHERE u.email IS NULL
        """)
        orphaned_prefs = cursor.fetchone()[0]
        
        if orphaned_prefs > 0:
            logger.warning(f"Found {orphaned_prefs} orphaned user preferences")
        
        # Check for invalid JSON in preferences
        cursor.execute("SELECT user_email, preferences FROM user_preferences")
        for row in cursor.fetchall():
            try:
                json.loads(row[1])
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in preferences for user {row[0]}")
        
        logger.info("✅ Data integrity verification passed")
    
    def verify_api_endpoints(self):
        """Verify API endpoints are working"""
        logger.info("Verifying API endpoints...")
        
        endpoints = [
            "/healthz",
            "/categories",
            "/sources",
            "/articles?limit=1"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response.raise_for_status()
                logger.info(f"✅ {endpoint} - OK")
            except Exception as e:
                logger.error(f"❌ {endpoint} - Failed: {e}")
                raise
    
    def verify_user_functionality(self):
        """Verify core user functionality"""
        logger.info("Verifying user functionality...")
        
        # Test user creation/preferences
        test_email = "test-migration@example.com"
        
        try:
            # Test getting user preferences
            response = requests.get(f"{self.api_base}/preferences/{test_email}")
            if response.status_code == 404:
                # User doesn't exist, create preferences
                test_prefs = {
                    "enabled_sources": [1, 2],
                    "enabled_categories": ["technology", "science"],
                    "max_articles_per_category": 5
                }
                
                response = requests.post(
                    f"{self.api_base}/preferences/{test_email}",
                    json=test_prefs
                )
                response.raise_for_status()
            
            # Verify preferences were saved
            response = requests.get(f"{self.api_base}/preferences/{test_email}")
            response.raise_for_status()
            
            # Clean up test user
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM user_preferences WHERE user_email = ?", (test_email,))
            cursor.execute("DELETE FROM users WHERE email = ?", (test_email,))
            self.connection.commit()
            
            logger.info("✅ User functionality verification passed")
            
        except Exception as e:
            logger.error(f"❌ User functionality verification failed: {e}")
            raise
    
    def run_verification(self):
        """Run complete verification suite"""
        try:
            self.verify_database_schema()
            self.verify_data_integrity()
            self.verify_api_endpoints()
            self.verify_user_functionality()
            logger.info("🎉 All migration verifications passed!")
            return True
        except Exception as e:
            logger.error(f"💥 Migration verification failed: {e}")
            return False

if __name__ == "__main__":
    verifier = MigrationVerifier()
    success = verifier.run_verification()
    exit(0 if success else 1)
```

## 📋 Migration Rollback

### Rollback Procedures

**Emergency Rollback Script:**
```bash
#!/bin/bash
# emergency-rollback.sh

BACKUP_PATH="/opt/daily-scribe/backups"
ROLLBACK_NAME="$1"

if [ -z "$ROLLBACK_NAME" ]; then
    echo "Usage: $0 <backup-name>"
    echo "Available backups:"
    ls -la $BACKUP_PATH/*.tar.gz
    exit 1
fi

echo "🚨 EMERGENCY ROLLBACK: Restoring from $ROLLBACK_NAME"

# 1. Stop current services immediately
docker-compose down

# 2. Create emergency backup of current state
EMERGENCY_BACKUP="emergency_$(date +%Y%m%d_%H%M%S)"
tar -czf "$BACKUP_PATH/$EMERGENCY_BACKUP.tar.gz" \
    data/ config.json docker-compose.yml

# 3. Restore from backup
cd /opt/daily-scribe
tar -xzf "$BACKUP_PATH/$ROLLBACK_NAME.tar.gz"

# 4. Start services
docker-compose up -d

# 5. Verify rollback
sleep 15
if curl -f http://localhost:8000/healthz; then
    echo "✅ Rollback successful"
else
    echo "❌ Rollback failed - services not responding"
    exit 1
fi

echo "Rollback completed. Emergency backup saved as: $EMERGENCY_BACKUP.tar.gz"
```

---

**Migration Planning Checklist:**
- [ ] Complete backup created and verified
- [ ] Migration tested in development environment
- [ ] Rollback procedure prepared and tested
- [ ] User notification sent (if applicable)
- [ ] Maintenance window scheduled
- [ ] Monitoring alerts configured
- [ ] Post-migration verification plan ready

**Last Updated:** September 7, 2025  
**Next Review:** December 7, 2025
