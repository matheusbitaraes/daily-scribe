#!/bin/bash

# Daily Scribe External Connectivity Test Script
# Tests port forwarding configuration and external accessibility

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT_SECONDS=10
MAX_RETRIES=3
TEST_RESULTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Test result tracking
add_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    TEST_RESULTS+=("$test_name|$status|$details")
}

# Get current public IP address
get_public_ip() {
    local ip_services=(
        "https://ipv4.icanhazip.com"
        "https://api.ipify.org"
        "https://checkip.amazonaws.com"
        "https://ipinfo.io/ip"
    )
    
    for service in "${ip_services[@]}"; do
        if ip=$(curl -s --max-time 5 "$service" 2>/dev/null); then
            if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                echo "$ip"
                return 0
            fi
        fi
    done
    
    return 1
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
test_http() {
    local url="$1"
    local expected_codes="$2"
    local timeout="${3:-10}"
    
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null)
    
    if [[ "$expected_codes" == *"$response_code"* ]]; then
        echo "$response_code"
        return 0
    else
        echo "$response_code"
        return 1
    fi
}

# Test DNS resolution
test_dns_resolution() {
    local domain="$1"
    local expected_ip="${2:-}"
    
    local resolved_ip
    if command -v dig &> /dev/null; then
        resolved_ip=$(dig +short "$domain" @8.8.8.8 2>/dev/null | head -1)
    elif command -v nslookup &> /dev/null; then
        resolved_ip=$(nslookup "$domain" 8.8.8.8 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    else
        log_warning "Neither dig nor nslookup available for DNS testing"
        return 1
    fi
    
    if [[ -n "$resolved_ip" ]]; then
        if [[ -n "$expected_ip" ]]; then
            if [[ "$resolved_ip" == "$expected_ip" ]]; then
                echo "$resolved_ip"
                return 0
            else
                echo "$resolved_ip (expected: $expected_ip)"
                return 1
            fi
        else
            echo "$resolved_ip"
            return 0
        fi
    else
        return 1
    fi
}

# Test SSL certificate
test_ssl_certificate() {
    local domain="$1"
    local port="${2:-443}"
    
    if command -v openssl &> /dev/null; then
        local cert_info
        cert_info=$(echo | timeout 10 openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        
        if [[ -n "$cert_info" ]]; then
            echo "$cert_info"
            return 0
        else
            return 1
        fi
    else
        log_warning "OpenSSL not available for certificate testing"
        return 1
    fi
}

# Get local server information
get_local_server_info() {
    log_info "Detecting local server configuration..."
    
    # Try to determine server IP
    local server_ip=""
    if command -v hostname &> /dev/null; then
        server_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")
    fi
    
    if [[ -z "$server_ip" ]]; then
        server_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -1 || echo "")
    fi
    
    # Try to determine gateway IP
    local gateway_ip=""
    if command -v ip &> /dev/null; then
        gateway_ip=$(ip route | grep default | awk '{print $3}' | head -1 || echo "")
    fi
    
    echo "Local server IP: ${server_ip:-Unknown}"
    echo "Gateway IP: ${gateway_ip:-Unknown}"
    
    # Check if Daily Scribe services are running locally
    if command -v docker &> /dev/null; then
        echo "Docker containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep daily-scribe || echo "No Daily Scribe containers running"
    fi
}

# Test local connectivity
test_local_connectivity() {
    log_info "Testing local connectivity..."
    
    # Test localhost access
    echo -n "Local HTTP (port 8000): "
    if test_port "localhost" "8000" 3; then
        log_success "Accessible"
        add_result "Local HTTP" "PASS" "Port 8000 accessible"
        
        # Test health endpoint
        echo -n "Local health endpoint: "
        if response=$(test_http "http://localhost:8000/healthz" "200" 5); then
            log_success "Healthy (HTTP $response)"
            add_result "Local Health Check" "PASS" "HTTP $response"
        else
            log_error "Unhealthy (HTTP $response)"
            add_result "Local Health Check" "FAIL" "HTTP $response"
        fi
    else
        log_error "Not accessible"
        add_result "Local HTTP" "FAIL" "Port 8000 not accessible"
    fi
    
    # Test if Caddy is running
    echo -n "Local HTTPS proxy (port 443): "
    if test_port "localhost" "443" 3; then
        log_success "Accessible"
        add_result "Local HTTPS" "PASS" "Port 443 accessible"
    else
        log_warning "Not accessible (Caddy may not be running)"
        add_result "Local HTTPS" "WARN" "Port 443 not accessible"
    fi
    
    echo -n "Local HTTP proxy (port 80): "
    if test_port "localhost" "80" 3; then
        log_success "Accessible"
        add_result "Local HTTP Proxy" "PASS" "Port 80 accessible"
    else
        log_warning "Not accessible (Caddy may not be running)"
        add_result "Local HTTP Proxy" "WARN" "Port 80 not accessible"
    fi
}

# Test external connectivity
test_external_connectivity() {
    log_info "Testing external connectivity..."
    
    # Get public IP
    echo -n "Public IP detection: "
    local public_ip
    if public_ip=$(get_public_ip); then
        log_success "$public_ip"
        add_result "Public IP Detection" "PASS" "$public_ip"
    else
        log_error "Failed to detect public IP"
        add_result "Public IP Detection" "FAIL" "Could not determine public IP"
        return 1
    fi
    
    # Test port accessibility
    echo -n "External port 80 accessibility: "
    if test_port "$public_ip" "80" "$TIMEOUT_SECONDS"; then
        log_success "Open"
        add_result "External Port 80" "PASS" "Port is accessible"
    else
        log_error "Closed/Filtered"
        add_result "External Port 80" "FAIL" "Port not accessible"
    fi
    
    echo -n "External port 443 accessibility: "
    if test_port "$public_ip" "443" "$TIMEOUT_SECONDS"; then
        log_success "Open"
        add_result "External Port 443" "PASS" "Port is accessible"
    else
        log_error "Closed/Filtered"
        add_result "External Port 443" "FAIL" "Port not accessible"
    fi
    
    # Test HTTP response if domain is configured
    if [[ -n "${DDNS_DOMAIN:-}" ]]; then
        echo -n "DDNS domain resolution: "
        if resolved_ip=$(test_dns_resolution "$DDNS_DOMAIN" "$public_ip"); then
            log_success "$resolved_ip"
            add_result "DDNS Resolution" "PASS" "$resolved_ip"
            
            # Test HTTP redirect
            echo -n "HTTP redirect test: "
            if response=$(test_http "http://$DDNS_DOMAIN" "301 302" "$TIMEOUT_SECONDS"); then
                log_success "Working (HTTP $response)"
                add_result "HTTP Redirect" "PASS" "HTTP $response"
            else
                log_error "Failed (HTTP $response)"
                add_result "HTTP Redirect" "FAIL" "HTTP $response"
            fi
            
            # Test HTTPS connectivity
            echo -n "HTTPS connectivity test: "
            if response=$(test_http "https://$DDNS_DOMAIN/healthz" "200" "$TIMEOUT_SECONDS"); then
                log_success "Working (HTTP $response)"
                add_result "HTTPS Connectivity" "PASS" "HTTP $response"
            else
                log_error "Failed (HTTP $response)"
                add_result "HTTPS Connectivity" "FAIL" "HTTP $response"
            fi
            
            # Test SSL certificate
            echo -n "SSL certificate test: "
            if cert_info=$(test_ssl_certificate "$DDNS_DOMAIN"); then
                log_success "Valid certificate"
                add_result "SSL Certificate" "PASS" "Certificate valid"
            else
                log_error "Certificate issues"
                add_result "SSL Certificate" "FAIL" "Certificate problems"
            fi
        else
            log_error "$resolved_ip"
            add_result "DDNS Resolution" "FAIL" "$resolved_ip"
        fi
    else
        log_warning "DDNS_DOMAIN not set, skipping domain-specific tests"
        
        # Test direct IP access
        echo -n "Direct IP HTTP test: "
        if response=$(test_http "http://$public_ip" "200 301 302" "$TIMEOUT_SECONDS"); then
            log_success "Working (HTTP $response)"
            add_result "Direct IP HTTP" "PASS" "HTTP $response"
        else
            log_error "Failed (HTTP $response)"
            add_result "Direct IP HTTP" "FAIL" "HTTP $response"
        fi
    fi
}

# Generate detailed report
generate_report() {
    echo ""
    echo "=================================================="
    echo "        Daily Scribe Connectivity Test Report"
    echo "=================================================="
    echo "Test Date: $(date)"
    echo "Public IP: ${PUBLIC_IP:-Unknown}"
    echo "DDNS Domain: ${DDNS_DOMAIN:-Not configured}"
    echo ""
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local warning_tests=0
    
    echo "Test Results:"
    echo "============="
    
    for result in "${TEST_RESULTS[@]}"; do
        IFS='|' read -r test_name status details <<< "$result"
        ((total_tests++))
        
        case "$status" in
            "PASS")
                echo -e "${GREEN}✓${NC} $test_name: $details"
                ((passed_tests++))
                ;;
            "FAIL")
                echo -e "${RED}✗${NC} $test_name: $details"
                ((failed_tests++))
                ;;
            "WARN")
                echo -e "${YELLOW}⚠${NC} $test_name: $details"
                ((warning_tests++))
                ;;
        esac
    done
    
    echo ""
    echo "Summary:"
    echo "========"
    echo "Total tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    echo "Warnings: $warning_tests"
    
    if [[ $failed_tests -eq 0 ]]; then
        echo -e "${GREEN}Overall Status: SUCCESS${NC}"
        echo "Your Daily Scribe service appears to be externally accessible!"
        return 0
    else
        echo -e "${RED}Overall Status: ISSUES DETECTED${NC}"
        echo ""
        echo "Troubleshooting suggestions:"
        echo "==========================="
        
        # Provide specific troubleshooting advice based on failures
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name status details <<< "$result"
            if [[ "$status" == "FAIL" ]]; then
                case "$test_name" in
                    "External Port 80"|"External Port 443")
                        echo "- Check router port forwarding configuration"
                        echo "- Verify server firewall settings (ufw status)"
                        echo "- Ensure Daily Scribe services are running"
                        ;;
                    "DDNS Resolution")
                        echo "- Verify DDNS service configuration"
                        echo "- Check domain name spelling"
                        echo "- Wait for DNS propagation (up to 15 minutes)"
                        ;;
                    "HTTP Redirect"|"HTTPS Connectivity")
                        echo "- Check Caddy container status"
                        echo "- Verify Caddyfile configuration"
                        echo "- Check container logs: docker-compose logs caddy"
                        ;;
                    "SSL Certificate")
                        echo "- Verify domain name is correct"
                        echo "- Check Let's Encrypt rate limits"
                        echo "- Ensure port 443 is properly forwarded"
                        ;;
                esac
            fi
        done
        
        return 1
    fi
}

# Main function
main() {
    echo "Daily Scribe External Connectivity Test"
    echo "======================================"
    echo ""
    
    # Load environment variables if available
    if [[ -f ".env" ]]; then
        # shellcheck source=/dev/null
        source .env
    fi
    
    get_local_server_info
    echo ""
    
    test_local_connectivity
    echo ""
    
    test_external_connectivity
    echo ""
    
    generate_report
}

# Show usage information
show_usage() {
    cat << EOF
Daily Scribe External Connectivity Test Script

Usage: $0 [OPTIONS]

OPTIONS:
    -d, --domain DOMAIN    Set DDNS domain for testing
    -t, --timeout SECONDS  Set timeout for network tests (default: 10)
    -r, --retries COUNT    Set maximum retries for failed tests (default: 3)
    -h, --help            Show this help message

ENVIRONMENT VARIABLES:
    DDNS_DOMAIN           Domain name for DDNS testing
    TIMEOUT_SECONDS       Timeout for network operations
    MAX_RETRIES           Maximum retry attempts

EXAMPLES:
    $0                                    # Basic connectivity test
    $0 -d mydomain.duckdns.org           # Test with specific domain
    $0 -t 15 -r 5                       # Extended timeout and retries
    DDNS_DOMAIN=mydomain.duckdns.org $0  # Test with environment variable

This script tests:
- Local service accessibility
- External port forwarding
- DNS resolution (if domain configured)
- HTTP/HTTPS connectivity
- SSL certificate validity

Run this script after configuring port forwarding to verify external access.

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DDNS_DOMAIN="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT_SECONDS="$2"
            shift 2
            ;;
        -r|--retries)
            MAX_RETRIES="$2"
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
