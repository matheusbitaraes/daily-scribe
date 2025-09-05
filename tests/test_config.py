"""
Tests for the configuration loader component.
"""

import json
import tempfile
import os
import pytest
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.config import ConfigLoader, AppConfig, EmailConfig, ScheduleConfig, DatabaseConfig


class TestConfigLoader:
    """Test cases for ConfigLoader class."""
    
    def test_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "rss_feeds": [
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://rss.cnn.com/rss/edition.rss"
            ],
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            config = loader.load_config()
            
            assert isinstance(config, AppConfig)
            assert len(config.rss_feeds) == 2
            assert config.rss_feeds[0] == "https://feeds.bbci.co.uk/news/rss.xml"
            assert config.email.to == "test@example.com"
            assert config.email.smtp_server == "smtp.gmail.com"
            assert config.email.smtp_port == 587
            assert config.schedule.hour == 8
            assert config.schedule.minute == 0
            
        finally:
            os.unlink(temp_config_path)
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        loader = ConfigLoader("nonexistent_config.json")
        
        with pytest.raises(FileNotFoundError):
            loader.load_config()
    
    def test_invalid_json(self):
        """Test handling of malformed JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content')
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(json.JSONDecodeError):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_missing_rss_feeds(self):
        """Test validation of missing RSS feeds section."""
        config_data = {
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="missing 'rss_feeds' section"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_empty_rss_feeds(self):
        """Test validation of empty RSS feeds list."""
        config_data = {
            "rss_feeds": [],
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="must be a non-empty list"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_invalid_rss_url(self):
        """Test validation of invalid RSS feed URLs."""
        config_data = {
            "rss_feeds": [
                "not-a-url",
                "https://feeds.bbci.co.uk/news/rss.xml"
            ],
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="Invalid RSS feed URL"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_missing_email_section(self):
        """Test validation of missing email section."""
        config_data = {
            "rss_feeds": [
                "https://feeds.bbci.co.uk/news/rss.xml"
            ],
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="missing 'email' section"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_invalid_smtp_port(self):
        """Test validation of invalid SMTP port."""
        config_data = {
            "rss_feeds": [
                "https://feeds.bbci.co.uk/news/rss.xml"
            ],
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": "not-a-number",
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 8,
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="must be a positive integer"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
    
    def test_invalid_schedule_hour(self):
        """Test validation of invalid schedule hour."""
        config_data = {
            "rss_feeds": [
                "https://feeds.bbci.co.uk/news/rss.xml"
            ],
            "email": {
                "to": "test@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com"
            },
            "schedule": {
                "hour": 25,  # Invalid hour
                "minute": 0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError, match="hour must be between 0 and 23"):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__]) 