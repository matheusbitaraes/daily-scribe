"""
Lightweight Prometheus textfile metrics writer for cron jobs.

Writes a .prom file that node-exporter's textfile collector picks up,
exposing per-job: last success timestamp, last run duration, and run counts.

Usage in cron scripts:
    from cron.cron_metrics import CronJobMetrics

    with CronJobMetrics("my-job-name") as metrics:
        # your job logic here — exceptions are caught and recorded as errors
        do_work()
"""

from __future__ import annotations

import fcntl
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

METRICS_DIR = Path(os.getenv("CRON_METRICS_DIR", "/var/log/cron"))
METRICS_FILE = METRICS_DIR / "cron_metrics.prom"


def _read_existing_metrics() -> dict[str, dict[str, str]]:
    """Parse the existing .prom file into a dict keyed by (metric_name, labels)."""
    metrics: dict[str, dict[str, str]] = {}
    if not METRICS_FILE.exists():
        return metrics

    try:
        lines = METRICS_FILE.read_text().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            brace_open = line.find("{")
            brace_close = line.find("}")
            if brace_open == -1 or brace_close == -1:
                continue
            metric_name = line[:brace_open]
            labels_str = line[brace_open + 1 : brace_close]
            value = line[brace_close + 1 :].strip()
            if metric_name not in metrics:
                metrics[metric_name] = {}
            metrics[metric_name][labels_str] = value
    except OSError as exc:
        logger.warning("Could not read existing metrics file: %s", exc)

    return metrics


def _write_metrics_file(metrics: dict[str, dict[str, str]]) -> None:
    """Write the full metrics dict back to the .prom file atomically."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    for metric_name, label_map in sorted(metrics.items()):
        for labels_str, value in sorted(label_map.items()):
            lines.append(f'{metric_name}{{{labels_str}}} {value}')

    tmp_path = METRICS_FILE.with_suffix(".prom.tmp")
    try:
        tmp_path.write_text("\n".join(lines) + "\n")
        tmp_path.replace(METRICS_FILE)
    except OSError as exc:
        logger.error("Could not write metrics file: %s", exc)
        raise


def _update_job_metrics(
    cronjob: str,
    status: str,
    duration_seconds: float,
    success: bool,
) -> None:
    """Atomically update metrics for one cron job."""
    lock_path = METRICS_DIR / "cron_metrics.lock"
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            metrics = _read_existing_metrics()
            now = time.time()

            _set(metrics, "daily_scribe_cronjob_last_run_timestamp", f'cronjob="{cronjob}"', str(now))
            _set(metrics, "daily_scribe_cronjob_last_duration_seconds", f'cronjob="{cronjob}"', f"{duration_seconds:.3f}")

            if success:
                _set(metrics, "daily_scribe_cronjob_last_success_timestamp", f'cronjob="{cronjob}"', str(now))

            # Increment run counter for the given status
            counter_labels = f'cronjob="{cronjob}",status="{status}"'
            current = float(metrics.get("daily_scribe_cronjob_runs_total", {}).get(counter_labels, "0"))
            _set(metrics, "daily_scribe_cronjob_runs_total", counter_labels, str(int(current) + 1))

            _write_metrics_file(metrics)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _set(metrics: dict, metric_name: str, labels_str: str, value: str) -> None:
    if metric_name not in metrics:
        metrics[metric_name] = {}
    metrics[metric_name][labels_str] = value


def record_job_run(cronjob: str, success: bool, duration_seconds: float) -> None:
    """Simple one-shot call to record a completed job run.

    Intended for scripts that use exit codes rather than exceptions::

        exit_code = main()
        record_job_run("db-backup-cleanup", success=exit_code == 0, duration_seconds=elapsed)

    Args:
        cronjob: Logical job name matching the label in Prometheus alerts.
        success: Whether the job completed without errors.
        duration_seconds: How long the job took to run.
    """
    status = "success" if success else "error"
    try:
        _update_job_metrics(
            cronjob=cronjob,
            status=status,
            duration_seconds=duration_seconds,
            success=success,
        )
    except Exception as exc:
        logger.warning("Failed to write cron metrics for %s: %s", cronjob, exc)


class CronJobMetrics:
    """Context manager that records success/failure metrics around a cron job body.

    Args:
        cronjob: The logical name of the cron job (must match the label used in alerts).

    Example::

        with CronJobMetrics("full-run"):
            run_full_pipeline()
    """

    def __init__(self, cronjob: str) -> None:
        self.cronjob = cronjob
        self._start: Optional[float] = None

    def __enter__(self) -> "CronJobMetrics":
        self._start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration = time.time() - (self._start or time.time())
        success = exc_type is None
        status = "success" if success else "error"

        try:
            _update_job_metrics(
                cronjob=self.cronjob,
                status=status,
                duration_seconds=duration,
                success=success,
            )
        except Exception as exc:
            logger.warning("Failed to write cron metrics for %s: %s", self.cronjob, exc)

        # Do not suppress the original exception
        return False
