#!/usr/bin/env python3
"""
Test script to verify health check endpoint error handling.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from fastapi.testclient import TestClient
from api import app

def test_healthy_response():
    """Test that health check returns 200 when everything is working."""
    client = TestClient(app)
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "daily-scribe-api"
    assert "checks" in data
    assert data["checks"]["database"]["status"] == "healthy"
    assert "system" in data
    assert "response_time_ms" in data
    assert data["response_time_ms"] < 100  # Should be very fast
    
    print("✓ Healthy response test passed")

def test_database_failure():
    """Test that health check returns 503 when database is unavailable."""
    client = TestClient(app)
    
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
        
    print("✓ Database failure test passed")

def test_response_time():
    """Test that health check response time is reasonable."""
    client = TestClient(app)
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be very fast for a simple health check
    assert data["response_time_ms"] < 100
    print(f"✓ Response time test passed ({data['response_time_ms']}ms)")

def test_system_info_included():
    """Test that system information is included in healthy responses."""
    client = TestClient(app)
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check system info
    assert "system" in data
    system_info = data["system"]
    assert "python_version" in system_info
    assert "platform" in system_info
    assert "pid" in system_info
    
    print("✓ System info test passed")

if __name__ == "__main__":
    print("Running health check endpoint tests...")
    
    try:
        test_healthy_response()
        test_database_failure()
        test_response_time()
        test_system_info_included()
        
        print("\n🎉 All health check tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
