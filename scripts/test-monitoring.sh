#!/bin/bash

# Daily Scribe Monitoring Test Script
# Comprehensive testing for monitoring and alerting setup

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
VERBOSE=false

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

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*"
    fi
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

# Test Docker service
test_docker_service() {
    local service_name="$1"
    local container_name="$2"
    
    if command_exists docker; then
        if docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
            return 0
        else
            return 1
        fi
    else
        log_warning "Docker not available"
        return 1
    fi
}

# Test application health endpoint
test_application_health() {
    log_info "Testing application health endpoint..."
    
    echo -n "Health endpoint availability: "
    if response=$(test_http_endpoint "http://localhost:8000/healthz" "200" 10); then
        log_success "Available (HTTP $response)"
        add_result "Health Endpoint" "PASS" "HTTP $response"
        
        # Test health endpoint content
        echo -n "Health endpoint response format: "
        if command_exists curl; then
            local health_response
            health_response=$(curl -s --max-time 10 "http://localhost:8000/healthz" 2>/dev/null || echo "{}")
            
            if echo "$health_response" | grep -q '"status"'; then
                log_success "Valid JSON format"
                add_result "Health Response Format" "PASS" "Valid JSON response"
                
                # Check specific health fields
                echo -n "Health check components: "
                local components=()
                if echo "$health_response" | grep -q '"database"'; then
                    components+=("database")
                fi
                if echo "$health_response" | grep -q '"disk_space"'; then
                    components+=("disk_space")
                fi
                if echo "$health_response" | grep -q '"memory"'; then
                    components+=("memory")
                fi
                
                if [[ ${#components[@]} -gt 0 ]]; then
                    log_success "Found components: ${components[*]}"
                    add_result "Health Components" "PASS" "Components: ${components[*]}"
                else
                    log_warning "No health components found"
                    add_result "Health Components" "WARN" "No components detected"
                fi
            else
                log_error "Invalid JSON format"
                add_result "Health Response Format" "FAIL" "Invalid JSON"
            fi
        fi
    else
        log_error "Not available (HTTP $response)"
        add_result "Health Endpoint" "FAIL" "HTTP $response"
    fi
    
    # Test metrics endpoint
    echo -n "Metrics endpoint availability: "
    if response=$(test_http_endpoint "http://localhost:8000/metrics" "200 404" 10); then
        if [[ "$response" == "200" ]]; then
            log_success "Available (HTTP $response)"
            add_result "Metrics Endpoint" "PASS" "HTTP $response"
        else
            log_warning "Not implemented (HTTP $response)"
            add_result "Metrics Endpoint" "WARN" "HTTP $response - not implemented"
        fi
    else
        log_error "Not available (HTTP $response)"
        add_result "Metrics Endpoint" "FAIL" "HTTP $response"
    fi
}

# Test monitoring configuration files
test_monitoring_config() {
    log_info "Testing monitoring configuration files..."
    
    local config_files=(
        "monitoring/config/prometheus.yml:Prometheus Config"
        "monitoring/alerts/daily-scribe.yml:Alert Rules"
        "monitoring/config/loki.yml:Loki Config"
        "monitoring/config/promtail.yml:Promtail Config"
        "docker-compose.monitoring.yml:Monitoring Compose"
    )
    
    for config_entry in "${config_files[@]}"; do
        IFS=':' read -r file_path description <<< "$config_entry"
        echo -n "$description: "
        
        if [[ -f "$file_path" ]]; then
            # Basic file validation
            if [[ -s "$file_path" ]]; then
                log_success "Present and non-empty"
                add_result "$description" "PASS" "File exists and has content"
                
                # YAML validation if possible
                if command_exists yamllint && [[ "$file_path" == *.yml ]]; then
                    if yamllint "$file_path" &>/dev/null; then
                        log_verbose "$description: YAML syntax valid"
                    else
                        log_warning "$description: YAML syntax issues detected"
                        add_result "$description YAML" "WARN" "Syntax issues"
                    fi
                fi
            else
                log_warning "Present but empty"
                add_result "$description" "WARN" "File exists but is empty"
            fi
        else
            log_error "Missing"
            add_result "$description" "FAIL" "File not found"
        fi
    done
}

# Test monitoring services
test_monitoring_services() {
    log_info "Testing monitoring services..."
    
    # Check if monitoring docker-compose exists
    if [[ ! -f "docker-compose.monitoring.yml" ]]; then
        log_warning "Monitoring docker-compose not found, skipping service tests"
        add_result "Monitoring Services" "WARN" "Configuration not found"
        return 0
    fi
    
    local services=(
        "prometheus:daily-scribe-prometheus:Prometheus"
        "grafana:daily-scribe-grafana:Grafana"
        "node-exporter:daily-scribe-node-exporter:Node Exporter"
        "loki:daily-scribe-loki:Loki"
        "promtail:daily-scribe-promtail:Promtail"
    )
    
    for service_entry in "${services[@]}"; do
        IFS=':' read -r service_name container_name description <<< "$service_entry"
        echo -n "$description service: "
        
        if test_docker_service "$service_name" "$container_name"; then
            log_success "Running"
            add_result "$description Service" "PASS" "Container running"
            
            # Test service-specific endpoints
            case "$service_name" in
                "prometheus")
                    echo -n "Prometheus web UI: "
                    if response=$(test_http_endpoint "http://localhost:9090/-/healthy" "200" 5); then
                        log_success "Accessible (HTTP $response)"
                        add_result "Prometheus Web UI" "PASS" "HTTP $response"
                    else
                        log_error "Not accessible (HTTP $response)"
                        add_result "Prometheus Web UI" "FAIL" "HTTP $response"
                    fi
                    ;;
                "grafana")
                    echo -n "Grafana web UI: "
                    if response=$(test_http_endpoint "http://localhost:3000/api/health" "200" 5); then
                        log_success "Accessible (HTTP $response)"
                        add_result "Grafana Web UI" "PASS" "HTTP $response"
                    else
                        log_error "Not accessible (HTTP $response)"
                        add_result "Grafana Web UI" "FAIL" "HTTP $response"
                    fi
                    ;;
                "loki")
                    echo -n "Loki API: "
                    if response=$(test_http_endpoint "http://localhost:3100/ready" "200" 5); then
                        log_success "Accessible (HTTP $response)"
                        add_result "Loki API" "PASS" "HTTP $response"
                    else
                        log_error "Not accessible (HTTP $response)"
                        add_result "Loki API" "FAIL" "HTTP $response"
                    fi
                    ;;
            esac
        else
            log_warning "Not running"
            add_result "$description Service" "WARN" "Container not running"
        fi
    done
}

# Test alert configuration
test_alert_config() {
    log_info "Testing alert configuration..."
    
    # Check environment variables for alerting
    local alert_vars=(
        "ALERT_EMAIL:Alert Email"
        "SMTP_HOST:SMTP Host"
        "SMTP_USERNAME:SMTP Username"
        "SMTP_PASSWORD:SMTP Password"
        "SLACK_WEBHOOK_URL:Slack Webhook"
    )
    
    for var_entry in "${alert_vars[@]}"; do
        IFS=':' read -r var_name description <<< "$var_entry"
        echo -n "$description: "
        
        if [[ -n "${!var_name:-}" ]]; then
            log_success "Configured"
            add_result "$description" "PASS" "Environment variable set"
        else
            log_warning "Not configured"
            add_result "$description" "WARN" "Environment variable not set"
        fi
    done
    
    # Test alert rules syntax
    if [[ -f "monitoring/alerts/daily-scribe.yml" ]]; then
        echo -n "Alert rules syntax: "
        if command_exists promtool; then
            if promtool check rules monitoring/alerts/daily-scribe.yml &>/dev/null; then
                log_success "Valid"
                add_result "Alert Rules Syntax" "PASS" "Prometheus syntax valid"
            else
                log_error "Invalid"
                add_result "Alert Rules Syntax" "FAIL" "Prometheus syntax errors"
            fi
        else
            log_warning "Cannot validate (promtool not available)"
            add_result "Alert Rules Syntax" "WARN" "Validation tool not available"
        fi
    fi
}

# Test external monitoring
test_external_monitoring() {
    log_info "Testing external monitoring configuration..."
    
    # Check external monitoring environment variables
    local external_vars=(
        "UPTIMEROBOT_API_KEY:UptimeRobot API Key"
        "UPTIMEROBOT_MONITOR_URL:UptimeRobot Monitor URL"
        "HEALTHCHECKS_UUID:Healthchecks.io UUID"
        "STATUSCAKE_API_KEY:StatusCake API Key"
    )
    
    local external_configured=false
    for var_entry in "${external_vars[@]}"; do
        IFS=':' read -r var_name description <<< "$var_entry"
        echo -n "$description: "
        
        if [[ -n "${!var_name:-}" ]]; then
            log_success "Configured"
            add_result "$description" "PASS" "Environment variable set"
            external_configured=true
        else
            log_warning "Not configured"
            add_result "$description" "WARN" "Environment variable not set"
        fi
    done
    
    if [[ "$external_configured" == false ]]; then
        log_warning "No external monitoring providers configured"
        add_result "External Monitoring" "WARN" "No providers configured"
    else
        log_success "At least one external monitoring provider configured"
        add_result "External Monitoring" "PASS" "Providers configured"
    fi
    
    # Test external monitoring script
    echo -n "External monitoring script: "
    if [[ -f "scripts/external-monitor.sh" ]]; then
        if [[ -x "scripts/external-monitor.sh" ]]; then
            log_success "Present and executable"
            add_result "External Monitor Script" "PASS" "Script ready"
        else
            log_warning "Present but not executable"
            add_result "External Monitor Script" "WARN" "Script not executable"
        fi
    else
        log_error "Missing"
        add_result "External Monitor Script" "FAIL" "Script not found"
    fi
}

# Test log management
test_log_management() {
    log_info "Testing log management..."
    
    # Check Docker logging configuration
    echo -n "Docker logging configuration: "
    if [[ -f "docker-compose.yml" ]]; then
        if grep -q "logging:" docker-compose.yml; then
            log_success "Configured in docker-compose.yml"
            add_result "Docker Logging" "PASS" "Logging section found"
        else
            log_warning "Not configured in docker-compose.yml"
            add_result "Docker Logging" "WARN" "No logging configuration"
        fi
    else
        log_error "docker-compose.yml not found"
        add_result "Docker Logging" "FAIL" "Main compose file missing"
    fi
    
    # Check log rotation
    echo -n "Log rotation configuration: "
    if [[ -f "docker-compose.yml" ]] && grep -q "max-size\|max-file" docker-compose.yml; then
        log_success "Log rotation configured"
        add_result "Log Rotation" "PASS" "Rotation parameters set"
    else
        log_warning "Log rotation not configured"
        add_result "Log Rotation" "WARN" "No rotation configuration"
    fi
    
    # Check for log aggregation setup
    echo -n "Log aggregation (Loki/Promtail): "
    if [[ -f "monitoring/config/loki.yml" ]] && [[ -f "monitoring/config/promtail.yml" ]]; then
        log_success "Configured"
        add_result "Log Aggregation" "PASS" "Loki and Promtail configured"
    else
        log_warning "Not configured"
        add_result "Log Aggregation" "WARN" "Loki/Promtail not set up"
    fi
}

# Test dashboard availability
test_dashboards() {
    log_info "Testing dashboard availability..."
    
    # Test simple status dashboard
    echo -n "Simple status dashboard: "
    if [[ -f "static/status.html" ]]; then
        log_success "Available"
        add_result "Status Dashboard" "PASS" "HTML dashboard present"
        
        # Test if it's accessible via web server
        echo -n "Status dashboard accessibility: "
        if response=$(test_http_endpoint "http://localhost:8000/static/status.html" "200 404" 5); then
            if [[ "$response" == "200" ]]; then
                log_success "Accessible (HTTP $response)"
                add_result "Status Dashboard Access" "PASS" "HTTP $response"
            else
                log_warning "Not accessible (HTTP $response)"
                add_result "Status Dashboard Access" "WARN" "HTTP $response"
            fi
        else
            log_error "Not accessible (HTTP $response)"
            add_result "Status Dashboard Access" "FAIL" "HTTP $response"
        fi
    else
        log_warning "Not found"
        add_result "Status Dashboard" "WARN" "Dashboard file missing"
    fi
    
    # Test Grafana dashboards
    echo -n "Grafana dashboard configuration: "
    if [[ -d "monitoring/dashboards" ]] && [[ -n "$(ls -A monitoring/dashboards 2>/dev/null)" ]]; then
        local dashboard_count
        dashboard_count=$(ls monitoring/dashboards/*.json 2>/dev/null | wc -l)
        log_success "$dashboard_count dashboard(s) configured"
        add_result "Grafana Dashboards" "PASS" "$dashboard_count dashboards"
    else
        log_warning "No dashboards configured"
        add_result "Grafana Dashboards" "WARN" "No dashboard files"
    fi
}

# Test overall system health
test_system_health() {
    log_info "Testing overall system health..."
    
    # Check disk space
    echo -n "Disk space availability: "
    local disk_usage
    disk_usage=$(df . | tail -1 | awk '{print $(NF-1)}' | sed 's/%//')
    
    if [[ $disk_usage -lt 80 ]]; then
        log_success "${disk_usage}% used"
        add_result "Disk Space" "PASS" "${disk_usage}% used"
    elif [[ $disk_usage -lt 90 ]]; then
        log_warning "${disk_usage}% used"
        add_result "Disk Space" "WARN" "${disk_usage}% used"
    else
        log_error "${disk_usage}% used"
        add_result "Disk Space" "FAIL" "${disk_usage}% used"
    fi
    
    # Check memory usage if possible
    if command_exists free; then
        echo -n "Memory usage: "
        local mem_usage
        mem_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100}')
        
        if [[ $mem_usage -lt 80 ]]; then
            log_success "${mem_usage}% used"
            add_result "Memory Usage" "PASS" "${mem_usage}% used"
        elif [[ $mem_usage -lt 90 ]]; then
            log_warning "${mem_usage}% used"
            add_result "Memory Usage" "WARN" "${mem_usage}% used"
        else
            log_error "${mem_usage}% used"
            add_result "Memory Usage" "FAIL" "${mem_usage}% used"
        fi
    fi
    
    # Check Docker daemon
    echo -n "Docker daemon: "
    if command_exists docker && docker info &>/dev/null; then
        log_success "Running"
        add_result "Docker Daemon" "PASS" "Docker daemon accessible"
    else
        log_error "Not accessible"
        add_result "Docker Daemon" "FAIL" "Cannot access Docker"
    fi
    
    # Check main application
    echo -n "Daily Scribe application: "
    if test_docker_service "app" "daily-scribe"; then
        log_success "Running"
        add_result "Main Application" "PASS" "Container running"
    else
        log_warning "Not running"
        add_result "Main Application" "WARN" "Container not running"
    fi
}

# Generate comprehensive report
generate_report() {
    echo ""
    echo "================================================================"
    echo "         Daily Scribe Monitoring Test Report"
    echo "================================================================"
    echo "Test Date: $(date)"
    echo "System: $(uname -s) $(uname -r)"
    echo "Docker: $(docker --version 2>/dev/null || echo "Not available")"
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
        esac
    done
    
    echo ""
    echo "Overall Assessment:"
    echo "=================="
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        if [[ $TESTS_WARNING -eq 0 ]]; then
            echo -e "${GREEN}✓ EXCELLENT${NC} - All monitoring components are working perfectly!"
        else
            echo -e "${YELLOW}⚠ GOOD${NC} - Monitoring is functional but some optional components need attention."
        fi
    elif [[ $TESTS_FAILED -lt 3 ]]; then
        echo -e "${YELLOW}⚠ NEEDS ATTENTION${NC} - Some monitoring components require fixes."
    else
        echo -e "${RED}✗ CRITICAL ISSUES${NC} - Monitoring setup needs significant work."
    fi
    
    echo ""
    echo "Recommendations:"
    echo "==============="
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo "Critical Actions Required:"
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name status details <<< "$result"
            if [[ "$status" == "FAIL" ]]; then
                case "$test_name" in
                    "Health Endpoint")
                        echo "  • Start Daily Scribe application: docker-compose up -d"
                        ;;
                    *"Config")
                        echo "  • Run monitoring setup: ./scripts/setup-monitoring.sh --internal"
                        ;;
                    *"Service")
                        echo "  • Start monitoring services: docker-compose -f docker-compose.monitoring.yml up -d"
                        ;;
                    "Main Application")
                        echo "  • Check application logs: docker-compose logs app"
                        ;;
                    "Docker Daemon")
                        echo "  • Start Docker daemon and ensure user has permissions"
                        ;;
                esac
            fi
        done
    fi
    
    if [[ $TESTS_WARNING -gt 0 ]]; then
        echo ""
        echo "Optional Improvements:"
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name status details <<< "$result"
            if [[ "$status" == "WARN" ]]; then
                case "$test_name" in
                    *"Alert Email"|*"SMTP"*)
                        echo "  • Configure email alerts in .env file"
                        ;;
                    "External Monitoring")
                        echo "  • Set up external monitoring providers (UptimeRobot, etc.)"
                        ;;
                    "Grafana Dashboards")
                        echo "  • Run: ./scripts/setup-monitoring.sh --grafana"
                        ;;
                    "Log Aggregation")
                        echo "  • Set up centralized logging: ./scripts/setup-monitoring.sh --loki"
                        ;;
                esac
            fi
        done
    fi
    
    echo ""
    echo "Next Steps:"
    echo "=========="
    if [[ $TESTS_FAILED -eq 0 ]] && [[ $TESTS_WARNING -eq 0 ]]; then
        echo "1. Monitor your system for 24-48 hours to ensure stability"
        echo "2. Set up regular testing schedule (weekly recommended)"
        echo "3. Document any custom configurations"
        echo "4. Train team on monitoring procedures"
    else
        echo "1. Address critical issues first"
        echo "2. Configure optional components for better coverage"
        echo "3. Re-run this test after making changes"
        echo "4. Set up regular monitoring once stable"
    fi
    
    # Return appropriate exit code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Daily Scribe Monitoring Test Script

Usage: $0 [OPTIONS]

OPTIONS:
    -v, --verbose         Show detailed debug information
    -h, --help           Show this help message

EXAMPLES:
    $0                   # Run all monitoring tests
    $0 --verbose         # Run tests with detailed output

This script performs comprehensive testing of:
- Application health endpoints
- Monitoring service configuration
- Alert configuration and delivery
- External monitoring setup
- Log management and rotation
- Dashboard availability
- Overall system health

Run this script after setting up monitoring to ensure everything works correctly.

EOF
}

# Main function
main() {
    echo "Daily Scribe Monitoring Test"
    echo "==========================="
    echo ""
    
    # Load environment if .env file exists
    if [[ -f ".env" ]]; then
        # shellcheck source=/dev/null
        set -a
        source .env
        set +a
        log_verbose "Loaded environment variables from .env"
    fi
    
    test_application_health
    echo ""
    
    test_monitoring_config
    echo ""
    
    test_monitoring_services
    echo ""
    
    test_alert_config
    echo ""
    
    test_external_monitoring
    echo ""
    
    test_log_management
    echo ""
    
    test_dashboards
    echo ""
    
    test_system_health
    echo ""
    
    generate_report
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
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
