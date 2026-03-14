#!/usr/bin/env bash
# Emergency disk cleanup for Daily Scribe when "No space left on device"
# Run from project root: ./scripts/emergency-disk-cleanup.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Daily Scribe Emergency Disk Cleanup ==="

# Run inside cron container (has the cleanup scripts)
if docker-compose ps cron 2>/dev/null | grep -q Up; then
    echo "Running disk cleanup in cron container..."
    docker-compose exec -T cron python /app/disk_cleanup_only.py || {
        echo "WARNING: Cleanup script failed. Trying manual steps..."
    }
else
    echo "Cron container not running. Try: docker-compose up -d cron"
    echo "Or run manually: python cron/disk_cleanup_only.py (with DB_PATH and data mounted)"
    exit 1
fi

echo ""
echo "Current disk usage:"
df -h . 2>/dev/null || df -h
echo ""
echo "Data directory size:"
du -sh ./data 2>/dev/null || echo "  (data dir not found)"
