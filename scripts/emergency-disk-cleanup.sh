#!/usr/bin/env bash
# Emergency disk cleanup for Daily Scribe when "No space left on device"
# Run from project root: ./scripts/emergency-disk-cleanup.sh

set -e
cd "$(dirname "$0")/.."

# Use explicit compose files to avoid docker-compose.override.yml (e.g. broken litestream)
if [[ -f docker-compose.elasticsearch.yml ]]; then
    COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.elasticsearch.yml"
else
    COMPOSE_CMD="docker-compose -f docker-compose.yml"
fi

echo "=== Daily Scribe Emergency Disk Cleanup ==="

# Run inside cron container (has the cleanup scripts)
if $COMPOSE_CMD ps cron 2>/dev/null | grep -q Up; then
    echo "Running disk cleanup in cron container..."
    $COMPOSE_CMD exec -T cron python /app/disk_cleanup_only.py || {
        echo "WARNING: Cleanup script failed. Trying manual steps..."
    }
else
    echo "Cron container not running."
    echo ""
    echo "Start it with (avoids override with broken litestream):"
    echo "  $COMPOSE_CMD up -d cron"
    echo ""
    echo "Or without Elasticsearch:"
    echo "  docker-compose -f docker-compose.yml up -d cron"
    exit 1
fi

echo ""
echo "Current disk usage:"
df -h . 2>/dev/null || df -h
echo ""
echo "Data directory size:"
du -sh ./data 2>/dev/null || echo "  (data dir not found)"
