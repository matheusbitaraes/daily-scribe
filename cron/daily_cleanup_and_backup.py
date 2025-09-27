#!/usr/bin/env python3
"""
Daily Scribe: Daily DB Backup and Cleanup Script

This script performs two main tasks:
1. Creates a timestamped backup of the database in /data
2. Removes articles and sent_articles older than 3 days

Follows best practices from the development guidelines:
- Uses specific exception types
- Implements proper error handling with logging
- Uses type hints for parameters and return values
- Follows PEP 8 style guide
"""

import os
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


def cleanup_old_backups(backup_dir: str, retention_days: int = 7) -> int:
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
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    exit_code = 0
    
    try:
        logger.info("Starting daily database backup and cleanup")
        
        # Step 1: Create database backup
        try:
            backup_path = create_database_backup(DB_PATH, BACKUP_DIR)
            logger.info(f"✓ Database backup created: {backup_path}")
        except Exception as e:
            logger.error(f"✗ Database backup failed: {e}")
            exit_code = 1
        
        # Step 2: Clean up old data
        try:
            cleanup_stats = cleanup_old_data(DB_PATH, RETENTION_DAYS)
            logger.info(f"✓ Data cleanup completed. Articles removed: {cleanup_stats['articles_deleted']}, "
                       f"Sent articles removed: {cleanup_stats['sent_articles_deleted']}")
        except Exception as e:
            logger.error(f"✗ Data cleanup failed: {e}")
            exit_code = 1
        
        # Step 3: Clean up old backup files (keep 7 days of backups)
        try:
            deleted_backups = cleanup_old_backups(BACKUP_DIR, retention_days=7)
            logger.info(f"✓ Backup cleanup completed. Old backups removed: {deleted_backups}")
        except Exception as e:
            logger.warning(f"⚠ Backup cleanup had issues: {e}")
            # Don't fail the whole script for backup cleanup issues
        
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
