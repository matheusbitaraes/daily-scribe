#!/bin/bash

# Daily Scribe - Dynamic DNS Update Script
# Automatically updates DDNS service with current public IP address
# Supports multiple DDNS providers for redundancy

set -euo pipefail

# Configuration
DDNS_CONFIG_FILE="${DDNS_CONFIG_FILE:-/etc/daily-scribe/ddns.conf}"
LOG_FILE="${LOG_FILE:-/var/log/daily-scribe/ddns.log}"
PID_FILE="/var/run/ddns-update.pid"
LOCK_FILE="/var/lock/ddns-update.lock"

# Use local directories if system directories are not writable (development mode)
if [[ ! -w "$(dirname "$LOG_FILE")" ]] 2>/dev/null; then
    LOG_FILE="${PWD}/logs/ddns.log"
fi

if [[ ! -w "$(dirname "$PID_FILE")" ]] 2>/dev/null; then
    PID_FILE="${PWD}/logs/ddns-update.pid"
fi

if [[ ! -w "$(dirname "$LOCK_FILE")" ]] 2>/dev/null; then
    LOCK_FILE="${PWD}/logs/ddns-update.lock"
fi

# Default configuration values
DEFAULT_UPDATE_INTERVAL=300  # 5 minutes
DEFAULT_MAX_RETRIES=3
DEFAULT_TIMEOUT=30
DEFAULT_IP_CHECK_URLS=(
    "https://ipv4.icanhazip.com"
    "https://api.ipify.org"
    "https://checkip.amazonaws.com"
    "https://ipinfo.io/ip"
)

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
    
    # Also log to syslog if available
    if command -v logger &> /dev/null; then
        logger -t "ddns-update" "[$level] $message"
    fi
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    cleanup
    exit 1
}

# Cleanup function
cleanup() {
    rm -f "$PID_FILE" "$LOCK_FILE"
}

# Trap signals for graceful shutdown
trap cleanup EXIT INT TERM

# Check if script is already running
check_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local existing_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
            log "INFO" "DDNS update script already running (PID: $existing_pid)"
            exit 0
        else
            log "WARN" "Stale lock file found, removing"
            rm -f "$LOCK_FILE"
        fi
    fi
    
    echo $$ > "$LOCK_FILE"
    echo $$ > "$PID_FILE"
}

# Load configuration
load_config() {
    if [[ -f "$DDNS_CONFIG_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$DDNS_CONFIG_FILE"
        log "INFO" "Loaded configuration from $DDNS_CONFIG_FILE"
    else
        log "WARN" "Configuration file not found: $DDNS_CONFIG_FILE"
        log "INFO" "Using default configuration"
    fi
    
    # Set defaults if not configured
    UPDATE_INTERVAL="${UPDATE_INTERVAL:-$DEFAULT_UPDATE_INTERVAL}"
    MAX_RETRIES="${MAX_RETRIES:-$DEFAULT_MAX_RETRIES}"
    TIMEOUT="${TIMEOUT:-$DEFAULT_TIMEOUT}"
    IP_CHECK_URLS=("${IP_CHECK_URLS[@]:-${DEFAULT_IP_CHECK_URLS[@]}}")
    
    # Validate required configuration
    if [[ -z "${DDNS_PROVIDERS:-}" ]]; then
        error_exit "No DDNS providers configured. Please set DDNS_PROVIDERS in config file."
    fi
}

# Get current public IP address
get_public_ip() {
    local ip=""
    local url=""
    
    for url in "${IP_CHECK_URLS[@]}"; do
        log "DEBUG" "Checking IP from: $url"
        
        if ip=$(curl -s --max-time "$TIMEOUT" --connect-timeout 10 "$url" 2>/dev/null); then
            # Validate IP format
            if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                # Additional validation for valid IP ranges
                IFS='.' read -ra ADDR <<< "$ip"
                local valid=true
                for i in "${ADDR[@]}"; do
                    if (( i > 255 )); then
                        valid=false
                        break
                    fi
                done
                
                if $valid; then
                    log "DEBUG" "Retrieved IP: $ip from $url"
                    echo "$ip"
                    return 0
                fi
            fi
        fi
        
        log "WARN" "Failed to get IP from $url"
    done
    
    error_exit "Failed to retrieve public IP address from any source"
}

# Update DuckDNS
update_duckdns() {
    local domain="$1"
    local token="$2"
    local ip="$3"
    
    local url="https://www.duckdns.org/update?domains=${domain}&token=${token}&ip=${ip}"
    local response
    
    response=$(curl -s --max-time "$TIMEOUT" --connect-timeout 10 "$url" 2>/dev/null || echo "FAILED")
    
    if [[ "$response" == "OK" ]]; then
        log "INFO" "DuckDNS update successful for $domain.duckdns.org"
        return 0
    else
        log "ERROR" "DuckDNS update failed for $domain.duckdns.org: $response"
        return 1
    fi
}

# Update Cloudflare DNS
update_cloudflare() {
    local zone_id="$1"
    local record_id="$2"
    local api_token="$3"
    local domain="$4"
    local ip="$5"
    
    local url="https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}"
    local data='{"type":"A","name":"'"$domain"'","content":"'"$ip"'","ttl":300}'
    local response
    
    response=$(curl -s --max-time "$TIMEOUT" --connect-timeout 10 \
        -X PUT "$url" \
        -H "Authorization: Bearer $api_token" \
        -H "Content-Type: application/json" \
        --data "$data" 2>/dev/null || echo '{"success":false}')
    
    if echo "$response" | grep -q '"success":true'; then
        log "INFO" "Cloudflare DNS update successful for $domain"
        return 0
    else
        log "ERROR" "Cloudflare DNS update failed for $domain: $response"
        return 1
    fi
}

# Update No-IP
update_noip() {
    local hostname="$1"
    local username="$2"
    local password="$3"
    local ip="$4"
    
    local url="https://dynupdate.no-ip.com/nic/update?hostname=${hostname}&myip=${ip}"
    local response
    
    response=$(curl -s --max-time "$TIMEOUT" --connect-timeout 10 \
        -u "${username}:${password}" \
        "$url" 2>/dev/null || echo "FAILED")
    
    if [[ "$response" == good* ]] || [[ "$response" == nochg* ]]; then
        log "INFO" "No-IP update successful for $hostname: $response"
        return 0
    else
        log "ERROR" "No-IP update failed for $hostname: $response"
        return 1
    fi
}

# Update all configured DDNS providers
update_ddns_providers() {
    local current_ip="$1"
    local success_count=0
    local total_count=0
    
    # Parse and update each provider
    IFS=',' read -ra PROVIDERS <<< "$DDNS_PROVIDERS"
    
    for provider_config in "${PROVIDERS[@]}"; do
        IFS=':' read -ra CONFIG <<< "$provider_config"
        local provider="${CONFIG[0]}"
        
        ((total_count++))
        
        case "$provider" in
            "duckdns")
                if [[ ${#CONFIG[@]} -ge 3 ]]; then
                    if update_duckdns "${CONFIG[1]}" "${CONFIG[2]}" "$current_ip"; then
                        ((success_count++))
                    fi
                else
                    log "ERROR" "Invalid DuckDNS configuration: $provider_config"
                fi
                ;;
            "cloudflare")
                if [[ ${#CONFIG[@]} -ge 5 ]]; then
                    if update_cloudflare "${CONFIG[1]}" "${CONFIG[2]}" "${CONFIG[3]}" "${CONFIG[4]}" "$current_ip"; then
                        ((success_count++))
                    fi
                else
                    log "ERROR" "Invalid Cloudflare configuration: $provider_config"
                fi
                ;;
            "noip")
                if [[ ${#CONFIG[@]} -ge 4 ]]; then
                    if update_noip "${CONFIG[1]}" "${CONFIG[2]}" "${CONFIG[3]}" "$current_ip"; then
                        ((success_count++))
                    fi
                else
                    log "ERROR" "Invalid No-IP configuration: $provider_config"
                fi
                ;;
            *)
                log "ERROR" "Unknown DDNS provider: $provider"
                ;;
        esac
    done
    
    log "INFO" "DDNS update completed: $success_count/$total_count providers successful"
    
    if [[ $success_count -eq 0 ]]; then
        return 1
    fi
    
    return 0
}

# Check if IP has changed since last update
check_ip_change() {
    local current_ip="$1"
    local cache_dir="/var/cache/daily-scribe"
    if [[ ! -w "/var/cache" ]] 2>/dev/null; then
        cache_dir="${PWD}/cache/daily-scribe"
    fi
    local last_ip_file="$cache_dir/last_ip"
    local last_ip=""
    
    if [[ -f "$last_ip_file" ]]; then
        last_ip=$(cat "$last_ip_file" 2>/dev/null || echo "")
    fi
    
    if [[ "$current_ip" == "$last_ip" ]]; then
        log "DEBUG" "IP address unchanged: $current_ip"
        return 1  # No change
    else
        log "INFO" "IP address changed: $last_ip -> $current_ip"
        mkdir -p "$(dirname "$last_ip_file")"
        echo "$current_ip" > "$last_ip_file"
        return 0  # Changed
    fi
}

# Main update function
perform_update() {
    local current_ip
    local retry_count=0
    
    log "INFO" "Starting DDNS update check"
    
    # Get current public IP
    current_ip=$(get_public_ip)
    
    # Check if IP has changed (unless forced)
    if [[ "${FORCE_UPDATE:-false}" != "true" ]] && ! check_ip_change "$current_ip"; then
        log "DEBUG" "No IP change detected, skipping update"
        return 0
    fi
    
    # Update DDNS providers with retries
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        if update_ddns_providers "$current_ip"; then
            log "INFO" "DDNS update successful on attempt $((retry_count + 1))"
            return 0
        fi
        
        ((retry_count++))
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            local wait_time=$((retry_count * 30))
            log "WARN" "DDNS update failed, retrying in ${wait_time}s (attempt $retry_count/$MAX_RETRIES)"
            sleep "$wait_time"
        fi
    done
    
    error_exit "DDNS update failed after $MAX_RETRIES attempts"
}

# Daemon mode function
run_daemon() {
    log "INFO" "Starting DDNS update daemon (interval: ${UPDATE_INTERVAL}s)"
    
    while true; do
        perform_update || log "ERROR" "Update cycle failed"
        sleep "$UPDATE_INTERVAL"
    done
}

# Health check function
health_check() {
    local current_ip
    local check_results=()
    
    echo "DDNS Health Check Report"
    echo "========================"
    echo "Timestamp: $(date)"
    echo ""
    
    # Check if we can get public IP
    if current_ip=$(get_public_ip 2>/dev/null); then
        echo "✓ Public IP retrieval: SUCCESS ($current_ip)"
    else
        echo "✗ Public IP retrieval: FAILED"
        return 1
    fi
    
    # Check each DDNS provider
    echo ""
    echo "DDNS Provider Status:"
    
    IFS=',' read -ra PROVIDERS <<< "$DDNS_PROVIDERS"
    for provider_config in "${PROVIDERS[@]}"; do
        IFS=':' read -ra CONFIG <<< "$provider_config"
        local provider="${CONFIG[0]}"
        
        case "$provider" in
            "duckdns")
                local domain="${CONFIG[1]}.duckdns.org"
                local resolved_ip=$(dig +short "$domain" @8.8.8.8 2>/dev/null || echo "FAILED")
                if [[ "$resolved_ip" == "$current_ip" ]]; then
                    echo "✓ $provider ($domain): IP matches ($resolved_ip)"
                else
                    echo "✗ $provider ($domain): IP mismatch (resolved: $resolved_ip, actual: $current_ip)"
                fi
                ;;
            "cloudflare"|"noip")
                local domain="${CONFIG[1]}"
                local resolved_ip=$(dig +short "$domain" @8.8.8.8 2>/dev/null || echo "FAILED")
                if [[ "$resolved_ip" == "$current_ip" ]]; then
                    echo "✓ $provider ($domain): IP matches ($resolved_ip)"
                else
                    echo "✗ $provider ($domain): IP mismatch (resolved: $resolved_ip, actual: $current_ip)"
                fi
                ;;
        esac
    done
    
    echo ""
    echo "Log file location: $LOG_FILE"
    echo "Configuration file: $DDNS_CONFIG_FILE"
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Daily Scribe Dynamic DNS Update Script

COMMANDS:
    update          Perform a single DDNS update (default)
    daemon          Run in daemon mode with periodic updates
    health          Perform health check and show status
    test            Test configuration without updating
    help            Show this help message

OPTIONS:
    -c, --config FILE    Configuration file path (default: $DDNS_CONFIG_FILE)
    -l, --log FILE       Log file path (default: $LOG_FILE)
    -f, --force          Force update even if IP hasn't changed
    -v, --verbose        Enable verbose logging (DEBUG level)
    -q, --quiet          Quiet mode (ERROR level only)

CONFIGURATION:
    Create $DDNS_CONFIG_FILE with the following variables:

    # Update interval for daemon mode (seconds)
    UPDATE_INTERVAL=300

    # Maximum retry attempts
    MAX_RETRIES=3

    # HTTP request timeout (seconds)
    TIMEOUT=30

    # DDNS providers (comma-separated list)
    # Format: provider:param1:param2:...
    DDNS_PROVIDERS="duckdns:mydomain:mytoken,cloudflare:zone_id:record_id:api_token:domain.example.com"

    # Custom IP check URLs (optional)
    IP_CHECK_URLS=("https://ipv4.icanhazip.com" "https://api.ipify.org")

EXAMPLES:
    # Single update
    $0 update

    # Run in daemon mode
    $0 daemon

    # Health check
    $0 health

    # Test with custom config
    $0 -c /path/to/config test

SUPPORTED PROVIDERS:
    - DuckDNS: duckdns:domain:token
    - Cloudflare: cloudflare:zone_id:record_id:api_token:domain
    - No-IP: noip:hostname:username:password

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--config)
                DDNS_CONFIG_FILE="$2"
                shift 2
                ;;
            -l|--log)
                LOG_FILE="$2"
                shift 2
                ;;
            -f|--force)
                FORCE_UPDATE="true"
                shift
                ;;
            -v|--verbose)
                LOG_LEVEL="DEBUG"
                shift
                ;;
            -q|--quiet)
                LOG_LEVEL="ERROR"
                shift
                ;;
            update|daemon|health|test|help)
                COMMAND="$1"
                shift
                ;;
            -h|--help)
                COMMAND="help"
                shift
                ;;
            *)
                echo "Unknown option: $1" >&2
                show_usage >&2
                exit 1
                ;;
        esac
    done
    
    COMMAND="${COMMAND:-update}"
}

# Main function
main() {
    local command="$1"
    
    # Create necessary directories
    mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$PID_FILE")"
    
    # Create cache directory (use local if system not writable)
    local cache_dir="/var/cache/daily-scribe"
    if [[ ! -w "/var/cache" ]] 2>/dev/null; then
        cache_dir="${PWD}/cache/daily-scribe"
    fi
    mkdir -p "$cache_dir"
    
    case "$command" in
        "update")
            check_lock
            load_config
            perform_update
            ;;
        "daemon")
            check_lock
            load_config
            run_daemon
            ;;
        "health")
            load_config
            health_check
            ;;
        "test")
            load_config
            log "INFO" "Configuration test - providers: $DDNS_PROVIDERS"
            local test_ip=$(get_public_ip)
            log "INFO" "Current public IP: $test_ip"
            log "INFO" "Configuration test completed successfully"
            ;;
        "help")
            show_usage
            ;;
        *)
            echo "Unknown command: $command" >&2
            show_usage >&2
            exit 1
            ;;
    esac
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_args "$@"
    main "$COMMAND"
fi
