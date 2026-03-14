#!/usr/bin/env python3
"""
Daily Scribe: Daily DB Backup and Cleanup Script

This script performs disk-space-aware cleanup and backup:
1. Cleans old backup files FIRST to free space (before any other operations)
2. Removes articles and sent_articles older than retention period
3. Runs SQLite VACUUM to reclaim disk space (DELETE alone does not free space)
4. Optionally creates a timestamped backup (skipped if disk is critically low)

Designed to prevent "No space left on device" errors on constrained VMs.
"""

import os
import shutil
import sqlite3
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the Python path to import utilities
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logging_config import setup_cron_logging

# Configure logging
setup_cron_logging()
logger = logging.getLogger(__name__)

# Configuration constants from environment variables with defaults
DB_PATH = os.getenv('DB_PATH', '/data/digest_history.db')
BACKUP_DIR = os.getenv('BACKUP_DIR', '/data')
BACKUP_PREFIX = os.getenv('BACKUP_PREFIX', 'digest_history_backup')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '3'))
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '3'))
MIN_FREE_SPACE_MB = int(os.getenv('CLEANUP_MIN_FREE_SPACE_MB', '500'))
SKIP_BACKUP_IF_LOW_DISK = os.getenv('SKIP_BACKUP_IF_LOW_DISK', 'true').lower() in ('1', 'true', 'yes')


def get_disk_free_space_mb(path: str) -> float:
    """
    Get free disk space in MB for the partition containing the given path.

    Args:
        path: Any path on the filesystem (e.g. database or backup directory)

    Returns:
        Free space in megabytes, or 0.0 if unavailable
    """
    try:
        stat = shutil.disk_usage(Path(path).resolve())
        return stat.free / (1024 * 1024)
    except OSError as e:
        logger.warning(f"Could not get disk usage for {path}: {e}")
        return 0.0


def vacuum_database(db_path: str) -> None:
    """
    Run SQLite VACUUM to reclaim disk space after deletions.
    SQLite does not free disk space on DELETE; VACUUM rebuilds the file.

    Args:
        db_path: Path to the SQLite database
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    try:
        with sqlite3.connect(db_path, timeout=60.0) as conn:
            conn.execute("VACUUM")
        logger.info("Database VACUUM completed successfully")
    except sqlite3.Error as e:
        logger.error(f"VACUUM failed: {e}")
        raise


def checkpoint_wal(db_path: str) -> None:
    """
    Checkpoint WAL to reduce size of -wal and -shm files.
    Helps prevent WAL from growing unbounded.
    """
    if not os.path.exists(db_path):
        return
    try:
        with sqlite3.connect(db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        logger.debug("WAL checkpoint completed")
    except sqlite3.Error as e:
        logger.warning(f"WAL checkpoint failed (non-fatal): {e}")


def create_database_backup(db_path: str, backup_dir: str) -> str:
    """
    Create a timestamped backup of the database.
    
    Args:
        db_path: Path to the source database file
        backup_dir: Directory where backup will be stored
        
    Returns:
        Path to the created backup file
        
    Raises:
        FileNotFoundError: If source database doesn't exist
        OSError: If backup creation fails
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    # Ensure backup directory exists
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d')
    backup_filename = f"{BACKUP_PREFIX}_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Create backup using SQLite backup API for consistency
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        # Use SQLite's backup API to ensure consistent backup
        source_conn.backup(backup_conn)
        
        backup_conn.close()
        source_conn.close()
        
        logger.info(f"Database backup created successfully: {backup_path}")
        return backup_path
        
    except Exception as e:
        # Clean up partial backup file if creation failed
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise OSError(f"Failed to create database backup: {e}") from e


def cleanup_old_data(db_path: str, retention_days: int) -> dict:
    """
    Remove articles and sent_articles older than the specified retention period.
    
    Args:
        db_path: Path to the database file
        retention_days: Number of days to retain data
        
    Returns:
        Dictionary with cleanup statistics
        
    Raises:
        sqlite3.Error: If database operations fail
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    # Calculate cutoff datetime
    cutoff_datetime = datetime.now() - timedelta(days=retention_days)
    cutoff_str = cutoff_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    stats = {
        'articles_deleted': 0,
        'sent_articles_deleted': 0,
        'cutoff_datetime': cutoff_str
    }
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Count records before deletion for logging
            cursor.execute("SELECT COUNT(*) FROM articles WHERE processed_at < ?", (cutoff_str,))
            articles_to_delete = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sent_articles WHERE sent_at < ?", (cutoff_str,))
            sent_articles_to_delete = cursor.fetchone()[0]
            
            # Delete old articles
            cursor.execute("DELETE FROM articles WHERE processed_at < ?", (cutoff_str,))
            stats['articles_deleted'] = cursor.rowcount
            
            # Delete old sent_articles
            cursor.execute("DELETE FROM sent_articles WHERE sent_at < ?", (cutoff_str,))
            stats['sent_articles_deleted'] = cursor.rowcount
            
            # Commit the transaction
            conn.commit()
            
            logger.info(f"Cleanup completed. Articles deleted: {stats['articles_deleted']}, "
                       f"Sent articles deleted: {stats['sent_articles_deleted']}")
            
            return stats
            
    except sqlite3.Error as e:
        logger.error(f"Database cleanup failed: {e}")
        raise


def cleanup_old_backups(backup_dir: str, retention_days: int = 5) -> int:
    """
    Remove backup files older than the specified retention period.
    
    Args:
        backup_dir: Directory containing backup files
        retention_days: Number of days to retain backup files
        
    Returns:
        Number of backup files deleted
    """
    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return deleted_count
        
        # Find old backup files
        for backup_file in backup_path.glob(f"{BACKUP_PREFIX}_*.db"):
            if backup_file.stat().st_mtime < cutoff_time.timestamp():
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file}")
                except OSError as e:
                    logger.warning(f"Failed to delete backup {backup_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup files")
        
    except Exception as e:
        logger.warning(f"Backup cleanup encountered an error: {e}")
    
    return deleted_count


def main() -> int:
    """
    Main function that orchestrates backup and cleanup operations.
    Order optimized for low-disk scenarios: free space first, then cleanup, then backup.
    """
    exit_code = 0

    try:
        logger.info("Starting daily database backup and cleanup (disk-space-aware)")

        # Step 1: Clean up old backup files FIRST to free space
        try:
            deleted_backups = cleanup_old_backups(BACKUP_DIR, retention_days=BACKUP_RETENTION_DAYS)
            logger.info(f"✓ Backup cleanup completed. Old backups removed: {deleted_backups}")
        except Exception as e:
            logger.warning(f"⚠ Backup cleanup had issues: {e}")

        # Step 2: Clean up old data (articles, sent_articles)
        try:
            cleanup_stats = cleanup_old_data(DB_PATH, RETENTION_DAYS)
            logger.info(
                f"✓ Data cleanup completed. Articles removed: {cleanup_stats['articles_deleted']}, "
                f"Sent articles removed: {cleanup_stats['sent_articles_deleted']}"
            )
        except Exception as e:
            logger.error(f"✗ Data cleanup failed: {e}")
            exit_code = 1

        # Step 3: Checkpoint WAL to reduce -wal file size
        try:
            checkpoint_wal(DB_PATH)
        except Exception as e:
            logger.warning(f"⚠ WAL checkpoint had issues: {e}")

        # Step 4: VACUUM to reclaim disk space (SQLite DELETE does not free space)
        try:
            vacuum_database(DB_PATH)
            logger.info("✓ Database VACUUM completed")
        except Exception as e:
            logger.error(f"✗ Database VACUUM failed: {e}")
            exit_code = 1

        # Step 5: Create backup only if disk has enough free space
        free_mb = get_disk_free_space_mb(BACKUP_DIR)
        db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024) if os.path.exists(DB_PATH) else 0
        skip_backup = False

        if SKIP_BACKUP_IF_LOW_DISK and free_mb < max(MIN_FREE_SPACE_MB, db_size_mb * 2):
            logger.warning(
                f"⚠ Skipping backup: low disk space ({free_mb:.0f} MB free, "
                f"need ~{db_size_mb:.0f} MB). Set SKIP_BACKUP_IF_LOW_DISK=false to force."
            )
            skip_backup = True

        if not skip_backup:
            try:
                backup_path = create_database_backup(DB_PATH, BACKUP_DIR)
                logger.info(f"✓ Database backup created: {backup_path}")
            except Exception as e:
                logger.error(f"✗ Database backup failed: {e}")
                exit_code = 1

        if exit_code == 0:
            logger.info("Daily backup and cleanup completed successfully")
        else:
            logger.error("Daily backup and cleanup completed with errors")

    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        exit_code = 1

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
