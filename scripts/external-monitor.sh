#!/bin/bash

# External monitoring integration script
# Configures external monitoring services

set -euo pipefail

# Load environment variables
if [[ -f ".env" ]]; then
    source .env
fi

# UptimeRobot configuration
setup_uptimerobot() {
    if [[ -n "${UPTIMEROBOT_API_KEY:-}" ]] && [[ -n "${UPTIMEROBOT_MONITOR_URL:-}" ]]; then
        echo "Configuring UptimeRobot monitor..."
        
        # Create monitor via API
        curl -X POST "https://api.uptimerobot.com/v2/newMonitor" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "api_key=${UPTIMEROBOT_API_KEY}" \
            -d "format=json" \
            -d "type=1" \
            -d "url=${UPTIMEROBOT_MONITOR_URL}" \
            -d "friendly_name=Daily Scribe Health Check" \
            -d "interval=300" \
            -d "timeout=30" \
            -d "alert_contacts=${UPTIMEROBOT_ALERT_CONTACTS:-}"
    else
        echo "UptimeRobot configuration not found in environment"
    fi
}

# Healthchecks.io configuration
setup_healthchecks() {
    if [[ -n "${HEALTHCHECKS_UUID:-}" ]]; then
        echo "Configuring Healthchecks.io..."
        
        # Test ping
        curl -fsS -m 10 --retry 5 "https://hc-ping.com/${HEALTHCHECKS_UUID}/start"
        echo "Healthchecks.io configured successfully"
    else
        echo "Healthchecks.io configuration not found"
    fi
}

# Main execution
case "${1:-all}" in
    "uptimerobot")
        setup_uptimerobot
        ;;
    "healthchecks")
        setup_healthchecks
        ;;
    "all")
        setup_uptimerobot
        setup_healthchecks
        ;;
    *)
        echo "Usage: $0 [uptimerobot|healthchecks|all]"
        exit 1
        ;;
esac
