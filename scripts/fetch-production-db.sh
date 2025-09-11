#!/bin/bash

# Daily Scribe Production Database Fetch Script
# Fetches digest_history.db from production and creates a backup of the local database

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVER_USER="matheus"
SERVER_HOST="${SERVER_HOST:-192.168.15.55}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/$SERVER_USER/daily-scribe}"
LOCAL_DATA_DIR="$PROJECT_ROOT/data"
LOCAL_DB_PATH="$LOCAL_DATA_DIR/digest_history.db"
PRODUCTION_DB_PATH="$DEPLOY_PATH/data/digest_history.db"
TODAY_DATE=$(date +%Y%m%d)
BACKUP_NAME="digest_history_backup_$TODAY_DATE.db"
BACKUP_PATH="$LOCAL_DATA_DIR/$BACKUP_NAME"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

print_usage() {
    echo "Daily Scribe Production Database Fetch Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run           Show what would be done without executing"
    echo "  --no-backup         Skip backing up the existing local database"
    echo "  --force             Skip confirmation prompts"
    echo "  --snapshot          Always create a snapshot from running container"
    echo "  --direct            Force direct file copy (skip container snapshot)"
    echo "  --server HOST       Override production server host (default: $SERVER_HOST)"
    echo "  --user USER         Override production server user (default: $SERVER_USER)"
    echo "  --help              Show this help message"
    echo ""
    echo "Description:"
    echo "  This script will:"
    echo "  1. Test SSH connection to production server"
    echo "  2. Backup existing local database (if exists) to digest_history_backup_YYYYMMDD.db"
    echo "  3. Fetch the production database to local data directory"
    echo "  4. Verify the fetched database integrity"
    echo ""
    echo "Database Fetch Methods:"
    echo "  - Default: Check if containers are running and offer snapshot option"
    echo "  - --snapshot: Always create a consistent snapshot from running container"
    echo "  - --direct: Always copy database file directly from host filesystem"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Normal operation with confirmation"
    echo "  $0 --force                           # Skip confirmations"
    echo "  $0 --dry-run                         # Show what would be done"
    echo "  $0 --snapshot                        # Always use container snapshot"
    echo "  $0 --direct                          # Direct file copy only"
    echo "  $0 --no-backup                       # Don't backup existing database"
    echo "  $0 --server 192.168.1.100           # Use different server"
}

# Test SSH connectivity
test_ssh_connection() {
    log_info "Testing SSH connection to $SERVER_USER@$SERVER_HOST..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_HOST" 'echo "SSH connection successful"' 2>/dev/null; then
        log_success "SSH connection established"
        return 0
    else
        log_error "Cannot establish SSH connection to $SERVER_USER@$SERVER_HOST"
        echo "Please ensure:"
        echo "1. SSH key is added to the server: ssh-copy-id $SERVER_USER@$SERVER_HOST"
        echo "2. Server is accessible: ping $SERVER_HOST"
        echo "3. Correct username and hostname are used"
        return 1
    fi
}

# Check if production database exists and is accessible
check_production_database() {
    log_info "Checking production database accessibility..."
    
    if ssh "$SERVER_USER@$SERVER_HOST" "test -f '$PRODUCTION_DB_PATH'"; then
        local db_size=$(ssh "$SERVER_USER@$SERVER_HOST" "stat -c%s '$PRODUCTION_DB_PATH' 2>/dev/null || echo '0'")
        local db_size_mb=$((db_size / 1024 / 1024))
        log_success "Production database found (Size: ${db_size_mb}MB)"
        
        # Check if database is locked by running containers
        local containers_running=$(ssh "$SERVER_USER@$SERVER_HOST" "cd '$DEPLOY_PATH' && docker-compose ps -q app" 2>/dev/null | wc -l)
        
        if [ "$FORCE_DIRECT" == "true" ]; then
            log_info "Using direct file copy (--direct flag specified)"
            return 0
        elif [ "$FORCE_SNAPSHOT" == "true" ]; then
            log_info "Creating database snapshot (--snapshot flag specified)"
            create_production_snapshot
            return $?
        elif [ "$containers_running" -gt 0 ]; then
            log_warning "Docker containers are running on production. Database might be in use."
            log_warning "For best results, consider one of these options:"
            log_warning "  1. Create a database snapshot from container:"
            log_warning "     $0 --snapshot"
            log_warning "  2. Or temporarily stop app container:"
            log_warning "     ssh $SERVER_USER@$SERVER_HOST 'cd $DEPLOY_PATH && docker-compose stop app'"
            log_warning "  3. Or force direct copy (may have issues):"
            log_warning "     $0 --direct"
            
            # Offer to create a snapshot automatically
            if [ "$FORCE" != "true" ] && [ "$DRY_RUN" != "true" ]; then
                echo
                read -p "Create a database snapshot from running container? [Y/n]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Nn]$ ]]; then
                    log_info "Proceeding with direct file copy (may have locking issues)"
                else
                    log_info "Creating database snapshot from container..."
                    create_production_snapshot
                    return $?
                fi
            fi
        fi
        
        return 0
    else
        log_error "Production database not found at: $PRODUCTION_DB_PATH"
        return 1
    fi
}

# Create data directory if it doesn't exist
ensure_data_directory() {
    if [ ! -d "$LOCAL_DATA_DIR" ]; then
        log_info "Creating local data directory: $LOCAL_DATA_DIR"
        mkdir -p "$LOCAL_DATA_DIR"
    fi
}

# Create a database snapshot from the running container
create_production_snapshot() {
    log_info "Creating database snapshot from running container..."
    
    local snapshot_name="production_snapshot_$(date +%Y%m%d_%H%M%S).db"
    local snapshot_path="$DEPLOY_PATH/data/$snapshot_name"
    
    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY RUN] Would create snapshot using container's sqlite3"
        log_info "[DRY RUN] Command: docker-compose exec app sqlite3 /data/digest_history.db \".backup /data/$snapshot_name\""
        
        # Update paths for dry run too
        PRODUCTION_DB_PATH="$snapshot_path"
        export PRODUCTION_DB_PATH
        CLEANUP_SNAPSHOT="$snapshot_path"
        export CLEANUP_SNAPSHOT
        
        return 0
    fi
    
    # Create snapshot using SQLite backup command from within container
    if ssh "$SERVER_USER@$SERVER_HOST" "cd '$DEPLOY_PATH' && docker-compose exec -T app sqlite3 /data/digest_history.db \".backup /data/$snapshot_name\"" 2>/dev/null; then
        log_success "Database snapshot created: $snapshot_name"
        
        # Update the production database path to point to the snapshot
        PRODUCTION_DB_PATH="$snapshot_path"
        export PRODUCTION_DB_PATH
        
        # Schedule cleanup of snapshot after fetch
        CLEANUP_SNAPSHOT="$snapshot_path"
        export CLEANUP_SNAPSHOT
        
        return 0
    else
        log_error "Failed to create database snapshot from container"
        log_warning "Falling back to direct file copy..."
        return 1
    fi
}

# Backup existing local database
backup_existing_database() {
    if [ -f "$LOCAL_DB_PATH" ]; then
        log_info "Backing up existing local database..."
        
        # Check if backup already exists
        if [ -f "$BACKUP_PATH" ]; then
            log_warning "Backup file already exists: $BACKUP_NAME"
            if [ "$FORCE" != "true" ]; then
                read -p "Overwrite existing backup? [y/N]: " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_error "Backup cancelled by user"
                    return 1
                fi
            fi
        fi
        
        if [ "$DRY_RUN" != "true" ]; then
            cp "$LOCAL_DB_PATH" "$BACKUP_PATH"
            local backup_size=$(stat -f%z "$BACKUP_PATH" 2>/dev/null || stat -c%s "$BACKUP_PATH" 2>/dev/null || echo "0")
            local backup_size_mb=$((backup_size / 1024 / 1024))
            log_success "Local database backed up to: $BACKUP_NAME (Size: ${backup_size_mb}MB)"
        else
            log_info "[DRY RUN] Would backup $LOCAL_DB_PATH to $BACKUP_PATH"
        fi
    else
        log_info "No existing local database to backup"
    fi
}

# Fetch database from production
fetch_production_database() {
    log_info "Fetching database from production server..."
    
    # Use rsync for robust file transfer with progress
    local rsync_opts="-avz --progress --stats"
    
    if [ "$DRY_RUN" == "true" ]; then
        rsync_opts="$rsync_opts --dry-run"
        log_info "[DRY RUN] Would fetch: $SERVER_USER@$SERVER_HOST:$PRODUCTION_DB_PATH"
        log_info "[DRY RUN] To: $LOCAL_DB_PATH"
    fi
    
    if rsync $rsync_opts "$SERVER_USER@$SERVER_HOST:$PRODUCTION_DB_PATH" "$LOCAL_DB_PATH"; then
        if [ "$DRY_RUN" != "true" ]; then
            local fetched_size=$(stat -f%z "$LOCAL_DB_PATH" 2>/dev/null || stat -c%s "$LOCAL_DB_PATH" 2>/dev/null || echo "0")
            local fetched_size_mb=$((fetched_size / 1024 / 1024))
            log_success "Database fetched successfully (Size: ${fetched_size_mb}MB)"
        else
            log_info "[DRY RUN] Fetch operation completed successfully"
        fi
        return 0
    else
        log_error "Failed to fetch database from production"
        return 1
    fi
}

# Verify database integrity
verify_database_integrity() {
    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY RUN] Would verify database integrity"
        return 0
    fi
    
    log_info "Verifying database integrity..."
    
    # Check if file exists and is not empty
    if [ ! -f "$LOCAL_DB_PATH" ] || [ ! -s "$LOCAL_DB_PATH" ]; then
        log_error "Database file is missing or empty"
        return 1
    fi
    
    # Try to open database and run a simple query
    if command -v sqlite3 >/dev/null 2>&1; then
        if sqlite3 "$LOCAL_DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_success "Database integrity check passed"
            
            # Show some basic stats
            local table_count=$(sqlite3 "$LOCAL_DB_PATH" "SELECT COUNT(name) FROM sqlite_master WHERE type='table';")
            local digest_count=$(sqlite3 "$LOCAL_DB_PATH" "SELECT COUNT(*) FROM digest_history;" 2>/dev/null || echo "N/A")
            
            log_info "Database statistics:"
            log_info "  Tables: $table_count"
            log_info "  Digest entries: $digest_count"
            
            return 0
        else
            log_error "Database integrity check failed"
            return 1
        fi
    else
        log_warning "sqlite3 not available for integrity check"
        log_warning "Database transferred but integrity not verified"
        return 0
    fi
}

# Show summary of what will be done
show_operation_summary() {
    echo ""
    log_info "Operation Summary:"
    echo "  Production server: $SERVER_USER@$SERVER_HOST"
    echo "  Production DB path: $PRODUCTION_DB_PATH"
    echo "  Local DB path: $LOCAL_DB_PATH"
    
    # Show database fetch method
    if [ "$FORCE_SNAPSHOT" == "true" ]; then
        echo "  Fetch method: Container snapshot (--snapshot)"
    elif [ "$FORCE_DIRECT" == "true" ]; then
        echo "  Fetch method: Direct file copy (--direct)"
    else
        echo "  Fetch method: Auto-detect (container snapshot if running, else direct)"
    fi
    
    if [ "$SKIP_BACKUP" != "true" ] && [ -f "$LOCAL_DB_PATH" ]; then
        echo "  Backup will be created: $BACKUP_NAME"
    fi
    
    if [ "$DRY_RUN" == "true" ]; then
        echo "  Mode: DRY RUN (no changes will be made)"
    fi
    
    echo ""
}

# Main execution function
main() {
    local DRY_RUN=false
    local SKIP_BACKUP=false
    local FORCE=false
    local FORCE_SNAPSHOT=false
    local FORCE_DIRECT=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --no-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --snapshot)
                FORCE_SNAPSHOT=true
                shift
                ;;
            --direct)
                FORCE_DIRECT=true
                shift
                ;;
            --server)
                SERVER_HOST="$2"
                shift 2
                ;;
            --user)
                SERVER_USER="$2"
                shift 2
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Validate conflicting options
    if [ "$FORCE_SNAPSHOT" == "true" ] && [ "$FORCE_DIRECT" == "true" ]; then
        log_error "Cannot use both --snapshot and --direct options"
        exit 1
    fi
    
    # Export variables for use in functions
    export DRY_RUN SKIP_BACKUP FORCE FORCE_SNAPSHOT FORCE_DIRECT
    
    echo "Daily Scribe - Production Database Fetch"
    echo "========================================"
    
    show_operation_summary
    
    # Confirmation prompt
    if [ "$FORCE" != "true" ] && [ "$DRY_RUN" != "true" ]; then
        read -p "Continue with database fetch? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # Execute steps
    test_ssh_connection || exit 1
    check_production_database || exit 1
    ensure_data_directory
    
    if [ "$SKIP_BACKUP" != "true" ]; then
        backup_existing_database || exit 1
    fi
    
    fetch_production_database || exit 1
    verify_database_integrity || exit 1
    
    echo ""
    log_success "Database fetch completed successfully!"
    
    # Clean up production snapshot if one was created
    if [ -n "${CLEANUP_SNAPSHOT:-}" ] && [ "$DRY_RUN" != "true" ]; then
        log_info "Cleaning up production snapshot..."
        ssh "$SERVER_USER@$SERVER_HOST" "rm -f '$CLEANUP_SNAPSHOT'" 2>/dev/null || log_warning "Could not clean up snapshot file"
    fi
    
    if [ "$DRY_RUN" != "true" ]; then
        echo ""
        echo "Next steps:"
        echo "1. Verify the application works with the new database"
        echo "2. If needed, restore from backup: cp $BACKUP_PATH $LOCAL_DB_PATH"
        
        if [ -f "$BACKUP_PATH" ]; then
            echo "3. Clean up backup when no longer needed: rm $BACKUP_PATH"
        fi
    fi
}

# Execute main function with all arguments
main "$@"
