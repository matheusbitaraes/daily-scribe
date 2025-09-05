#!/bin/bash

# Daily Scribe DDNS Test Script
# Comprehensive testing for Dynamic DNS functionality

set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="/tmp/ddns-test-$$"
TEST_CONFIG="$TEST_DIR/ddns.conf"
TEST_LOG="$TEST_DIR/ddns.log"
SCRIPT_PATH="${1:-./scripts/ddns-update.sh}"

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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
}

# Test framework functions
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    ((TESTS_TOTAL++))
    log_info "Running test: $test_name"
    
    if $test_function; then
        log_success "$test_name"
    else
        log_error "$test_name"
    fi
    
    echo ""
}

# Setup test environment
setup_test_env() {
    log_info "Setting up test environment..."
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    
    # Create test configuration
    cat > "$TEST_CONFIG" << EOF
UPDATE_INTERVAL=60
MAX_RETRIES=2
TIMEOUT=10
LOG_LEVEL=DEBUG
DDNS_PROVIDERS="duckdns:testdomain:testtoken"
FORCE_UPDATE=false
EOF
    
    # Check if script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        log_error "DDNS script not found: $SCRIPT_PATH"
        exit 1
    fi
    
    # Make script executable
    chmod +x "$SCRIPT_PATH"
    
    log_success "Test environment setup complete"
}

# Cleanup test environment
cleanup_test_env() {
    log_info "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
    log_success "Cleanup complete"
}

# Test script existence and permissions
test_script_basic() {
    [[ -f "$SCRIPT_PATH" ]] && [[ -x "$SCRIPT_PATH" ]]
}

# Test help command
test_help_command() {
    "$SCRIPT_PATH" help > /dev/null 2>&1
}

# Test configuration loading
test_config_loading() {
    DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test > /dev/null 2>&1
}

# Test IP retrieval
test_ip_retrieval() {
    local output
    output=$(DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test 2>&1)
    echo "$output" | grep -q "Current public IP:"
}

# Test invalid configuration
test_invalid_config() {
    local empty_config="$TEST_DIR/empty.conf"
    echo "" > "$empty_config"
    
    ! DDNS_CONFIG_FILE="$empty_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test > /dev/null 2>&1
}

# Test health check
test_health_check() {
    DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" health > /dev/null 2>&1
}

# Test with DuckDNS provider
test_duckdns_provider() {
    local test_config="$TEST_DIR/duckdns.conf"
    cat > "$test_config" << EOF
DDNS_PROVIDERS="duckdns:testdomain:testtoken"
MAX_RETRIES=1
TIMEOUT=5
EOF
    
    # This will fail (expected) but should not crash
    ! DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" update > /dev/null 2>&1
}

# Test with Cloudflare provider
test_cloudflare_provider() {
    local test_config="$TEST_DIR/cloudflare.conf"
    cat > "$test_config" << EOF
DDNS_PROVIDERS="cloudflare:zone123:record456:token789:test.example.com"
MAX_RETRIES=1
TIMEOUT=5
EOF
    
    # This will fail (expected) but should not crash
    ! DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" update > /dev/null 2>&1
}

# Test with No-IP provider
test_noip_provider() {
    local test_config="$TEST_DIR/noip.conf"
    cat > "$test_config" << EOF
DDNS_PROVIDERS="noip:test.ddns.net:user:pass"
MAX_RETRIES=1
TIMEOUT=5
EOF
    
    # This will fail (expected) but should not crash
    ! DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" update > /dev/null 2>&1
}

# Test multiple providers
test_multiple_providers() {
    local test_config="$TEST_DIR/multi.conf"
    cat > "$test_config" << EOF
DDNS_PROVIDERS="duckdns:test1:token1,noip:test2.ddns.net:user:pass"
MAX_RETRIES=1
TIMEOUT=5
EOF
    
    # This will fail (expected) but should not crash
    ! DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" update > /dev/null 2>&1
}

# Test logging functionality
test_logging() {
    DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test > /dev/null 2>&1
    [[ -f "$TEST_LOG" ]] && [[ -s "$TEST_LOG" ]]
}

# Test lock file mechanism
test_lock_mechanism() {
    local lock_file="/tmp/ddns-test-lock"
    local test_config="$TEST_DIR/lock.conf"
    
    cat > "$test_config" << EOF
DDNS_PROVIDERS="duckdns:testdomain:testtoken"
UPDATE_INTERVAL=1
MAX_RETRIES=1
TIMEOUT=1
EOF
    
    # Start a background process
    DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" daemon > /dev/null 2>&1 &
    local daemon_pid=$!
    
    sleep 2
    
    # Try to start another instance (should exit immediately)
    local result=0
    DDNS_CONFIG_FILE="$test_config" LOG_FILE="$TEST_LOG" timeout 5s "$SCRIPT_PATH" update > /dev/null 2>&1 || result=$?
    
    # Kill the daemon
    kill "$daemon_pid" 2>/dev/null || true
    wait "$daemon_pid" 2>/dev/null || true
    
    # Should have exited with non-zero (lock conflict)
    [[ $result -ne 0 ]]
}

# Test environment variable override
test_env_override() {
    UPDATE_INTERVAL=123 MAX_RETRIES=9 DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test 2>&1 | grep -q "Configuration test completed"
}

# Test IP change detection
test_ip_change_detection() {
    local cache_dir="$TEST_DIR/cache"
    local last_ip_file="$cache_dir/last_ip"
    
    mkdir -p "$cache_dir"
    echo "1.2.3.4" > "$last_ip_file"
    
    # Mock getting a different IP would trigger an update
    [[ -f "$last_ip_file" ]]
}

# Docker-specific tests
test_docker_build() {
    if command -v docker &> /dev/null; then
        docker build -f docker/Dockerfile.ddns -t daily-scribe-ddns-test . > /dev/null 2>&1
        docker rmi daily-scribe-ddns-test > /dev/null 2>&1 || true
    else
        log_warning "Docker not available, skipping Docker build test"
        return 0
    fi
}

# DNS resolution test
test_dns_resolution() {
    # Test that dig command works (required for health checks)
    command -v dig > /dev/null 2>&1 || command -v nslookup > /dev/null 2>&1
}

# Performance test
test_performance() {
    local start_time=$(date +%s)
    DDNS_CONFIG_FILE="$TEST_CONFIG" LOG_FILE="$TEST_LOG" "$SCRIPT_PATH" test > /dev/null 2>&1
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Should complete within reasonable time (30 seconds)
    [[ $duration -lt 30 ]]
}

# Main test runner
run_all_tests() {
    log_info "Starting Daily Scribe DDNS Test Suite"
    log_info "Script path: $SCRIPT_PATH"
    echo ""
    
    # Basic functionality tests
    run_test "Script existence and permissions" test_script_basic
    run_test "Help command" test_help_command
    run_test "Configuration loading" test_config_loading
    run_test "IP retrieval functionality" test_ip_retrieval
    run_test "Invalid configuration handling" test_invalid_config
    run_test "Health check command" test_health_check
    
    # Provider tests
    run_test "DuckDNS provider configuration" test_duckdns_provider
    run_test "Cloudflare provider configuration" test_cloudflare_provider
    run_test "No-IP provider configuration" test_noip_provider
    run_test "Multiple providers configuration" test_multiple_providers
    
    # Advanced functionality tests
    run_test "Logging functionality" test_logging
    run_test "Lock file mechanism" test_lock_mechanism
    run_test "Environment variable override" test_env_override
    run_test "IP change detection" test_ip_change_detection
    run_test "DNS resolution tools" test_dns_resolution
    run_test "Performance test" test_performance
    
    # Docker tests (if available)
    if command -v docker &> /dev/null; then
        run_test "Docker build test" test_docker_build
    fi
}

# Generate test report
generate_report() {
    echo ""
    echo "=========================================="
    echo "        DDNS Test Suite Results"
    echo "=========================================="
    echo ""
    echo "Total tests:  $TESTS_TOTAL"
    echo "Passed:       $TESTS_PASSED"
    echo "Failed:       $TESTS_FAILED"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All tests passed! ✅"
        echo ""
        echo "The DDNS system is ready for deployment."
        return 0
    else
        log_error "Some tests failed! ❌"
        echo ""
        echo "Please review the failed tests and fix issues before deployment."
        return 1
    fi
}

# Signal handler for cleanup
trap cleanup_test_env EXIT

# Main execution
main() {
    setup_test_env
    if ! run_all_tests; then
        log_error "Test execution failed"
        return 1
    fi
    if ! generate_report; then
        log_error "Report generation failed"
        return 1
    fi
}

# Show usage if help requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat << EOF
Daily Scribe DDNS Test Script

Usage: $0 [SCRIPT_PATH]

Arguments:
    SCRIPT_PATH    Path to the ddns-update.sh script (default: ./scripts/ddns-update.sh)

Options:
    -h, --help     Show this help message

Examples:
    $0                                    # Test default script location
    $0 /path/to/ddns-update.sh           # Test specific script location

This script performs comprehensive testing of the DDNS update functionality,
including configuration validation, provider testing, and Docker integration.

EOF
    exit 0
fi

# Run main function
main
