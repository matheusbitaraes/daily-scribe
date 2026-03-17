#!/usr/bin/env python3
"""
Daily Scribe: Log Rotation and Cleanup

Performs two operations:
1. Deletes log files older than 7 days
2. Trims any log file larger than 10 MB to its last 2 MB

Extracted into a standalone script because multi-line Python
in crontab entries breaks Supercronic's parser.
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.logging_config import setup_cron_logging

setup_cron_logging()
logger = logging.getLogger(__name__)

LOG_DIR = Path(os.getenv("CRON_LOG_DIR", "/var/log/cron"))
MAX_AGE_DAYS = 7
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
TAIL_KEEP_BYTES = 2 * 1024 * 1024  # 2 MB


def delete_old_logs(log_dir: Path, max_age_days: int) -> int:
    """Delete .log files older than ``max_age_days``."""
    import time

    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    for path in log_dir.glob("*.log"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
                logger.info("Deleted old log: %s", path)
        except OSError as exc:
            logger.warning("Could not delete %s: %s", path, exc)
    return deleted


def trim_large_logs(log_dir: Path, max_size: int, keep_bytes: int) -> int:
    """Trim .log files exceeding ``max_size`` to their last ``keep_bytes``."""
    trimmed = 0
    for path in log_dir.glob("*.log"):
        try:
            size = path.stat().st_size
            if size <= max_size:
                continue
            with open(path, "rb") as fh:
                fh.seek(-keep_bytes, 2)
                tail = fh.read()
            with open(path, "wb") as fh:
                fh.write(tail)
            trimmed += 1
            logger.info("Trimmed %s: %d -> %d bytes", path, size, keep_bytes)
        except OSError as exc:
            logger.warning("Could not trim %s: %s", path, exc)
    return trimmed


def main() -> int:
    """Run log rotation."""
    exit_code = 0
    try:
        logger.info("Starting log rotation in %s", LOG_DIR)
        deleted = delete_old_logs(LOG_DIR, MAX_AGE_DAYS)
        trimmed = trim_large_logs(LOG_DIR, MAX_SIZE_BYTES, TAIL_KEEP_BYTES)
        logger.info(
            "Log rotation complete: %d deleted, %d trimmed", deleted, trimmed
        )
    except Exception as exc:
        logger.error("Log rotation failed: %s", exc)
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    import time as _time

    _start = _time.time()
    _exit_code = main()
    try:
        from cron_metrics import record_job_run

        record_job_run(
            "log-rotation",
            success=_exit_code == 0,
            duration_seconds=_time.time() - _start,
        )
    except Exception as _exc:
        logger.warning("Failed to write cron metrics: %s", _exc)
    sys.exit(_exit_code)
