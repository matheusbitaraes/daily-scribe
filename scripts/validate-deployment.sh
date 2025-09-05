#!/bin/bash

# Daily Scribe Deployment Validation Script
# Comprehensive validation of server deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0
TEST_RESULTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
    ((TESTS_WARNING++))
}

# Add test result for reporting
add_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    TEST_RESULTS+=("$test_name|$status|$details")
}

# Test if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Test HTTP endpoint
test_http_endpoint() {
    local url="$1"
    local expected_codes="${2:-200}"
    local timeout="${3:-10}"
    
    local response_code=""
    if command_exists curl; then
        response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null || echo "000")
    else
        log_warning "curl not available for HTTP testing"
        return 1
    fi
    
    if [[ "$expected_codes" == *"$response_code"* ]]; then
        echo "$response_code"
        return 0
    else
        echo "$response_code"
        return 1
    fi
}

# Test system requirements
test_system_requirements() {
    log_info "Testing system requirements..."
    
    # Check OS
    echo -n "Operating System: "
    if [[ -f /etc/os-release ]]; then
        local os_info
        os_info=$(grep "PRETTY_NAME" /etc/os-release | cut -d'"' -f2)
        log_success "$os_info"
        add_result "Operating System" "PASS" "$os_info"
    else
        log_warning "Cannot determine OS version"
        add_result "Operating System" "WARN" "Unknown OS"
    fi
    
    # Check memory
    echo -n "Memory: "
    local memory_gb
    memory_gb=$(free -g | grep '^Mem:' | awk '{print $2}')
    if [[ $memory_gb -ge 2 ]]; then
        log_success "${memory_gb}GB available"
        add_result "Memory" "PASS" "${memory_gb}GB"
    else
        log_warning "${memory_gb}GB available (minimum 2GB recommended)"
        add_result "Memory" "WARN" "${memory_gb}GB - below recommended"
    fi
    
    # Check disk space
    echo -n "Disk space: "
    local disk_usage
    disk_usage=$(df -h . | tail -1 | awk '{print $4 " available (" $5 " used)"}')
    local disk_percent
    disk_percent=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $disk_percent -lt 80 ]]; then
        log_success "$disk_usage"
        add_result "Disk Space" "PASS" "$disk_usage"
    elif [[ $disk_percent -lt 90 ]]; then
        log_warning "$disk_usage"
        add_result "Disk Space" "WARN" "$disk_usage"
    else
        log_error "$disk_usage"
        add_result "Disk Space" "FAIL" "$disk_usage"
    fi
    
    # Check CPU cores
    echo -n "CPU cores: "
    local cpu_cores
    cpu_cores=$(nproc)
    if [[ $cpu_cores -ge 2 ]]; then
        log_success "$cpu_cores cores"
        add_result "CPU Cores" "PASS" "$cpu_cores cores"
    else
        log_warning "$cpu_cores core (2+ recommended)"
        add_result "CPU Cores" "WARN" "$cpu_cores core"
    fi
}

# Test Docker installation
test_docker_installation() {
    log_info "Testing Docker installation..."
    
    # Check Docker
    echo -n "Docker engine: "
    if command_exists docker; then
        local docker_version
        docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_success "Installed ($docker_version)"
        add_result "Docker Engine" "PASS" "$docker_version"
        
        # Test Docker daemon
        echo -n "Docker daemon: "
        if docker info &>/dev/null; then
            log_success "Running"
            add_result "Docker Daemon" "PASS" "Accessible"
        else
            log_error "Not accessible"
            add_result "Docker Daemon" "FAIL" "Cannot access Docker daemon"
        fi
    else
        log_error "Not installed"
        add_result "Docker Engine" "FAIL" "Docker not found"
    fi
    
    # Check Docker Compose
    echo -n "Docker Compose: "
    if command_exists docker-compose; then
        local compose_version
        compose_version=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
        log_success "Installed ($compose_version)"
        add_result "Docker Compose" "PASS" "$compose_version"
    else
        log_error "Not installed"
        add_result "Docker Compose" "FAIL" "Docker Compose not found"
    fi
}

# Test network configuration
test_network_configuration() {
    log_info "Testing network configuration..."
    
    # Test internet connectivity
    echo -n "Internet connectivity: "
    if ping -c 1 -W 5 8.8.8.8 &>/dev/null; then
        log_success "Connected"
        add_result "Internet Connectivity" "PASS" "Can reach external hosts"
    else
        log_error "No connection"
        add_result "Internet Connectivity" "FAIL" "Cannot reach external hosts"
    fi
    
    # Test DNS resolution
    echo -n "DNS resolution: "
    if nslookup google.com &>/dev/null; then
        log_success "Working"
        add_result "DNS Resolution" "PASS" "DNS queries successful"
    else
        log_error "Failed"
        add_result "DNS Resolution" "FAIL" "DNS queries failing"
    fi
    
    # Check firewall status
    echo -n "Firewall status: "
    if command_exists ufw; then
        local ufw_status
        ufw_status=$(sudo ufw status | head -1 | awk '{print $2}')
        if [[ "$ufw_status" == "active" ]]; then
            log_success "Active"
            add_result "Firewall" "PASS" "UFW active"
        else
            log_warning "Inactive"
            add_result "Firewall" "WARN" "UFW not active"
        fi
    else
        log_warning "UFW not installed"
        add_result "Firewall" "WARN" "UFW not available"
    fi
    
    # Check open ports
    echo -n "Required ports: "
    local open_ports=()
    if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
        open_ports+=("80")
    fi
    if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
        open_ports+=("443")
    fi
    if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
        open_ports+=("8000")
    fi
    
    if [[ ${#open_ports[@]} -gt 0 ]]; then
        log_success "Open: ${open_ports[*]}"
        add_result "Required Ports" "PASS" "Ports open: ${open_ports[*]}"
    else
        log_warning "No application ports detected"
        add_result "Required Ports" "WARN" "No ports detected"
    fi
}

# Test application deployment
test_application_deployment() {
    log_info "Testing application deployment..."
    
    # Check deployment directory
    echo -n "Deployment directory: "
    if [[ -f "docker-compose.yml" ]]; then
        log_success "Found"
        add_result "Deployment Files" "PASS" "docker-compose.yml present"
    else
        log_error "Missing docker-compose.yml"
        add_result "Deployment Files" "FAIL" "docker-compose.yml not found"
        return 1
    fi
    
    # Check environment configuration
    echo -n "Environment configuration: "
    if [[ -f ".env" ]]; then
        log_success "Present"
        add_result "Environment Config" "PASS" ".env file exists"
    else
        log_warning "Missing .env file"
        add_result "Environment Config" "WARN" ".env file not found"
    fi
    
    # Check data directories
    echo -n "Data directories: "
    local missing_dirs=()
    for dir in "data" "cache" "logs"; do
        if [[ ! -d "$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#missing_dirs[@]} -eq 0 ]]; then
        log_success "All present"
        add_result "Data Directories" "PASS" "All directories exist"
    else
        log_warning "Missing: ${missing_dirs[*]}"
        add_result "Data Directories" "WARN" "Missing: ${missing_dirs[*]}"
    fi
    
    # Check Docker network
    echo -n "Docker network: "
    if docker network ls | grep -q "daily-scribe-network"; then
        log_success "Created"
        add_result "Docker Network" "PASS" "daily-scribe-network exists"
    else
        log_warning "Missing"
        add_result "Docker Network" "WARN" "daily-scribe-network not found"
    fi
}

# Test running services
test_running_services() {
    log_info "Testing running services..."
    
    # Check if docker-compose.yml exists
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found, skipping service tests"
        return 1
    fi
    
    # Get list of services from docker-compose
    local services
    services=$(docker-compose config --services 2>/dev/null || echo "")
    
    if [[ -z "$services" ]]; then
        log_warning "Cannot read docker-compose configuration"
        add_result "Service Configuration" "WARN" "Cannot parse docker-compose.yml"
        return 1
    fi
    
    # Test each service
    for service in $services; do
        echo -n "Service $service: "
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "Running"
            add_result "Service $service" "PASS" "Container running"
        else
            local status
            status=$(docker-compose ps "$service" | tail -1 | awk '{print $4}' || echo "Unknown")
            log_error "Not running ($status)"
            add_result "Service $service" "FAIL" "Container not running: $status"
        fi
    done
}

# Test application endpoints
test_application_endpoints() {
    log_info "Testing application endpoints..."
    
    # Test health endpoint
    echo -n "Health endpoint: "
    if response=$(test_http_endpoint "http://localhost:8000/healthz" "200" 10); then
        log_success "Accessible (HTTP $response)"
        add_result "Health Endpoint" "PASS" "HTTP $response"
        
        # Test health response format
        echo -n "Health response: "
        if command_exists curl; then
            local health_data
            health_data=$(curl -s http://localhost:8000/healthz 2>/dev/null || echo "{}")
            if echo "$health_data" | grep -q '"status"'; then
                local status
                status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                if [[ "$status" == "healthy" ]]; then
                    log_success "Healthy"
                    add_result "Health Status" "PASS" "Application healthy"
                else
                    log_warning "Status: $status"
                    add_result "Health Status" "WARN" "Status: $status"
                fi
            else
                log_warning "Invalid response format"
                add_result "Health Status" "WARN" "Invalid JSON response"
            fi
        fi
    else
        log_error "Not accessible (HTTP $response)"
        add_result "Health Endpoint" "FAIL" "HTTP $response"
    fi
    
    # Test metrics endpoint
    echo -n "Metrics endpoint: "
    if response=$(test_http_endpoint "http://localhost:8000/metrics" "200" 10); then
        log_success "Accessible (HTTP $response)"
        add_result "Metrics Endpoint" "PASS" "HTTP $response"
    else
        log_warning "Not accessible (HTTP $response)"
        add_result "Metrics Endpoint" "WARN" "HTTP $response"
    fi
    
    # Test main application
    echo -n "Main application: "
    if response=$(test_http_endpoint "http://localhost:8000/" "200 404" 10); then
        log_success "Responding (HTTP $response)"
        add_result "Main Application" "PASS" "HTTP $response"
    else
        log_error "Not responding (HTTP $response)"
        add_result "Main Application" "FAIL" "HTTP $response"
    fi
}

# Test monitoring services
test_monitoring_services() {
    log_info "Testing monitoring services..."
    
    # Check if monitoring is configured
    if [[ ! -f "docker-compose.monitoring.yml" ]]; then
        log_info "Monitoring not configured, skipping monitoring tests"
        add_result "Monitoring Configuration" "INFO" "Not configured"
        return 0
    fi
    
    # Test Prometheus
    echo -n "Prometheus: "
    if response=$(test_http_endpoint "http://localhost:9090/-/healthy" "200" 5); then
        log_success "Running (HTTP $response)"
        add_result "Prometheus" "PASS" "HTTP $response"
    else
        log_warning "Not accessible (HTTP $response)"
        add_result "Prometheus" "WARN" "HTTP $response"
    fi
    
    # Test Grafana
    echo -n "Grafana: "
    if response=$(test_http_endpoint "http://localhost:3000/api/health" "200" 5); then
        log_success "Running (HTTP $response)"
        add_result "Grafana" "PASS" "HTTP $response"
    else
        log_warning "Not accessible (HTTP $response)"
        add_result "Grafana" "WARN" "HTTP $response"
    fi
    
    # Test AlertManager
    echo -n "AlertManager: "
    if response=$(test_http_endpoint "http://localhost:9093/-/healthy" "200" 5); then
        log_success "Running (HTTP $response)"
        add_result "AlertManager" "PASS" "HTTP $response"
    else
        log_warning "Not accessible (HTTP $response)"
        add_result "AlertManager" "WARN" "HTTP $response"
    fi
}

# Test backup configuration
test_backup_configuration() {
    log_info "Testing backup configuration..."
    
    # Check Litestream configuration
    echo -n "Litestream config: "
    if [[ -f "litestream.yml" ]]; then
        log_success "Present"
        add_result "Litestream Config" "PASS" "Configuration file exists"
        
        # Check if Litestream service is running
        echo -n "Litestream service: "
        if docker-compose ps litestream 2>/dev/null | grep -q "Up"; then
            log_success "Running"
            add_result "Litestream Service" "PASS" "Container running"
        else
            log_warning "Not running"
            add_result "Litestream Service" "WARN" "Container not running"
        fi
    else
        log_warning "Missing"
        add_result "Litestream Config" "WARN" "Configuration not found"
    fi
    
    # Check backup scripts
    echo -n "Backup scripts: "
    if [[ -f "scripts/backup-manager.sh" ]] && [[ -x "scripts/backup-manager.sh" ]]; then
        log_success "Present and executable"
        add_result "Backup Scripts" "PASS" "Scripts available"
    else
        log_warning "Missing or not executable"
        add_result "Backup Scripts" "WARN" "Scripts not properly configured"
    fi
}

# Generate deployment report
generate_report() {
    echo ""
    echo "================================================================"
    echo "         Daily Scribe Deployment Validation Report"
    echo "================================================================"
    echo "Validation Date: $(date)"
    echo "Server: $(hostname)"
    echo "IP Address: $(hostname -I | awk '{print $1}')"
    echo "Current Directory: $(pwd)"
    echo ""
    
    echo "Test Summary:"
    echo "============="
    echo "Total tests: $((TESTS_PASSED + TESTS_FAILED + TESTS_WARNING))"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Warnings: $TESTS_WARNING"
    echo ""
    
    echo "Detailed Results:"
    echo "================="
    
    for result in "${TEST_RESULTS[@]}"; do
        IFS='|' read -r test_name status details <<< "$result"
        
        case "$status" in
            "PASS")
                echo -e "${GREEN}✓${NC} $test_name: $details"
                ;;
            "FAIL")
                echo -e "${RED}✗${NC} $test_name: $details"
                ;;
            "WARN")
                echo -e "${YELLOW}⚠${NC} $test_name: $details"
                ;;
            "INFO")
                echo -e "${BLUE}ℹ${NC} $test_name: $details"
                ;;
        esac
    done
    
    echo ""
    echo "Overall Assessment:"
    echo "=================="
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        if [[ $TESTS_WARNING -eq 0 ]]; then
            echo -e "${GREEN}✓ EXCELLENT${NC} - Deployment is ready for production!"
        else
            echo -e "${YELLOW}⚠ GOOD${NC} - Deployment is functional with minor issues to address."
        fi
    elif [[ $TESTS_FAILED -lt 3 ]]; then
        echo -e "${YELLOW}⚠ NEEDS ATTENTION${NC} - Some critical issues need to be resolved."
    else
        echo -e "${RED}✗ CRITICAL ISSUES${NC} - Deployment has significant problems."
    fi
    
    echo ""
    echo "Next Steps:"
    echo "=========="
    
    if [[ $TESTS_FAILED -eq 0 ]] && [[ $TESTS_WARNING -eq 0 ]]; then
        echo "🎉 Your Daily Scribe deployment is ready!"
        echo ""
        echo "1. Configure your domain and DDNS in .env file"
        echo "2. Set up router port forwarding (80, 443 -> $(hostname -I | awk '{print $1}'))"
        echo "3. Test external access: ./scripts/validate-port-forwarding.sh"
        echo "4. Set up external monitoring (UptimeRobot, etc.)"
        echo "5. Schedule regular maintenance"
    else
        echo "🔧 Address the following issues:"
        if [[ $TESTS_FAILED -gt 0 ]]; then
            echo ""
            echo "Critical Issues:"
            for result in "${TEST_RESULTS[@]}"; do
                IFS='|' read -r test_name status details <<< "$result"
                if [[ "$status" == "FAIL" ]]; then
                    case "$test_name" in
                        "Docker Engine")
                            echo "  • Install Docker: curl -fsSL https://get.docker.com | sh"
                            ;;
                        "Docker Compose")
                            echo "  • Install Docker Compose: sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
                            ;;
                        "Service "*|"Health Endpoint")
                            echo "  • Start services: docker-compose up -d"
                            echo "  • Check logs: docker-compose logs"
                            ;;
                        "Deployment Files")
                            echo "  • Ensure you're in the correct directory with docker-compose.yml"
                            ;;
                    esac
                fi
            done
        fi
        
        if [[ $TESTS_WARNING -gt 0 ]]; then
            echo ""
            echo "Recommendations:"
            for result in "${TEST_RESULTS[@]}"; do
                IFS='|' read -r test_name status details <<< "$result"
                if [[ "$status" == "WARN" ]]; then
                    case "$test_name" in
                        "Environment Config")
                            echo "  • Create .env file: cp .env.example .env && nano .env"
                            ;;
                        "Firewall")
                            echo "  • Configure firewall: sudo ufw enable"
                            ;;
                        "Monitoring Configuration")
                            echo "  • Set up monitoring: ./scripts/setup-monitoring.sh --all"
                            ;;
                    esac
                fi
            done
        fi
        
        echo ""
        echo "After addressing issues, run this validation again:"
        echo "./scripts/validate-deployment.sh"
    fi
    
    # Return appropriate exit code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Main function
main() {
    echo "Daily Scribe Deployment Validation"
    echo "=================================="
    echo ""
    
    test_system_requirements
    echo ""
    
    test_docker_installation
    echo ""
    
    test_network_configuration
    echo ""
    
    test_application_deployment
    echo ""
    
    test_running_services
    echo ""
    
    test_application_endpoints
    echo ""
    
    test_monitoring_services
    echo ""
    
    test_backup_configuration
    echo ""
    
    generate_report
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
