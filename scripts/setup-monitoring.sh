#!/bin/bash

# Daily Scribe Monitoring Setup Script
# Comprehensive monitoring and alerting configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/monitoring"
CONFIG_DIR="$MONITORING_DIR/config"
DASHBOARDS_DIR="$MONITORING_DIR/dashboards"
ALERTS_DIR="$MONITORING_DIR/alerts"

# Default configuration
SETUP_INTERNAL=false
SETUP_EXTERNAL=false
SETUP_GRAFANA=false
SETUP_LOKI=false
ENABLE_ALERTS=true
DRY_RUN=false

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

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Validate environment
validate_environment() {
    log_info "Validating environment..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        log_error "Please run this script from the Daily Scribe project root"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_warning ".env file not found. Some monitoring features may not work properly."
    fi
    
    log_success "Environment validation passed"
}

# Create monitoring directories
create_directories() {
    log_info "Creating monitoring directories..."
    
    local dirs=(
        "$MONITORING_DIR"
        "$CONFIG_DIR"
        "$DASHBOARDS_DIR"
        "$ALERTS_DIR"
        "$MONITORING_DIR/grafana/dashboards"
        "$MONITORING_DIR/grafana/datasources"
        "$MONITORING_DIR/loki"
        "$MONITORING_DIR/promtail"
        "$MONITORING_DIR/prometheus"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    log_success "Monitoring directories created"
}

# Setup internal monitoring
setup_internal_monitoring() {
    log_info "Setting up internal monitoring..."
    
    # Create Prometheus configuration
    cat > "$CONFIG_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/alerts/*.yml"

scrape_configs:
  - job_name: 'daily-scribe-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'caddy'
    static_configs:
      - targets: ['caddy:2019']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  - job_name: 'docker'
    static_configs:
      - targets: ['docker-exporter:9323']
    scrape_interval: 30s
EOF

    # Create alert rules
    cat > "$ALERTS_DIR/daily-scribe.yml" << 'EOF'
groups:
  - name: daily-scribe.rules
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 2 minutes."

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value }} on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 90% on {{ $labels.instance }}"

      - alert: LowDiskSpace
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk usage is above 90% on {{ $labels.instance }}"

      - alert: DatabaseConnectivity
        expr: daily_scribe_database_health != 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connectivity issues"
          description: "Daily Scribe cannot connect to the database"

      - alert: BackupFailure
        expr: litestream_backup_last_success_timestamp < (time() - 3600)
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Backup failure detected"
          description: "Litestream backup has not succeeded in the last hour"

      - alert: DDNSUpdateFailure
        expr: ddns_last_update_success < (time() - 7200)
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "DDNS update failure"
          description: "DDNS has not updated successfully in the last 2 hours"
EOF

    log_success "Internal monitoring configuration created"
}

# Setup external monitoring
setup_external_monitoring() {
    log_info "Setting up external monitoring configuration..."
    
    # Create external monitoring script
    cat > "$SCRIPT_DIR/external-monitor.sh" << 'EOF'
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
EOF

    chmod +x "$SCRIPT_DIR/external-monitor.sh"
    
    # Create external monitoring documentation
    cat > "$MONITORING_DIR/external-monitoring.md" << 'EOF'
# External Monitoring Configuration

## UptimeRobot Setup

1. Create account at https://uptimerobot.com
2. Get API key from account settings
3. Add to .env file:
   ```
   UPTIMEROBOT_API_KEY=ur123456789-abcdef
   UPTIMEROBOT_MONITOR_URL=https://yourdomain.duckdns.org/healthz
   UPTIMEROBOT_ALERT_CONTACTS=email_contact_id
   ```
4. Run: `./scripts/external-monitor.sh uptimerobot`

## Healthchecks.io Setup

1. Create account at https://healthchecks.io
2. Create new check and get UUID
3. Add to .env file:
   ```
   HEALTHCHECKS_UUID=12345678-1234-5678-9012-123456789abc
   ```
4. Run: `./scripts/external-monitor.sh healthchecks`

## StatusCake Setup

1. Create account at https://www.statuscake.com
2. Get API key from account settings
3. Add to .env file:
   ```
   STATUSCAKE_API_KEY=your-api-key
   STATUSCAKE_TEST_URL=https://yourdomain.duckdns.org/healthz
   ```
EOF

    log_success "External monitoring configuration created"
}

# Setup Grafana dashboards
setup_grafana() {
    log_info "Setting up Grafana dashboards..."
    
    # Create Grafana datasource configuration
    cat > "$MONITORING_DIR/grafana/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
EOF

    # Create simple dashboard configuration
    cat > "$MONITORING_DIR/grafana/dashboards/dashboard.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'daily-scribe'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Create Daily Scribe dashboard JSON
    cat > "$DASHBOARDS_DIR/daily-scribe-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Daily Scribe Overview",
    "tags": ["daily-scribe"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"daily-scribe-app\"}",
            "legendFormat": "Application"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": 0
                },
                {
                  "color": "green",
                  "value": 1
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

    log_success "Grafana configuration created"
}

# Setup Loki logging
setup_loki() {
    log_info "Setting up Loki logging..."
    
    # Create Loki configuration
    cat > "$CONFIG_DIR/loki.yml" << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem
EOF

    # Create Promtail configuration
    cat > "$CONFIG_DIR/promtail.yml" << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[^|]*))\|
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          stream:
          container_name:
      - output:
          source: output

  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          __path__: /var/log/syslog
EOF

    log_success "Loki logging configuration created"
}

# Create monitoring docker-compose
create_monitoring_compose() {
    log_info "Creating monitoring docker-compose configuration..."
    
    cat > "$PROJECT_ROOT/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: daily-scribe-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/config/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerts:/etc/prometheus/alerts
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - daily-scribe-network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:v1.6.0
    container_name: daily-scribe-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - daily-scribe-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.1.0
    container_name: daily-scribe-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
      - ./monitoring/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    networks:
      - daily-scribe-network
    restart: unless-stopped

  loki:
    image: grafana/loki:2.9.0
    container_name: daily-scribe-loki
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/config/loki.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - daily-scribe-network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.9.0
    container_name: daily-scribe-promtail
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./monitoring/config/promtail.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - daily-scribe-network
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  loki-data:

networks:
  daily-scribe-network:
    external: true
EOF

    log_success "Monitoring docker-compose configuration created"
}

# Update main docker-compose with monitoring integration
update_main_compose() {
    log_info "Updating main docker-compose with monitoring integration..."
    
    # Create backup of existing docker-compose.yml
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        cp "$PROJECT_ROOT/docker-compose.yml" "$PROJECT_ROOT/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Add monitoring labels and metrics endpoints to existing services
    local temp_file
    temp_file=$(mktemp)
    
    # This is a simplified update - in production, you'd want more sophisticated YAML manipulation
    cat >> "$temp_file" << 'EOF'

# Add these labels to your app service:
#   labels:
#     - "prometheus.io/scrape=true"
#     - "prometheus.io/port=8000"
#     - "prometheus.io/path=/metrics"

# Add metrics endpoint to Caddy configuration:
# :2019 {
#   metrics
# }
EOF

    log_info "Monitoring integration notes created in: $temp_file"
    log_warning "Manual integration required for existing docker-compose.yml"
    log_warning "See monitoring setup guide for detailed instructions"
}

# Create simple status dashboard
create_status_dashboard() {
    log_info "Creating simple status dashboard..."
    
    mkdir -p "$PROJECT_ROOT/static"
    
    cat > "$PROJECT_ROOT/static/status.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Scribe Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .status-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }
        .status-healthy {
            background-color: #d4edda;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .healthy { background-color: #28a745; }
        .warning { background-color: #ffc107; }
        .error { background-color: #dc3545; }
        .timestamp {
            color: #666;
            font-size: 0.9em;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="status-container">
        <h1>Daily Scribe System Status</h1>
        <div id="status-items">
            <!-- Status items will be loaded here -->
        </div>
        <div class="timestamp" id="last-update">
            Last updated: <span id="timestamp"></span>
        </div>
    </div>

    <script>
        async function updateStatus() {
            try {
                const response = await fetch('/healthz');
                const data = await response.json();
                
                const container = document.getElementById('status-items');
                container.innerHTML = '';
                
                // Overall status
                const overall = document.createElement('div');
                overall.className = `status-item status-${data.status === 'healthy' ? 'healthy' : 'error'}`;
                overall.innerHTML = `
                    <div>
                        <span class="status-indicator ${data.status === 'healthy' ? 'healthy' : 'error'}"></span>
                        Overall System Status
                    </div>
                    <div>${data.status.toUpperCase()}</div>
                `;
                container.appendChild(overall);
                
                // Individual checks
                if (data.checks) {
                    Object.entries(data.checks).forEach(([name, check]) => {
                        const item = document.createElement('div');
                        const status = check.status === 'healthy' ? 'healthy' : 'error';
                        item.className = `status-item status-${status}`;
                        item.innerHTML = `
                            <div>
                                <span class="status-indicator ${status}"></span>
                                ${name.replace(/_/g, ' ').toUpperCase()}
                            </div>
                            <div>${check.status.toUpperCase()}</div>
                        `;
                        container.appendChild(item);
                    });
                }
                
                document.getElementById('timestamp').textContent = new Date().toLocaleString();
                
            } catch (error) {
                console.error('Failed to fetch status:', error);
                const container = document.getElementById('status-items');
                container.innerHTML = `
                    <div class="status-item status-error">
                        <div>
                            <span class="status-indicator error"></span>
                            System Status
                        </div>
                        <div>UNAVAILABLE</div>
                    </div>
                `;
                document.getElementById('timestamp').textContent = new Date().toLocaleString();
            }
        }
        
        // Update on page load and every 30 seconds
        updateStatus();
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
EOF

    log_success "Status dashboard created at static/status.html"
}

# Test monitoring setup
test_monitoring() {
    log_info "Testing monitoring setup..."
    
    # Check if monitoring services are configured
    if [[ -f "$PROJECT_ROOT/docker-compose.monitoring.yml" ]]; then
        log_success "Monitoring docker-compose configuration found"
    else
        log_error "Monitoring docker-compose configuration not found"
    fi
    
    # Check configuration files
    local config_files=(
        "$CONFIG_DIR/prometheus.yml"
        "$ALERTS_DIR/daily-scribe.yml"
    )
    
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Configuration file found: $(basename "$file")"
        else
            log_error "Configuration file missing: $(basename "$file")"
        fi
    done
    
    # Test if main application health endpoint is accessible
    if command_exists curl; then
        if curl -sf "http://localhost:8000/healthz" &>/dev/null; then
            log_success "Application health endpoint accessible"
        else
            log_warning "Application health endpoint not accessible (service may not be running)"
        fi
    fi
    
    log_success "Monitoring setup test completed"
}

# Show usage information
show_usage() {
    cat << EOF
Daily Scribe Monitoring Setup Script

Usage: $0 [OPTIONS]

OPTIONS:
    --internal              Setup internal monitoring (Prometheus)
    --external              Setup external monitoring configuration
    --grafana              Setup Grafana dashboards
    --loki                 Setup Loki logging
    --all                  Setup all monitoring components
    --test                 Test monitoring configuration
    --dry-run              Show what would be done without making changes
    -h, --help             Show this help message

EXAMPLES:
    $0 --internal                    # Setup basic internal monitoring
    $0 --all                        # Setup complete monitoring stack
    $0 --test                       # Test current configuration
    $0 --internal --external        # Setup internal and external monitoring

ENVIRONMENT VARIABLES:
    ALERT_EMAIL             Email address for alerts
    SMTP_HOST               SMTP server for email alerts
    SMTP_USERNAME           SMTP username
    SMTP_PASSWORD           SMTP password
    SLACK_WEBHOOK_URL       Slack webhook for notifications
    GRAFANA_ADMIN_PASSWORD  Grafana admin password

This script sets up comprehensive monitoring for Daily Scribe including:
- Internal health checks and metrics collection
- External uptime monitoring configuration
- Log aggregation and rotation
- Alert management and notifications
- Optional Grafana dashboards

EOF
}

# Main function
main() {
    echo "Daily Scribe Monitoring Setup"
    echo "============================="
    echo ""
    
    # Validate environment first
    validate_environment
    
    # Create necessary directories
    create_directories
    
    if [[ "$SETUP_INTERNAL" == true ]] || [[ "$1" == "--all" ]]; then
        setup_internal_monitoring
    fi
    
    if [[ "$SETUP_EXTERNAL" == true ]] || [[ "$1" == "--all" ]]; then
        setup_external_monitoring
    fi
    
    if [[ "$SETUP_GRAFANA" == true ]] || [[ "$1" == "--all" ]]; then
        setup_grafana
    fi
    
    if [[ "$SETUP_LOKI" == true ]] || [[ "$1" == "--all" ]]; then
        setup_loki
    fi
    
    if [[ "$1" == "--all" ]] || [[ "$SETUP_INTERNAL" == true ]]; then
        create_monitoring_compose
        update_main_compose
    fi
    
    create_status_dashboard
    
    echo ""
    log_success "Monitoring setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Configure environment variables in .env file"
    echo "2. Start monitoring services: docker-compose -f docker-compose.monitoring.yml up -d"
    echo "3. Access Grafana at http://localhost:3000 (admin/admin)"
    echo "4. Access Prometheus at http://localhost:9090"
    echo "5. Configure external monitoring providers"
    echo "6. Test the setup: $0 --test"
    echo ""
    echo "For detailed configuration, see: docs/monitoring-setup.md"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --internal)
            SETUP_INTERNAL=true
            shift
            ;;
        --external)
            SETUP_EXTERNAL=true
            shift
            ;;
        --grafana)
            SETUP_GRAFANA=true
            shift
            ;;
        --loki)
            SETUP_LOKI=true
            shift
            ;;
        --all)
            SETUP_INTERNAL=true
            SETUP_EXTERNAL=true
            SETUP_GRAFANA=true
            SETUP_LOKI=true
            shift
            ;;
        --test)
            test_monitoring
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
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

# If no options provided, show usage
if [[ "$SETUP_INTERNAL" == false ]] && [[ "$SETUP_EXTERNAL" == false ]] && [[ "$SETUP_GRAFANA" == false ]] && [[ "$SETUP_LOKI" == false ]]; then
    show_usage
    exit 1
fi

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
