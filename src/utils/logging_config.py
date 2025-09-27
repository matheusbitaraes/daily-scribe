"""
Centralized logging configuration for Daily Scribe application.

This module provides standardized logging setup across all components
of the Daily Scribe application to ensure consistent log formatting,
levels, and output handling.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Union


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    include_console: bool = True,
    include_file: bool = True,
    force_override: bool = True
) -> None:
    """
    Configure logging for the application with standardized format and handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, uses LOG_LEVEL environment variable or defaults to INFO.
        log_file: Path to log file. If None, uses a default based on the calling module.
        include_console: Whether to include console (stdout) logging handler.
        include_file: Whether to include file logging handler.
        force_override: Whether to force override existing logging configuration.
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Validate log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Create handlers list
    handlers: List[logging.Handler] = []
    
    # Add console handler if requested
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        handlers.append(console_handler)
    
    # Add file handler if requested
    if include_file:
        if log_file is None:
            # Default log file name based on application component
            log_file = 'daily-scribe.log'
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)
    
    # Configure logging with standardized format
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=force_override  # Override any existing configuration
    )


def get_logger(name: str, setup_if_needed: bool = True) -> logging.Logger:
    """
    Get a logger instance with optional automatic setup.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        setup_if_needed: Whether to automatically call setup_logging if no handlers exist
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If no handlers are configured and setup is requested, configure logging
    if setup_if_needed and not logger.handlers and not logging.getLogger().handlers:
        setup_logging()
    
    return logger


def setup_api_logging() -> None:
    """Configure logging specifically for the FastAPI API application."""
    setup_logging(
        log_file='api.log',
        include_console=True,
        include_file=True
    )


def setup_cli_logging() -> None:
    """Configure logging specifically for CLI commands (main.py)."""
    setup_logging(
        log_file='digest.log',
        include_console=True,
        include_file=True
    )


def setup_cron_logging() -> None:
    """Configure logging specifically for cron jobs and background tasks."""
    setup_logging(
        log_file='cron.log',
        include_console=True,
        include_file=True
    )


def setup_migration_logging() -> None:
    """Configure logging specifically for database migrations."""
    setup_logging(
        log_file='migrations.log',
        include_console=True,
        include_file=True
    )


# Convenience function for backward compatibility
def configure_logging(level: str = 'INFO') -> None:
    """
    Legacy function for backward compatibility.
    
    Args:
        level: Logging level
    """
    setup_logging(log_level=level)