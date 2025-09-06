# Production Database Fetch Script

The `fetch-production-db.sh` script allows you to safely fetch the production `digest_history.db` database and store it locally in the `/data` directory.

## Features

- **Safe Operation**: Automatically backs up existing local database before fetching
- **SSH Connection Testing**: Verifies connection to production server before proceeding
- **Database Integrity Verification**: Checks the fetched database for corruption
- **Dry Run Mode**: See what would happen without making changes
- **Progress Monitoring**: Shows transfer progress and file sizes
- **Flexible Options**: Multiple configuration options for different scenarios

## Usage

### Basic Usage
```bash
# Fetch production database with confirmation prompts
./scripts/fetch-production-db.sh

# Skip confirmation prompts
./scripts/fetch-production-db.sh --force

# See what would happen without making changes
./scripts/fetch-production-db.sh --dry-run
```

### Advanced Options
```bash
# Skip backing up existing local database
./scripts/fetch-production-db.sh --no-backup

# Always create a snapshot from running container (recommended)
./scripts/fetch-production-db.sh --snapshot

# Force direct file copy (may have locking issues if containers running)
./scripts/fetch-production-db.sh --direct

# Use different production server
./scripts/fetch-production-db.sh --server 192.168.1.100

# Use different SSH user
./scripts/fetch-production-db.sh --user myuser

# Combine options
./scripts/fetch-production-db.sh --force --snapshot --server 192.168.1.100
```

### Database Fetch Methods

The script supports multiple methods for fetching the database:

1. **Container Snapshot (Recommended)**: Creates a consistent snapshot from the running container using SQLite's `.backup` command
2. **Direct File Copy**: Copies the database file directly from the host filesystem
3. **Auto-detect (Default)**: Checks if containers are running and offers to create a snapshot

#### When to Use Each Method

- **--snapshot**: Always use when production containers are running (ensures data consistency)
- **--direct**: Use when containers are stopped or you need the exact file from disk
- **Default**: Let the script decide based on container status

## What the Script Does

1. **Tests SSH Connection**: Verifies you can connect to the production server
2. **Checks Production Database**: Confirms the database exists and gets its size
3. **Determines Fetch Method**: 
   - If `--snapshot`: Creates a snapshot from running container
   - If `--direct`: Uses direct file copy
   - Default: Checks container status and offers snapshot option
4. **Backs Up Local Database**: Creates `digest_history_backup_YYYYMMDD.db` in `/data` (unless `--no-backup`)
5. **Fetches Production Database**: Uses `rsync` for reliable transfer with progress
6. **Verifies Integrity**: Runs SQLite integrity check on the fetched database
7. **Provides Summary**: Shows database statistics and next steps
8. **Cleanup**: Removes temporary snapshot files (if created)

## Prerequisites

- SSH key-based authentication to production server
- `rsync` installed (usually available by default on macOS/Linux)
- `sqlite3` command-line tool (for integrity verification)

## File Locations

- **Local Database**: `./data/digest_history.db`
- **Backup Location**: `./data/digest_history_backup_YYYYMMDD.db`
- **Production Database**: `/home/matheus/daily-scribe/data/digest_history.db`

## Safety Features

- **Automatic Backups**: Always backs up existing local database (unless `--no-backup`)
- **Confirmation Prompts**: Asks before overwriting (unless `--force`)
- **Dry Run Mode**: Test the operation without making changes
- **Integrity Checks**: Verifies database after transfer
- **Container Detection**: Warns if production containers are running

## Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connection manually
ssh matheus@192.168.15.55

# Add SSH key if needed
ssh-copy-id matheus@192.168.15.55
```

### Database Lock Issues
If production containers are running, you might get a locked database. Stop them temporarily:
```bash
ssh matheus@192.168.15.55 'cd /home/matheus/daily-scribe && docker-compose stop app'
./scripts/fetch-production-db.sh
ssh matheus@192.168.15.55 'cd /home/matheus/daily-scribe && docker-compose start app'
```

### Restore from Backup
If you need to restore the previous local database:
```bash
cp ./data/digest_history_backup_YYYYMMDD.db ./data/digest_history.db
```

## Examples

### Standard Development Workflow
```bash
# 1. Fetch latest production data using snapshot (safest method)
./scripts/fetch-production-db.sh --snapshot --force

# 2. Verify the application works
python src/main.py health-check

# 3. If there are issues, restore backup
cp ./data/digest_history_backup_$(date +%Y%m%d).db ./data/digest_history.db
```

### Testing New Features
```bash
# 1. Get a fresh copy for testing (with snapshot for consistency)
./scripts/fetch-production-db.sh --snapshot --dry-run  # Check what will happen
./scripts/fetch-production-db.sh --snapshot --force    # Get the data

# 2. Test your changes
python src/main.py send-digest --dry-run

# 3. Clean up backup when done
rm ./data/digest_history_backup_*.db
```

### Working with Stopped Containers
```bash
# If you've stopped production containers for maintenance
./scripts/fetch-production-db.sh --direct --force
```
