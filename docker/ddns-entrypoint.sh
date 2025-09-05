#!/bin/bash

# Daily Scribe DDNS Container Entrypoint
set -euo pipefail

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ENTRYPOINT] $*"
}

# Signal handlers for graceful shutdown
shutdown_handler() {
    log "Received shutdown signal, stopping DDNS service..."
    if [[ -n "${DDNS_PID:-}" ]]; then
        kill -TERM "$DDNS_PID" 2>/dev/null || true
        wait "$DDNS_PID" 2>/dev/null || true
    fi
    log "DDNS service stopped"
    exit 0
}

# Set up signal traps
trap shutdown_handler SIGTERM SIGINT

# Validate environment
validate_environment() {
    if [[ -z "${DDNS_PROVIDERS:-}" ]]; then
        log "ERROR: DDNS_PROVIDERS environment variable is required"
        log "Example: DDNS_PROVIDERS='duckdns:mydomain:mytoken'"
        exit 1
    fi
    
    log "Environment validated successfully"
    log "DDNS Providers: ${DDNS_PROVIDERS}"
    log "Update Interval: ${UPDATE_INTERVAL:-300} seconds"
}

# Create configuration file from environment variables
create_config() {
    local config_file="${DDNS_CONFIG_FILE:-/etc/daily-scribe/ddns.conf}"
    local config_dir=$(dirname "$config_file")
    
    # Create config directory if it doesn't exist
    mkdir -p "$config_dir"
    
    log "Creating configuration file: $config_file"
    
    cat > "$config_file" << EOF
# Generated DDNS configuration from environment variables
# Generated at: $(date)

UPDATE_INTERVAL=${UPDATE_INTERVAL:-300}
MAX_RETRIES=${MAX_RETRIES:-3}
TIMEOUT=${TIMEOUT:-30}
LOG_LEVEL=${LOG_LEVEL:-INFO}
DDNS_PROVIDERS="${DDNS_PROVIDERS}"
FORCE_UPDATE=${FORCE_UPDATE:-false}

# IP check URLs (using defaults if not specified)
EOF

    if [[ -n "${IP_CHECK_URLS:-}" ]]; then
        echo "IP_CHECK_URLS=(${IP_CHECK_URLS})" >> "$config_file"
    fi
    
    log "Configuration file created successfully"
}

# Wait for network connectivity
wait_for_network() {
    local max_attempts=30
    local attempt=1
    
    log "Waiting for network connectivity..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s --max-time 10 --connect-timeout 5 "https://www.google.com" >/dev/null 2>&1; then
            log "Network connectivity confirmed"
            return 0
        fi
        
        log "Network check attempt $attempt/$max_attempts failed, retrying in 5s..."
        sleep 5
        ((attempt++))
    done
    
    log "ERROR: Failed to establish network connectivity after $max_attempts attempts"
    exit 1
}

# Run initial IP check and update
initial_update() {
    log "Performing initial DDNS update..."
    if /usr/local/bin/ddns-update.sh update; then
        log "Initial DDNS update completed successfully"
    else
        log "WARNING: Initial DDNS update failed, will retry in daemon mode"
    fi
}

# Main function
main() {
    local command="${1:-daemon}"
    
    log "Starting Daily Scribe DDNS service"
    log "Command: $command"
    log "User: $(whoami)"
    log "Working directory: $(pwd)"
    
    # Validate environment and create config
    validate_environment
    create_config
    
    # Wait for network
    wait_for_network
    
    case "$command" in
        "daemon")
            # Perform initial update
            initial_update
            
            # Start daemon mode
            log "Starting DDNS daemon mode..."
            /usr/local/bin/ddns-update.sh daemon &
            DDNS_PID=$!
            
            log "DDNS daemon started with PID: $DDNS_PID"
            
            # Wait for the daemon process
            wait "$DDNS_PID"
            ;;
        "update")
            log "Performing single DDNS update..."
            exec /usr/local/bin/ddns-update.sh update
            ;;
        "health")
            log "Performing health check..."
            exec /usr/local/bin/ddns-update.sh health
            ;;
        "test")
            log "Testing configuration..."
            exec /usr/local/bin/ddns-update.sh test
            ;;
        *)
            log "ERROR: Unknown command: $command"
            log "Supported commands: daemon, update, health, test"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
