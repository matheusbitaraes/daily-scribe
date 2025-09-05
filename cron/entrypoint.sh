#!/bin/bash

# Daily Scribe Cron Container Entrypoint
# This script initializes the cron environment and handles graceful shutdown

set -e

# Function to handle graceful shutdown
shutdown_handler() {
    echo "$(date): Received shutdown signal, stopping cron jobs gracefully..."
    
    # Kill supercronic if it's running
    if [ ! -z "$SUPERCRONIC_PID" ]; then
        kill -TERM "$SUPERCRONIC_PID" 2>/dev/null || true
        wait "$SUPERCRONIC_PID" 2>/dev/null || true
    fi
    
    echo "$(date): Cron container stopped gracefully"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap shutdown_handler SIGTERM SIGINT

# Create log directory if it doesn't exist
mkdir -p /var/log/cron

# Set proper environment variables for cron jobs
# These will be available to all cron jobs
export PATH="/opt/venv/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONPATH="/app/src:/app"

# Ensure we're using the virtual environment
source /opt/venv/bin/activate

# Load environment variables from .env file if it exists
if [ -f /app/.env ]; then
    echo "$(date): Loading environment variables from .env file"
    export $(grep -v '^#' /app/.env | xargs)
fi

# Set default database path if not specified
export DB_PATH="${DB_PATH:-/data/digest_history.db}"
export DB_TIMEOUT="${DB_TIMEOUT:-30}"

# Ensure data directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Log startup information
echo "$(date): Starting Daily Scribe cron container"
echo "$(date): Database path: $DB_PATH"
echo "$(date): Database timeout: $DB_TIMEOUT"
echo "$(date): Python path: $PYTHONPATH"

# Validate that the application is working
echo "$(date): Validating application setup..."
cd /app

# Test that we can import the main module
echo "$(date): Testing main module import..."
if ! python -c "import sys; sys.path.insert(0, '/app/src'); import main; print('Main module imported successfully')" 2>&1; then
    echo "$(date): ERROR: Cannot import main application module"
    echo "$(date): Python path: $PYTHONPATH"
    echo "$(date): Working directory: $(pwd)"
    echo "$(date): Available files in /app/src:"
    ls -la /app/src/ || echo "src directory not found"
    
    # Try to get more detailed error information
    echo "$(date): Detailed import error:"
    python -c "import sys; sys.path.insert(0, '/app/src'); import main" 2>&1 || true
    exit 1
fi

# Test database connectivity
if ! python -c "
import sys
sys.path.insert(0, '/app/src')
from components.database import DatabaseService
db = DatabaseService()
with db._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    assert result[0] == 1
print('Database connection test passed')
" 2>/dev/null; then
    echo "$(date): ERROR: Database connection test failed"
    exit 1
fi

echo "$(date): Application validation completed successfully"

# Start supercronic with the crontab
echo "$(date): Starting cron scheduler..."
echo "$(date): Cron schedule:"
cat /app/crontab

# Start supercronic in the background
supercronic /app/crontab &
SUPERCRONIC_PID=$!

echo "$(date): Supercronic started with PID $SUPERCRONIC_PID"
echo "$(date): Cron container is ready and waiting for scheduled tasks"

# Wait for supercronic to exit (keeps the container running)
wait "$SUPERCRONIC_PID"

# If we reach here, supercronic exited unexpectedly
echo "$(date): Supercronic exited unexpectedly"
exit 1
