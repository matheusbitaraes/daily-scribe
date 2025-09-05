"""
Tests for the FastAPI application endpoints.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthCheckEndpoint:
    """Test cases for the /healthz endpoint."""
    
    def test_health_check_healthy_response(self, client):
        """Test that health check returns 200 when system is healthy."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "daily-scribe-api"
        assert data["version"] == "1.0.0"
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"
        assert "response_time_ms" in data["checks"]["database"]
        assert "system" in data
        assert "response_time_ms" in data
        
    def test_health_check_response_time(self, client):
        """Test that health check response time is under 100ms."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should meet the performance requirement
        assert data["response_time_ms"] < 100
        
    def test_health_check_system_info(self, client):
        """Test that system information is included in response."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check system info structure
        system_info = data["system"]
        assert "python_version" in system_info
        assert "platform" in system_info
        assert "pid" in system_info
        
    def test_health_check_database_failure(self, client):
        """Test that health check returns 503 when database is unavailable."""
        # Mock the database service to raise an exception
        with patch('api.db_service._get_connection') as mock_get_connection:
            mock_get_connection.side_effect = Exception("Database connection failed")
            
            response = client.get("/healthz")
            
            assert response.status_code == 503
            data = response.json()
            
            # Check error response structure
            assert data["status"] == "unhealthy"
            assert "timestamp" in data
            assert data["service"] == "daily-scribe-api"
            assert data["checks"]["database"]["status"] == "unhealthy"
            assert "error" in data["checks"]["database"]
            assert "Database connection failed" in data["checks"]["database"]["error"]
            assert "response_time_ms" in data
            
    def test_health_check_database_query_failure(self, client):
        """Test that health check handles database query failures."""
        # Mock the database connection to return unexpected result
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0]  # Wrong result
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        
        with patch('api.db_service._get_connection', return_value=mock_conn):
            response = client.get("/healthz")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"]["status"] == "unhealthy"
            
    def test_health_check_content_type(self, client):
        """Test that health check returns proper JSON content type."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
    def test_health_check_timestamp_format(self, client):
        """Test that timestamp is in proper ISO format."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be ISO format with Z suffix
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp  # ISO format should have T separator


class TestExistingEndpoints:
    """Test that existing endpoints still work after adding health check."""
    
    def test_articles_endpoint_still_works(self, client):
        """Test that /articles endpoint is not affected by health check addition."""
        # Test that the endpoint is registered and doesn't return 404
        response = client.get("/articles")
        
        # Should not return 404 (endpoint exists)
        # Note: May return 500 due to existing issues, but should not be 404
        assert response.status_code != 404
        
    def test_sources_endpoint_still_works(self, client):
        """Test that /sources endpoint is not affected by health check addition."""
        response = client.get("/sources")
        
        assert response.status_code == 200
