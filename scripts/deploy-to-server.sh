#!/bin/bash

# Daily Scribe Server Deployment Script
# Automates deployment to production server

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
MONITORING_ENABLED=true
SKIP_FIREWALL=true
SKIP_DOCKER_INSTALL=true

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

# Check server requirements
check_server_requirements() {
    log_info "Checking server requirements..."
    
    # Check OS
    OS_INFO=$(ssh "$SERVER_USER@$SERVER_HOST" 'cat /etc/os-release | grep "^ID\|^VERSION_ID"' || echo "")
    log_info "Server OS: $OS_INFO"
    
    # Check memory
    MEMORY_GB=$(ssh "$SERVER_USER@$SERVER_HOST" "free -g | grep '^Mem:' | awk '{print \$2}'" || echo "0")
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_warning "Server has less than 2GB RAM ($MEMORY_GB GB). Consider upgrading for better performance."
    else
        log_success "Memory: ${MEMORY_GB}GB"
    fi
    
    # Check disk space
    DISK_SPACE=$(ssh "$SERVER_USER@$SERVER_HOST" "df -h / | tail -1 | awk '{print \$4}'" || echo "0")
    log_info "Available disk space: $DISK_SPACE"
    
    # Check if user has sudo access
    if ssh "$SERVER_USER@$SERVER_HOST" 'sudo -n true' 2>/dev/null; then
        log_success "User has sudo access"
    else
        log_warning "User may not have passwordless sudo access. Some installation steps may require manual password entry."
    fi
}

# Install Docker and Docker Compose
install_docker() {
    if [[ "$SKIP_DOCKER_INSTALL" == true ]]; then
        log_info "Skipping Docker installation as requested"
        return 0
    fi
    
    log_info "Installing Docker and Docker Compose on server..."
    
    ssh "$SERVER_USER@$SERVER_HOST" 'bash -s' << 'EOF'
        # Check if Docker is already installed
        if command -v docker &> /dev/null; then
            echo "Docker is already installed"
            docker --version
        else
            echo "Installing Docker..."
            
            # Update package list
            sudo apt update
            
            # Install prerequisites
            sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # Add Docker GPG key
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Add Docker repository
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io
            
            # Add user to docker group
            sudo usermod -aG docker $USER
            
            echo "Docker installation completed"
        fi
        
        # Check if Docker Compose is installed
        if command -v docker-compose &> /dev/null; then
            echo "Docker Compose is already installed"
            docker-compose --version
        else
            echo "Installing Docker Compose..."
            
            # Download Docker Compose
            sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            
            # Make it executable
            sudo chmod +x /usr/local/bin/docker-compose
            
            echo "Docker Compose installation completed"
        fi
        
        # Start and enable Docker service
        sudo systemctl start docker
        sudo systemctl enable docker
EOF

    log_success "Docker and Docker Compose installation completed"
}

# Configure firewall
configure_firewall() {
    if [[ "$SKIP_FIREWALL" == true ]]; then
        log_info "Skipping firewall configuration as requested"
        return 0
    fi
    
    log_info "Configuring firewall on server..."
    
    ssh "$SERVER_USER@$SERVER_HOST" 'bash -s' << 'EOF'
        # Check if UFW is installed
        if ! command -v ufw &> /dev/null; then
            echo "Installing UFW..."
            sudo apt update
            sudo apt install -y ufw
        fi
        
        # Reset UFW to defaults
        sudo ufw --force reset
        
        # Set default policies
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        
        # Allow SSH (current connection)
        sudo ufw allow 22/tcp
        
        # Allow HTTP and HTTPS
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        # Allow monitoring ports from local network only
        sudo ufw allow from 192.168.0.0/16 to any port 3000 comment 'Grafana'
        sudo ufw allow from 192.168.0.0/16 to any port 9090 comment 'Prometheus'
        
        # Enable UFW
        echo "y" | sudo ufw enable
        
        # Show status
        sudo ufw status verbose
EOF

    log_success "Firewall configuration completed"
}

# Deploy application files
deploy_application() {
    log_info "Deploying application files to server..."
    
    # Create deployment directory
    ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p '$DEPLOY_PATH'"
    
    # Sync application files (excluding development files)
    log_info "Syncing files to server..."
    rsync -avz --progress \
        --exclude='.git/' \
        --exclude='venv/' \
        --exclude='__pycache__/' \
        --exclude='.pytest_cache/' \
        --exclude='*.pyc' \
        --exclude='dev_data/' \
        --exclude='data/' \
        --exclude='test_*.db*' \
        --exclude='.DS_Store' \
        --exclude='logs/' \
        "$PROJECT_ROOT/" \
        "$SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/"
    
    log_success "Application files deployed"
}

# Setup environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Determine which environment file to use
    ENV_FILE=".env.production"
    ENV_SOURCE="$PROJECT_ROOT/.env.production"
    log_info "Using production environment configuration"
    
    # Copy appropriate environment file
    if [[ -f "$ENV_SOURCE" ]]; then
        log_info "Copying production environment file to server..."
        scp "$ENV_SOURCE" "$SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/.env"
        log_success "Production environment file deployed"
    else
        log_error "Production environment file not found: $ENV_SOURCE"
        log_info "Please create .env.production file with production settings"
        exit 1
    fi
    
    log_info "Environment configuration setup completed"
}

# Create necessary directories and set permissions
setup_directories() {
    log_info "Setting up directories and permissions..."
    
    ssh "$SERVER_USER@$SERVER_HOST" "
        cd '$DEPLOY_PATH'
        
        # Create data directories
        mkdir -p data cache logs
        
        # Set permissions
        chmod 755 data cache logs
        
        # Make scripts executable
        chmod +x scripts/*.sh
        
        # Create Docker network
        docker network create daily-scribe-network 2>/dev/null || echo 'Network already exists'
    "
    
    log_success "Directories and permissions setup completed"
}

# Start services
start_services() {
    log_info "Starting Daily Scribe services..."
    
    # Determine which profiles to use
    local compose_files="-f docker-compose.yml -f docker-compose.elasticsearch.yml"
    local compose_profiles=""

    compose_profiles="--profile admin"
    compose_files+=" -f docker-compose.yml"
    log_info "Starting with development profiles and overrides"
    
    ssh "$SERVER_USER@$SERVER_HOST" "
        cd '$DEPLOY_PATH'
        
        # Pull latest images
        docker-compose $compose_files pull || echo 'Some images need to be built locally'
        
        # Build any containers that need building (app, cron, frontend)
        docker-compose $compose_files build
        
        # Start core services
        docker-compose $compose_files up -d
        
        # Start profile-specific services
        docker-compose $compose_files $compose_profiles up -d
        
        # Wait for services to start
        echo 'Waiting for services to start...'
        sleep 15
        
        # Show service status
        docker-compose $compose_files ps
    "
    
    log_success "Services started successfully"
}

# Setup monitoring
setup_monitoring() {
    if [[ "$MONITORING_ENABLED" != true ]]; then
        log_info "Skipping monitoring setup as requested"
        return 0
    fi
    
    log_info "Setting up monitoring services..."
    
    ssh "$SERVER_USER@$SERVER_HOST" "
        cd '$DEPLOY_PATH'
        
        # Setup monitoring configuration
        ./scripts/setup-monitoring.sh --all
        
        # Start monitoring services
        docker-compose -f docker-compose.monitoring.yml up -d
        
        # Wait for monitoring services
        echo 'Waiting for monitoring services to start...'
        sleep 10
        
        # Show monitoring service status
        docker-compose -f docker-compose.monitoring.yml ps
    "
    
    log_success "Monitoring services started"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    ssh "$SERVER_USER@$SERVER_HOST" "
        cd '$DEPLOY_PATH'
        
        # Test application health
        echo 'Testing application health...'
        timeout 30 bash -c 'until curl -sf http://localhost:8000/healthz; do sleep 2; done' || echo 'Health check timed out'
        
        # Test metrics endpoint
        echo 'Testing metrics endpoint...'
        curl -sf http://localhost:8000/metrics | head -5 || echo 'Metrics endpoint not available'
        
        # Show running containers
        echo 'Running containers:'
        docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
        
        # Test monitoring (if enabled)
        if [[ -f docker-compose.monitoring.yml ]] && docker-compose -f docker-compose.monitoring.yml ps | grep -q 'Up'; then
            echo 'Testing monitoring services...'
            curl -sf http://localhost:9090/-/healthy || echo 'Prometheus not healthy'
            curl -sf http://localhost:3000/api/health || echo 'Grafana not healthy'
        fi
    "
    
    log_success "Deployment validation completed"
}

# Show deployment summary
show_summary() {
    echo ""
    echo "================================================================"
    echo "         Daily Scribe Deployment Summary"
    echo "================================================================"
    echo "Server: $SERVER_USER@$SERVER_HOST"
    echo "Deploy Path: $DEPLOY_PATH"
    echo "Monitoring Enabled: $MONITORING_ENABLED"
    echo ""
    echo "Next Steps:"
    echo "1. Configure environment variables:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $DEPLOY_PATH && nano .env'"
    echo ""
    echo "2. Configure router port forwarding (ports 80, 443 -> $SERVER_HOST)"
    echo ""
    echo "3. Test external access:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $DEPLOY_PATH && ./scripts/validate-port-forwarding.sh'"
    echo ""
    echo "4. Access services:"
    echo "   - Frontend: http://$SERVER_HOST/ (via Caddy proxy)"
    echo "   - Application: http://$SERVER_HOST:8000 (direct API access)"
    echo "   - CloudBeaver: http://$SERVER_HOST:8080 (cbadmin)"
    echo "   - Kibana: http://$SERVER_HOST:5601 (admin/admin)"
    echo "   - Elasticsearch: http://$SERVER_HOST:9200"
    if [[ "$MONITORING_ENABLED" == true ]]; then
        echo "   - Grafana: http://$SERVER_HOST:3000 (admin/admin)"
        echo "   - Prometheus: http://$SERVER_HOST:9092"
    fi
    echo ""
    echo "5. Monitor logs:"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $DEPLOY_PATH && docker-compose logs -f'"
    echo ""
    echo "For detailed configuration, see: docs/server-deployment-guide.md"
}

# Show usage information
show_usage() {
    cat << EOF
Daily Scribe Server Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    --server HOST          Server hostname or IP (default: $SERVER_HOST)
    --user USER           SSH username (default: $SERVER_USER)
    --path PATH           Deployment path (default: $DEPLOY_PATH)
    --no-monitoring       Skip monitoring setup
    -h, --help           Show this help message

EXAMPLES:
    $0                                          # Deploy with defaults
    $0 --server 192.168.1.100 --user admin     # Custom server and user
    $0 --no-monitoring                          # Skip monitoring setup

ENVIRONMENT VARIABLES:
    SERVER_HOST           Target server hostname/IP
    SERVER_USER           SSH username
    DEPLOY_PATH           Deployment directory path

PREREQUISITES:
    - SSH key access to target server
    - Server running Ubuntu/Debian
    - User with sudo privileges
    - rsync installed locally

This script automates the deployment of Daily Scribe to a production server.

EOF
}

# Main deployment function
main() {
    echo "Daily Scribe Server Deployment"
    echo "=============================="
    echo ""
    
    # Test SSH connection
    if ! test_ssh_connection; then
        exit 1
    fi
    
    # Check server requirements
    check_server_requirements
    
    # Install Docker and Docker Compose
    install_docker
    
    # Configure firewall
    configure_firewall
    
    # Deploy application files
    deploy_application
    
    # Setup environment
    setup_environment
    
    # Setup directories and permissions
    setup_directories
    
    # Start core services
    start_services
    
    # Setup monitoring
    setup_monitoring
    
    # Validate deployment
    validate_deployment
    
    # Show summary
    show_summary
    
    log_success "Deployment completed successfully!"
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
        --no-monitoring)
            MONITORING_ENABLED=false
            shift
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
