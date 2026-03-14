#!/usr/bin/env python3
"""
Daily Scribe: Lightweight Disk Cleanup (no backup)

Runs cleanup + VACUUM without creating a backup. Use for:
- More frequent runs (every 6-12 hours) to prevent disk filling up
- Emergency recovery when disk is full and backup would fail

Operations (in order):
1. Remove old backup files
2. Delete old articles/sent_articles -> skipped for now
3. WAL checkpoint
4. VACUUM to reclaim space
"""

import sys
from pathlib import Path

# Ensure /app is in path for daily_cleanup_and_backup import (when run from cron container)
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

from utils.logging_config import setup_cron_logging
import logging

setup_cron_logging()
logger = logging.getLogger(__name__)

# Import cleanup functions from the main script (must be in same dir, e.g. /app)
from daily_cleanup_and_backup import (
    DB_PATH,
    BACKUP_DIR,
    RETENTION_DAYS,
    BACKUP_RETENTION_DAYS,
    cleanup_old_backups,
    cleanup_old_data,
    checkpoint_wal,
    vacuum_database,
)


def main() -> int:
    """Run cleanup only (no backup)."""
    exit_code = 0
    try:
        logger.info("Starting disk cleanup (no backup)")

        cleanup_old_backups(BACKUP_DIR, retention_days=BACKUP_RETENTION_DAYS)
        #cleanup_old_data(DB_PATH, RETENTION_DAYS)
        checkpoint_wal(DB_PATH)
        vacuum_database(DB_PATH)

        logger.info("Disk cleanup completed successfully")
    except Exception as e:
        logger.error(f"Disk cleanup failed: {e}")
        exit_code = 1

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
