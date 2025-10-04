#!/bin/bash

# Daily Scribe Utility Script
# Shifts all article timestamps (published_at and processed_at) into the future
# by a configurable number of days (defaults to +1 day).

set -euo pipefail

# ------------------------------------------------------------
# Styling helpers
# ------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_usage() {
    cat <<'EOF'
Daily Scribe - Advance Article Timestamps
========================================
Shift every article's published_at and processed_at forward in time.

Usage:
  advance-articles-timestamps.sh [options]

Options:
  --db-path <path>   Override path to SQLite database (default: from .env or ./data/digest_history.db)
  --days <n>         Number of days to shift forward (default: 1)
  --dry-run          Show what would change without committing updates
  --no-backup        Skip creating a safety copy of the database before updating
  --force            Skip confirmation prompt
  --help             Show this message
EOF
}

# ------------------------------------------------------------
# Initial setup
# ------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_DB_PATH="$PROJECT_ROOT/data/digest_history.db"
SQLITE_BIN="${SQLITE_BIN:-sqlite3}"

shift_days=1
dry_run=false
skip_backup=false
force_run=false

# Load environment variables if available
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$PROJECT_ROOT/.env"
    set +o allexport
fi

DB_PATH="${DB_PATH:-$DEFAULT_DB_PATH}"
BACKUP_DIR="$PROJECT_ROOT/data/backups"

# ------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db-path)
            if [[ $# -lt 2 ]]; then
                log_error "--db-path requires a value"
                exit 1
            fi
            DB_PATH="$2"
            shift 2
            ;;
        --days)
            if [[ $# -lt 2 ]]; then
                log_error "--days requires a numeric value"
                exit 1
            fi
            if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                log_error "--days must be a non-negative integer"
                exit 1
            fi
            shift_days="$2"
            shift 2
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        --no-backup)
            skip_backup=true
            shift
            ;;
        --force)
            force_run=true
            shift
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo
            print_usage
            exit 1
            ;;
    esac
done

if [ "$shift_days" -eq 0 ]; then
    log_warning "Shift value is 0 days; no changes will be applied."
fi

# ------------------------------------------------------------
# Validations
# ------------------------------------------------------------
if ! command -v "$SQLITE_BIN" >/dev/null 2>&1; then
    log_error "sqlite3 command not found. Install sqlite3 or set SQLITE_BIN to the correct binary."
    exit 1
fi

if [ ! -f "$DB_PATH" ]; then
    log_error "Database not found at: $DB_PATH"
    exit 1
fi

log_info "Using database: $DB_PATH"
log_info "Shift amount: +${shift_days} day(s)"

# Count affected rows beforehand
row_count="$($SQLITE_BIN "$DB_PATH" "SELECT COUNT(*) FROM articles WHERE published_at IS NOT NULL OR processed_at IS NOT NULL;")"

if [[ -z "$row_count" ]]; then
    log_error "Failed to count articles. Aborting."
    exit 1
fi

log_info "Rows eligible for shifting: $row_count"

if [ "$row_count" -eq 0 ]; then
    log_warning "No rows have timestamps to shift."
fi

if [ "$dry_run" = true ]; then
    log_info "Running in DRY RUN mode. No changes will be committed."
fi

# Create backup unless skipped or dry run
backup_path=""
if [ "$dry_run" = false ] && [ "$skip_backup" = false ] && [ -f "$DB_PATH" ]; then
    mkdir -p "$BACKUP_DIR"
    timestamp="$(date +%Y%m%d_%H%M%S)"
    db_filename="$(basename "$DB_PATH")"
    backup_path="$BACKUP_DIR/${db_filename%.db}_pre_shift_${timestamp}.db"
    log_info "Creating database backup at: $backup_path"
    cp "$DB_PATH" "$backup_path"
    log_success "Backup created."
fi

if [ "$force_run" = false ] && [ "$dry_run" = false ]; then
    echo -ne "${YELLOW}Proceed with shifting timestamps?${NC} [y/N]: "
    read -r reply
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        log_warning "Operation cancelled by user."
        if [ -n "$backup_path" ]; then
            log_info "Backup retained at $backup_path"
        fi
        exit 0
    fi
fi

update_sql="UPDATE articles
SET
    published_at = CASE
        WHEN published_at IS NOT NULL THEN datetime(published_at, '+${shift_days} day')
        ELSE published_at
    END,
    processed_at = CASE
        WHEN processed_at IS NOT NULL THEN datetime(processed_at, '+${shift_days} day')
        ELSE processed_at
    END
WHERE published_at IS NOT NULL OR processed_at IS NOT NULL;"

if [ "$dry_run" = true ]; then
    log_info "Preview of update statement:\n$update_sql"
fi

transaction_begin=$([ "$dry_run" = true ] && echo "BEGIN;" || echo "BEGIN IMMEDIATE;")
transaction_end=$([ "$dry_run" = true ] && echo "ROLLBACK;" || echo "COMMIT;")

set +e
result="$($SQLITE_BIN "$DB_PATH" <<SQL
$transaction_begin
$update_sql
SELECT changes();
$transaction_end
SQL
)"
exit_code=$?
set -e

if [ $exit_code -ne 0 ]; then
    log_error "SQLite execution failed."
    if [ -n "$backup_path" ]; then
        log_warning "Original database backup available at $backup_path"
    fi
    exit $exit_code
fi

changes="$(echo "$result" | tail -n1)"

if ! [[ "$changes" =~ ^[0-9]+$ ]]; then
    log_warning "Could not determine number of updated rows. Raw output:" 
    echo "$result"
else
    if [ "$dry_run" = true ]; then
        log_info "[DRY RUN] Rows that would be updated: $changes"
    else
        log_success "Updated rows: $changes"
    fi
fi

if [ -n "$backup_path" ]; then
    log_info "Backup stored at: $backup_path"
fi

if [ "$dry_run" = true ]; then
    log_info "Dry run complete. No changes were committed."
else
    log_success "Timestamp shift operation completed successfully."
fi
