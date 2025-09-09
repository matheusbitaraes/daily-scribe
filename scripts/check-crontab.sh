#!/bin/bash

# Daily Scribe Crontab Checker
# Checks the cron configuration on a remote server

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_USER="${SERVER_USER:-matheus}"
SERVER_HOST="${SERVER_HOST:-192.168.15.55}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/$SERVER_USER/daily-scribe}"

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

# Show usage information
show_usage() {
    cat << EOF
Daily Scribe Crontab Checker

Usage: $0 [OPTIONS]

OPTIONS:
    --server HOST          Server hostname or IP (default: $SERVER_HOST)
    --user USER           SSH username (default: $SERVER_USER)
    --path PATH           Deployment path (default: $DEPLOY_PATH)
    -h, --help           Show this help message

EXAMPLES:
    $0                                          # Check with defaults
    $0 --server 192.168.1.100 --user admin     # Custom server and user

ENVIRONMENT VARIABLES:
    SERVER_HOST           Target server hostname/IP
    SERVER_USER           SSH username
    DEPLOY_PATH           Deployment directory path

This script checks the cron configuration in the Daily Scribe containers.

EOF
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
        echo "3. SSH service is running on the server"
        return 1
    fi
}

# Check container crontab
check_crontab() {
    log_info "Checking container crontab configuration..."
    
    ssh "$SERVER_USER@$SERVER_HOST" "
        cd '$DEPLOY_PATH'
        
        echo '================================================================'
        echo '                   Daily Scribe Crontab Check'
        echo '================================================================'
        echo ''
        
        # Check if docker-compose file exists
        if [[ ! -f docker-compose.yml ]]; then
            echo 'ERROR: docker-compose.yml not found in $DEPLOY_PATH'
            exit 1
        fi
        
        # Check if cron container is running
        echo 'Container Status:'
        echo '=================='
        if docker-compose ps cron | grep -q 'Up'; then
            echo '✅ Cron container is running'
            CRON_CONTAINER=\$(docker-compose ps -q cron)
            echo \"Container ID: \$CRON_CONTAINER\"
        else
            echo '❌ Cron container is not running'
            echo 'Available containers:'
            docker-compose ps
            echo ''
            echo 'To start the cron container:'
            echo 'docker-compose up -d cron'
            exit 1
        fi
        
        echo ''
        echo 'Crontab Configuration:'
        echo '======================'
        
        # Check user crontab
        echo 'User crontab (crontab -l):'
        docker-compose exec -T cron crontab -l 2>/dev/null || echo 'No user crontab configured'
        
        echo ''
        echo 'System crontab (/etc/crontab):'
        docker-compose exec -T cron cat /etc/crontab 2>/dev/null || echo 'No /etc/crontab file found'
        
        echo ''
        echo 'Cron directories:'
        docker-compose exec -T cron ls -la /etc/cron.d/ 2>/dev/null || echo 'No /etc/cron.d/ directory'
        
        echo ''
        echo 'Cron Process Status:'
        echo '===================='
        docker-compose exec -T cron ps aux | grep -E \"(cron|PID)\" || echo 'Cron process not found'
        
        echo ''
        echo 'Cron Service Status:'
        echo '===================='
        docker-compose exec -T cron service cron status 2>/dev/null || echo 'Cannot check cron service status'
        
        echo ''
        echo 'Environment Variables:'
        echo '======================'
        docker-compose exec -T cron env | grep -E \"(CRON|PATH|HOME|USER)\" | sort || echo 'No relevant environment variables found'
        
        echo ''
        echo 'Recent Cron Container Logs:'
        echo '==========================='
        docker-compose logs --tail=20 cron
        
        echo ''
        echo 'Cron Log Files (inside container):'
        echo '=================================='
        docker-compose exec -T cron find /var/log -name \"*cron*\" -type f 2>/dev/null || echo 'No cron log files found'
        
        echo ''
        echo 'Custom Cron Scripts:'
        echo '===================='
        docker-compose exec -T cron find /app -name \"*.sh\" -type f 2>/dev/null | head -10 || echo 'No script files found'
        
        echo ''
        echo '================================================================'
        echo 'Crontab check completed'
        echo ''
        echo 'Useful commands:'
        echo '  View live logs: docker-compose logs -f cron'
        echo '  Restart cron:   docker-compose restart cron'
        echo '  Enter container: docker-compose exec cron bash'
        echo '================================================================'
    "
    
    log_success "Crontab check completed"
}

# Main function
main() {
    echo "Daily Scribe Crontab Checker"
    echo "============================"
    echo ""
    
    # Test SSH connection
    if ! test_ssh_connection; then
        exit 1
    fi
    
    # Check crontab
    check_crontab
    
    log_success "All checks completed!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --server)
            SERVER_HOST="$2"
            shift 2
            ;;
        --user)
            SERVER_USER="$2"
            shift 2
            ;;
        --path)
            DEPLOY_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage >&2
            exit 1
            ;;
    esac
done

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
