#!/bin/bash
# Litestream Backup Management Script
# Utilities for managing Daily Scribe database backups

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LITESTREAM_CONFIG="./litestream.yml"
DB_PATH="/app/data/digest_history.db"
BACKUP_PREFIX="daily-scribe-db"

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

print_usage() {
    echo "Daily Scribe Litestream Backup Manager"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status      Show backup replication status"
    echo "  snapshots   List available snapshots"
    echo "  restore     Restore database from backup"
    echo "  verify      Verify backup integrity"
    echo "  monitor     Start monitoring mode"
    echo "  help        Show this help message"
    echo ""
    echo "Options:"
    echo "  --date DATE     For restore: specify date (YYYY-MM-DD format)"
    echo "  --output PATH   For restore: specify output file path"
    echo "  --dry-run       For restore: show what would be restored without doing it"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 snapshots"
    echo "  $0 restore --date 2025-09-04"
    echo "  $0 restore --date 2025-09-04 --output ./restored-db.db"
    echo "  $0 verify"
}

check_litestream() {
    if ! command -v litestream &> /dev/null; then
        echo -e "${RED}❌ Litestream not found. Please install Litestream or run from Docker container.${NC}"
        exit 1
    fi
}

check_config() {
    if [ ! -f "$LITESTREAM_CONFIG" ]; then
        echo -e "${RED}❌ Litestream config not found: $LITESTREAM_CONFIG${NC}"
        exit 1
    fi
}

check_environment() {
    if [ -z "$GCS_BUCKET" ]; then
        echo -e "${RED}❌ GCS_BUCKET environment variable not set${NC}"
        exit 1
    fi
}

show_status() {
    echo -e "${BLUE}📊 Litestream Replication Status${NC}"
    echo "=================================="
    
    check_litestream
    check_config
    
    # Check if Litestream is running in Docker
    if docker-compose ps litestream | grep -q "Up"; then
        echo -e "${GREEN}✅ Litestream container is running${NC}"
        
        # Get replication status from container
        echo ""
        echo -e "${YELLOW}📈 Replication Metrics:${NC}"
        docker-compose exec litestream litestream snapshots -config /etc/litestream.yml "${DB_PATH}" || true
        
        echo ""
        echo -e "${YELLOW}🔍 Recent Activity:${NC}"
        docker-compose logs --tail=10 litestream
    else
        echo -e "${RED}❌ Litestream container is not running${NC}"
        echo "Start with: docker-compose up -d litestream"
    fi
}

list_snapshots() {
    echo -e "${BLUE}📸 Available Snapshots${NC}"
    echo "======================"
    
    check_environment
    
    if docker-compose ps litestream | grep -q "Up"; then
        docker-compose exec litestream litestream snapshots -config /etc/litestream.yml "${DB_PATH}"
    else
        echo -e "${YELLOW}⚠️  Litestream container not running. Starting temporarily...${NC}"
        docker-compose run --rm litestream litestream snapshots -config /etc/litestream.yml "${DB_PATH}"
    fi
}

restore_database() {
    local restore_date=""
    local output_path="./restored-database.db"
    local dry_run=false
    
    # Parse restore options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --date)
                restore_date="$2"
                shift 2
                ;;
            --output)
                output_path="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                print_usage
                exit 1
                ;;
        esac
    done
    
    echo -e "${BLUE}🔄 Database Restore${NC}"
    echo "==================="
    
    check_environment
    
    if [ -n "$restore_date" ]; then
        echo "Restore date: $restore_date"
    else
        echo "Restore date: Latest available"
    fi
    echo "Output path: $output_path"
    
    if [ "$dry_run" = true ]; then
        echo -e "${YELLOW}🔍 DRY RUN MODE - No actual restore will be performed${NC}"
    fi
    
    # Confirm before proceeding
    if [ "$dry_run" = false ]; then
        echo ""
        echo -e "${YELLOW}⚠️  This will restore the database from backup.${NC}"
        echo -e "${YELLOW}    Make sure to stop the application first to avoid conflicts.${NC}"
        echo ""
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Restore cancelled."
            exit 0
        fi
    fi
    
    # Build restore command
    restore_cmd="litestream restore -config /etc/litestream.yml"
    if [ -n "$restore_date" ]; then
        restore_cmd="$restore_cmd -timestamp $restore_date"
    fi
    restore_cmd="$restore_cmd -o $output_path $DB_PATH"
    
    if [ "$dry_run" = true ]; then
        echo -e "${BLUE}Would execute:${NC} $restore_cmd"
        return
    fi
    
    echo -e "${BLUE}🔄 Starting restore...${NC}"
    
    # Execute restore
    if docker-compose ps litestream | grep -q "Up"; then
        docker-compose exec litestream bash -c "$restore_cmd"
    else
        docker-compose run --rm litestream bash -c "$restore_cmd"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored successfully to: $output_path${NC}"
        echo -e "${YELLOW}💡 Remember to stop services before replacing the active database${NC}"
    else
        echo -e "${RED}❌ Restore failed${NC}"
        exit 1
    fi
}

verify_backups() {
    echo -e "${BLUE}🔍 Backup Verification${NC}"
    echo "======================"
    
    check_environment
    
    echo "Verifying backup integrity and accessibility..."
    
    # Test restore to a temporary location
    temp_restore="/tmp/verify-restore-$(date +%s).db"
    
    echo "Testing restore to temporary location: $temp_restore"
    
    if docker-compose ps litestream | grep -q "Up"; then
        docker-compose exec litestream litestream restore -config /etc/litestream.yml -o "$temp_restore" "$DB_PATH"
    else
        docker-compose run --rm litestream litestream restore -config /etc/litestream.yml -o "$temp_restore" "$DB_PATH"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup verification successful${NC}"
        echo -e "${GREEN}✅ Backups are accessible and restorable${NC}"
        
        # Clean up temporary file
        rm -f "$temp_restore" 2>/dev/null || true
    else
        echo -e "${RED}❌ Backup verification failed${NC}"
        exit 1
    fi
}

monitor_replication() {
    echo -e "${BLUE}📊 Litestream Monitoring Mode${NC}"
    echo "=============================="
    echo "Press Ctrl+C to exit"
    echo ""
    
    while true; do
        clear
        echo -e "${BLUE}📊 Litestream Status - $(date)${NC}"
        echo "=================================="
        
        if docker-compose ps litestream | grep -q "Up"; then
            echo -e "${GREEN}✅ Litestream container: Running${NC}"
            
            # Show replication lag
            echo ""
            echo -e "${YELLOW}📈 Replication Status:${NC}"
            docker-compose exec litestream litestream snapshots -config /etc/litestream.yml "${DB_PATH}" | tail -5
            
            # Show container health
            echo ""
            echo -e "${YELLOW}💊 Container Health:${NC}"
            docker-compose ps litestream
            
            # Show recent logs
            echo ""
            echo -e "${YELLOW}📝 Recent Logs:${NC}"
            docker-compose logs --tail=5 litestream
        else
            echo -e "${RED}❌ Litestream container: Not running${NC}"
        fi
        
        sleep 30
    done
}

# Main command handling
case "${1:-help}" in
    status)
        show_status
        ;;
    snapshots)
        list_snapshots
        ;;
    restore)
        shift
        restore_database "$@"
        ;;
    verify)
        verify_backups
        ;;
    monitor)
        monitor_replication
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
