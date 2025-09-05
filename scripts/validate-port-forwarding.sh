#!/bin/bash

# Daily Scribe Port Forwarding Validation Script
# Comprehensive testing for router port forwarding configuration

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

# Test TCP port connectivity
test_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-5}"
    
    if timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Test HTTP response
test_http_response() {
    local url="$1"
    local expected_codes="$2"
    local timeout="${3:-10}"
    
    local response_code
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

# Get public IP address
get_public_ip() {
    local ip_services=(
        "https://ipv4.icanhazip.com"
        "https://api.ipify.org"
        "https://checkip.amazonaws.com"
        "https://ipinfo.io/ip"
    )
    
    for service in "${ip_services[@]}"; do
        if command_exists curl; then
            if ip=$(curl -s --max-time 5 "$service" 2>/dev/null); then
                if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                    echo "$ip"
                    return 0
                fi
            fi
        fi
    done
    
    return 1
}

# Test DNS resolution
test_dns() {
    local domain="$1"
    local expected_ip="${2:-}"
    
    local resolved_ip=""
    if command_exists dig; then
        resolved_ip=$(dig +short "$domain" @8.8.8.8 2>/dev/null | grep -E '^[0-9]+\.' | head -1)
    elif command_exists nslookup; then
        resolved_ip=$(nslookup "$domain" 8.8.8.8 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    else
        log_warning "Neither dig nor nslookup available"
        return 1
    fi
    
    if [[ -n "$resolved_ip" ]]; then
        if [[ -n "$expected_ip" ]] && [[ "$resolved_ip" != "$expected_ip" ]]; then
            echo "$resolved_ip (expected: $expected_ip)"
            return 1
        else
            echo "$resolved_ip"
            return 0
        fi
    else
        return 1
    fi
}

# Check local services
test_local_services() {
    log_info "Testing local services..."
    
    # Test if Daily Scribe app is running
    echo -n "Daily Scribe app (port 8000): "
    if test_port "localhost" "8000" 3; then
        log_success "Running"
        add_result "Local App Service" "PASS" "Port 8000 accessible"
        
        # Test health endpoint
        echo -n "Health endpoint response: "
        if response=$(test_http_response "http://localhost:8000/healthz" "200" 5); then
            log_success "Healthy (HTTP $response)"
            add_result "Health Endpoint" "PASS" "HTTP $response"
        else
            log_error "Unhealthy (HTTP $response)"
            add_result "Health Endpoint" "FAIL" "HTTP $response"
        fi
    else
        log_error "Not running"
        add_result "Local App Service" "FAIL" "Port 8000 not accessible"
    fi
    
    # Test Caddy proxy
    echo -n "Caddy HTTP proxy (port 80): "
    if test_port "localhost" "80" 3; then
        log_success "Running"
        add_result "Caddy HTTP" "PASS" "Port 80 accessible"
    else
        log_warning "Not running"
        add_result "Caddy HTTP" "WARN" "Port 80 not accessible"
    fi
    
    echo -n "Caddy HTTPS proxy (port 443): "
    if test_port "localhost" "443" 3; then
        log_success "Running"
        add_result "Caddy HTTPS" "PASS" "Port 443 accessible"
    else
        log_warning "Not running"
        add_result "Caddy HTTPS" "WARN" "Port 443 not accessible"
    fi
    
    # Check Docker containers if Docker is available
    if command_exists docker; then
        echo -n "Docker containers status: "
        local running_containers
        running_containers=$(docker ps --filter "name=daily-scribe" --format "{{.Names}}" | wc -l)
        if [[ $running_containers -gt 0 ]]; then
            log_success "$running_containers containers running"
            add_result "Docker Containers" "PASS" "$running_containers containers running"
        else
            log_warning "No Daily Scribe containers running"
            add_result "Docker Containers" "WARN" "No containers running"
        fi
    fi
}

# Test network configuration
test_network_config() {
    log_info "Testing network configuration..."
    
    # Get local IP
    echo -n "Local IP detection: "
    local local_ip=""
    if command_exists hostname; then
        local_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")
    fi
    
    if [[ -z "$local_ip" ]] && command_exists ip; then
        local_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -1 || echo "")
    fi
    
    if [[ -n "$local_ip" ]]; then
        log_success "$local_ip"
        add_result "Local IP Detection" "PASS" "$local_ip"
        export LOCAL_IP="$local_ip"
    else
        log_error "Failed to detect local IP"
        add_result "Local IP Detection" "FAIL" "Could not determine local IP"
    fi
    
    # Get gateway IP
    echo -n "Gateway IP detection: "
    local gateway_ip=""
    if command_exists ip; then
        gateway_ip=$(ip route | grep default | awk '{print $3}' | head -1 || echo "")
    fi
    
    if [[ -n "$gateway_ip" ]]; then
        log_success "$gateway_ip"
        add_result "Gateway Detection" "PASS" "$gateway_ip"
        export GATEWAY_IP="$gateway_ip"
        
        # Test gateway connectivity
        echo -n "Gateway connectivity: "
        if ping -c 1 -W 3 "$gateway_ip" &> /dev/null; then
            log_success "Reachable"
            add_result "Gateway Connectivity" "PASS" "Gateway reachable"
        else
            log_error "Unreachable"
            add_result "Gateway Connectivity" "FAIL" "Gateway unreachable"
        fi
    else
        log_error "Failed to detect gateway"
        add_result "Gateway Detection" "FAIL" "Could not determine gateway"
    fi
    
    # Test internet connectivity
    echo -n "Internet connectivity: "
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        log_success "Connected"
        add_result "Internet Connectivity" "PASS" "Internet reachable"
    else
        log_error "No internet connection"
        add_result "Internet Connectivity" "FAIL" "Internet unreachable"
    fi
}

# Test external accessibility
test_external_access() {
    log_info "Testing external accessibility..."
    
    # Get public IP
    echo -n "Public IP detection: "
    local public_ip=""
    if public_ip=$(get_public_ip); then
        log_success "$public_ip"
        add_result "Public IP Detection" "PASS" "$public_ip"
        export PUBLIC_IP="$public_ip"
    else
        log_error "Failed to get public IP"
        add_result "Public IP Detection" "FAIL" "Could not determine public IP"
        return 1
    fi
    
    # Test external port accessibility
    echo -n "External port 80 accessibility: "
    if test_port "$public_ip" "80" 10; then
        log_success "Port 80 is open"
        add_result "External Port 80" "PASS" "Port accessible from internet"
    else
        log_error "Port 80 is closed/filtered"
        add_result "External Port 80" "FAIL" "Port not accessible from internet"
    fi
    
    echo -n "External port 443 accessibility: "
    if test_port "$public_ip" "443" 10; then
        log_success "Port 443 is open"
        add_result "External Port 443" "PASS" "Port accessible from internet"
    else
        log_error "Port 443 is closed/filtered"
        add_result "External Port 443" "FAIL" "Port not accessible from internet"
    fi
}

# Test DDNS configuration
test_ddns_config() {
    if [[ -z "${DDNS_DOMAIN:-}" ]]; then
        log_info "DDNS_DOMAIN not set, skipping DDNS tests"
        return 0
    fi
    
    log_info "Testing DDNS configuration for: $DDNS_DOMAIN"
    
    # Test DNS resolution
    echo -n "DDNS domain resolution: "
    local resolved_ip=""
    if resolved_ip=$(test_dns "$DDNS_DOMAIN" "${PUBLIC_IP:-}"); then
        log_success "Resolves to $resolved_ip"
        add_result "DDNS Resolution" "PASS" "Resolves to $resolved_ip"
    else
        log_error "DNS resolution failed: $resolved_ip"
        add_result "DDNS Resolution" "FAIL" "DNS resolution failed"
        return 1
    fi
    
    # Test HTTP access via domain
    echo -n "HTTP access via domain: "
    if response=$(test_http_response "http://$DDNS_DOMAIN" "200 301 302" 15); then
        log_success "Working (HTTP $response)"
        add_result "Domain HTTP Access" "PASS" "HTTP $response"
    else
        log_error "Failed (HTTP $response)"
        add_result "Domain HTTP Access" "FAIL" "HTTP $response"
    fi
    
    # Test HTTPS access via domain
    echo -n "HTTPS access via domain: "
    if response=$(test_http_response "https://$DDNS_DOMAIN/healthz" "200" 15); then
        log_success "Working (HTTP $response)"
        add_result "Domain HTTPS Access" "PASS" "HTTP $response"
    else
        log_error "Failed (HTTP $response)"
        add_result "Domain HTTPS Access" "FAIL" "HTTP $response"
    fi
    
    # Test SSL certificate
    if command_exists openssl; then
        echo -n "SSL certificate validation: "
        if echo | timeout 10 openssl s_client -servername "$DDNS_DOMAIN" -connect "$DDNS_DOMAIN:443" &>/dev/null; then
            log_success "Valid SSL certificate"
            add_result "SSL Certificate" "PASS" "Certificate valid"
        else
            log_error "SSL certificate issues"
            add_result "SSL Certificate" "FAIL" "Certificate problems"
        fi
    fi
}

# Test router security
test_router_security() {
    log_info "Testing router security configuration..."
    
    # Test if router admin interface is externally accessible (should NOT be)
    if [[ -n "${GATEWAY_IP:-}" ]]; then
        echo -n "Router admin interface security: "
        if [[ -n "${PUBLIC_IP:-}" ]]; then
            # Test common router admin ports from external perspective
            local admin_ports=(80 443 8080 8443)
            local exposed_ports=()
            
            for port in "${admin_ports[@]}"; do
                if test_port "$PUBLIC_IP" "$port" 3; then
                    # Check if this looks like router admin interface
                    if response=$(test_http_response "http://$PUBLIC_IP:$port" "200" 5); then
                        exposed_ports+=("$port")
                    fi
                fi
            done
            
            if [[ ${#exposed_ports[@]} -eq 0 ]]; then
                log_success "Router admin interface not externally accessible"
                add_result "Router Security" "PASS" "Admin interface not exposed"
            else
                log_error "Router admin interface may be exposed on ports: ${exposed_ports[*]}"
                add_result "Router Security" "FAIL" "Admin interface potentially exposed"
            fi
        else
            log_warning "Cannot test without public IP"
            add_result "Router Security" "WARN" "Cannot test without public IP"
        fi
    fi
    
    # Test for common vulnerable ports
    if [[ -n "${PUBLIC_IP:-}" ]]; then
        echo -n "Vulnerable port scan: "
        local vulnerable_ports=(21 22 23 25 53 135 139 445 993 995 1433 3389 5432 5900)
        local open_ports=()
        
        for port in "${vulnerable_ports[@]}"; do
            if test_port "$PUBLIC_IP" "$port" 2; then
                open_ports+=("$port")
            fi
        done
        
        if [[ ${#open_ports[@]} -eq 0 ]]; then
            log_success "No common vulnerable ports detected"
            add_result "Vulnerable Ports" "PASS" "No vulnerable ports open"
        else
            log_warning "Open ports detected: ${open_ports[*]} (verify these are intentional)"
            add_result "Vulnerable Ports" "WARN" "Open ports: ${open_ports[*]}"
        fi
    fi
}

# Generate detailed report
generate_report() {
    echo ""
    echo "================================================================"
    echo "         Daily Scribe Port Forwarding Validation Report"
    echo "================================================================"
    echo "Test Date: $(date)"
    echo "Local IP: ${LOCAL_IP:-Unknown}"
    echo "Gateway IP: ${GATEWAY_IP:-Unknown}"
    echo "Public IP: ${PUBLIC_IP:-Unknown}"
    echo "DDNS Domain: ${DDNS_DOMAIN:-Not configured}"
    echo ""
    
    echo "Detailed Test Results:"
    echo "====================="
    
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
    echo "Summary:"
    echo "========"
    echo "Total tests: $((TESTS_PASSED + TESTS_FAILED + TESTS_WARNING))"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Warnings: $TESTS_WARNING"
    echo ""
    
    # Overall assessment
    if [[ $TESTS_FAILED -eq 0 ]]; then
        if [[ $TESTS_WARNING -eq 0 ]]; then
            echo -e "${GREEN}✓ Overall Status: EXCELLENT${NC}"
            echo "Your port forwarding configuration is working perfectly!"
        else
            echo -e "${YELLOW}⚠ Overall Status: GOOD WITH WARNINGS${NC}"
            echo "Port forwarding is working but there are some items to review."
        fi
    else
        echo -e "${RED}✗ Overall Status: ISSUES DETECTED${NC}"
        echo "Port forwarding configuration needs attention."
    fi
    
    # Provide specific recommendations
    echo ""
    echo "Recommendations:"
    echo "==============="
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo "Critical Issues to Address:"
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name status details <<< "$result"
            if [[ "$status" == "FAIL" ]]; then
                case "$test_name" in
                    "Local App Service")
                        echo "  • Start Daily Scribe application: docker-compose up -d"
                        ;;
                    "External Port 80"|"External Port 443")
                        echo "  • Configure port forwarding on router for ports 80 and 443"
                        echo "  • Check router firewall settings"
                        echo "  • Verify server firewall allows these ports"
                        ;;
                    "DDNS Resolution")
                        echo "  • Check DDNS provider configuration"
                        echo "  • Verify domain name spelling"
                        echo "  • Wait for DNS propagation (up to 15 minutes)"
                        ;;
                    "Domain HTTPS Access")
                        echo "  • Verify Caddy is running and configured correctly"
                        echo "  • Check SSL certificate provisioning"
                        echo "  • Ensure domain points to correct IP"
                        ;;
                esac
            fi
        done
    fi
    
    if [[ $TESTS_WARNING -gt 0 ]]; then
        echo ""
        echo "Items to Review:"
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name status details <<< "$result"
            if [[ "$status" == "WARN" ]]; then
                case "$test_name" in
                    "Caddy HTTP"|"Caddy HTTPS")
                        echo "  • Consider starting Caddy proxy for full functionality"
                        ;;
                    "Vulnerable Ports")
                        echo "  • Review open ports and ensure they are intentionally exposed"
                        echo "  • Consider closing unnecessary ports for security"
                        ;;
                    "Router Security")
                        echo "  • Verify router admin interface is not externally accessible"
                        ;;
                esac
            fi
        done
    fi
    
    echo ""
    echo "Next Steps:"
    echo "==========="
    if [[ $TESTS_FAILED -eq 0 ]] && [[ $TESTS_WARNING -eq 0 ]]; then
        echo "1. Document your working configuration"
        echo "2. Set up monitoring for ongoing validation"
        echo "3. Schedule regular testing (weekly recommended)"
        echo "4. Proceed with production deployment"
    else
        echo "1. Address critical issues listed above"
        echo "2. Re-run this test after making changes"
        echo "3. Consult router documentation for specific configuration steps"
        echo "4. Consider using the router configuration checklist"
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
Daily Scribe Port Forwarding Validation Script

Usage: $0 [OPTIONS]

OPTIONS:
    -d, --domain DOMAIN    DDNS domain to test (optional)
    -h, --help            Show this help message

ENVIRONMENT VARIABLES:
    DDNS_DOMAIN           Domain name for DDNS testing
    PUBLIC_IP             Public IP address (auto-detected if not set)
    LOCAL_IP              Local server IP (auto-detected if not set)

EXAMPLES:
    $0                                    # Basic port forwarding test
    $0 -d mydomain.duckdns.org           # Test with DDNS domain
    DDNS_DOMAIN=mydomain.duckdns.org $0  # Test with environment variable

This script performs comprehensive testing of:
- Local service availability
- Network configuration
- External port accessibility
- DDNS configuration (if configured)
- Basic security checks

Run this script after configuring port forwarding to ensure everything works correctly.

EOF
}

# Main function
main() {
    echo "Daily Scribe Port Forwarding Validation"
    echo "======================================="
    echo ""
    
    # Load environment if .env file exists
    if [[ -f ".env" ]]; then
        # shellcheck source=/dev/null
        source .env
    fi
    
    test_local_services
    echo ""
    
    test_network_config
    echo ""
    
    test_external_access
    echo ""
    
    test_ddns_config
    echo ""
    
    test_router_security
    echo ""
    
    generate_report
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DDNS_DOMAIN="$2"
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
