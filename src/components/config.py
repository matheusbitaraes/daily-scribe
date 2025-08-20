"""
Configuration loader for Daily Scribe application.

This module handles loading and validating the application configuration
from a JSON file, including RSS feeds and email settings.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Email configuration settings."""
    to: str
    smtp_server: str
    smtp_port: int
    username: str


@dataclass
class ScheduleConfig:
    """Schedule configuration settings."""
    hour: int
    minute: int


@dataclass
class AppConfig:
    """Main application configuration."""
    rss_feeds: List[str]
    email: EmailConfig
    schedule: ScheduleConfig


class ConfigLoader:
    """Handles loading and validation of application configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the configuration file. If None, defaults to 'config.json' in the current directory.
        """
        self.config_path = config_path or "config.json"
    
    def load_config(self) -> AppConfig:
        """
        Load and validate the configuration file.
        
        Returns:
            AppConfig: Validated configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is malformed
            ValueError: If config validation fails
        """
        # Check if config file exists
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file '{self.config_path}' not found. "
                f"Please create a config.json file based on config.json.example"
            )
        
        # Read and parse JSON
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Configuration file '{self.config_path}' contains invalid JSON: {e}",
                e.doc,
                e.pos
            )
        
        # Validate and return config
        return self._validate_config(config_data)
    
    def _validate_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """
        Validate the configuration data and return an AppConfig object.
        
        Args:
            config_data: Raw configuration data from JSON
            
        Returns:
            AppConfig: Validated configuration object
            
        Raises:
            ValueError: If validation fails
        """
        # Validate RSS feeds
        if 'rss_feeds' not in config_data:
            raise ValueError("Configuration missing 'rss_feeds' section")
        
        rss_feeds = config_data['rss_feeds']
        if not isinstance(rss_feeds, list) or len(rss_feeds) == 0:
            raise ValueError("'rss_feeds' must be a non-empty list")
        
        for feed_url in rss_feeds:
            if not isinstance(feed_url, str) or not feed_url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid RSS feed URL: {feed_url}")
        
        # Validate email configuration
        if 'email' not in config_data:
            raise ValueError("Configuration missing 'email' section")
        
        email_data = config_data['email']
        required_email_fields = ['to', 'smtp_server', 'smtp_port', 'username']
        for field in required_email_fields:
            if field not in email_data:
                raise ValueError(f"Email configuration missing '{field}' field")
        
        if not isinstance(email_data['smtp_port'], int) or email_data['smtp_port'] <= 0:
            raise ValueError("SMTP port must be a positive integer")
        
        # Validate schedule configuration
        if 'schedule' not in config_data:
            raise ValueError("Configuration missing 'schedule' section")
        
        schedule_data = config_data['schedule']
        if 'hour' not in schedule_data or 'minute' not in schedule_data:
            raise ValueError("Schedule configuration missing 'hour' or 'minute' field")
        
        hour = schedule_data['hour']
        minute = schedule_data['minute']
        
        if not isinstance(hour, int) or not isinstance(minute, int):
            raise ValueError("Schedule hour and minute must be integers")
        
        if not (0 <= hour <= 23):
            raise ValueError("Schedule hour must be between 0 and 23")
        
        if not (0 <= minute <= 59):
            raise ValueError("Schedule minute must be between 0 and 59")
        
        # Create and return validated config
        email_config = EmailConfig(
            to=email_data['to'],
            smtp_server=email_data['smtp_server'],
            smtp_port=email_data['smtp_port'],
            username=email_data['username']
        )
        
        schedule_config = ScheduleConfig(
            hour=hour,
            minute=minute
        )
        
        return AppConfig(
            rss_feeds=rss_feeds,
            email=email_config,
            schedule=schedule_config
        )


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        AppConfig: Loaded and validated configuration
    """
    loader = ConfigLoader(config_path)
    return loader.load_config()


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"RSS Feeds: {len(config.rss_feeds)} feeds configured")
        print(f"Email: {config.email.to}")
        print(f"Schedule: {config.schedule.hour:02d}:{config.schedule.minute:02d}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1) 