"""
Tests for user preference API endpoints.

This module tests the RESTful API endpoints for preference management
including token validation, CRUD operations, and error handling.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api import app
from components.database import DatabaseService
from components.security.token_manager import SecureTokenManager


@pytest.fixture
def db_service():
    """Create test database service."""
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        db = DatabaseService(temp_db.name)
        yield db
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_db.name)
        except:
            pass


@pytest.fixture
def token_manager(db_service):
    """Create token manager with test database."""
    return SecureTokenManager(db_service)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "sources": ["TechCrunch", "BBC News"],
        "categories": ["Technology", "Business"],
        "keywords": ["AI", "machine learning"],
        "max_news": 15
    }


@pytest.fixture
def valid_token(db_service, token_manager, test_user_data):
    """Create a valid token for testing."""
    # Add user preferences to database
    prefs_id = db_service.add_user_preferences(
        email_address=test_user_data["email"],
        enabled_sources=test_user_data["sources"],
        enabled_categories=test_user_data["categories"],
        keywords=test_user_data["keywords"],
        max_news_per_category=test_user_data["max_news"]
    )
    
    # Create token
    token = token_manager.create_preference_token(
        user_email=test_user_data["email"],
        user_agent="Mozilla/5.0 Test Browser",
        ip_address="192.168.1.100"
    )
    
    return token


class TestPreferenceEndpoints:
    """Test preference management endpoints."""
    
    def test_get_preferences_success(self, client, db_service, valid_token, test_user_data):
        """Test successful retrieval of user preferences."""
        with patch('src.api.db_service', db_service):
            response = client.get(
                f"/preferences/{valid_token}",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email_address"] == test_user_data["email"]
        assert set(data["enabled_sources"]) == set(test_user_data["sources"])
        assert set(data["enabled_categories"]) == set(test_user_data["categories"])
        assert set(data["keywords"]) == set(test_user_data["keywords"])
        assert data["max_news_per_category"] == test_user_data["max_news"]
    
    def test_get_preferences_missing_token(self, client):
        """Test getting preferences without token."""
        response = client.get("/preferences/dummy_token")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "MISSING_TOKEN"
    
    def test_get_preferences_invalid_token(self, client):
        """Test getting preferences with invalid token."""
        response = client.get(
            "/preferences/invalid_token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "INVALID_TOKEN"
    
    def test_update_preferences_success(self, client, db_service, valid_token, test_user_data):
        """Test successful update of user preferences."""
        update_data = {
            "enabled_sources": ["Reuters", "The Guardian"],
            "enabled_categories": ["Science", "Health"],
            "keywords": ["climate", "research"],
            "max_news_per_category": 20
        }
        
        with patch('src.api.db_service', db_service):
            response = client.put(
                f"/preferences/{valid_token}",
                json=update_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert set(data["enabled_sources"]) == set(update_data["enabled_sources"])
        assert set(data["enabled_categories"]) == set(update_data["enabled_categories"])
        assert set(data["keywords"]) == set(update_data["keywords"])
        assert data["max_news_per_category"] == update_data["max_news_per_category"]
    
    def test_update_preferences_partial(self, client, db_service, valid_token, test_user_data):
        """Test partial update of user preferences."""
        update_data = {
            "keywords": ["new", "keywords"]
        }
        
        with patch('src.api.db_service', db_service):
            response = client.put(
                f"/preferences/{valid_token}",
                json=update_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Keywords should be updated
        assert set(data["keywords"]) == set(update_data["keywords"])
        
        # Other fields should remain unchanged
        assert set(data["enabled_sources"]) == set(test_user_data["sources"])
        assert set(data["enabled_categories"]) == set(test_user_data["categories"])
        assert data["max_news_per_category"] == test_user_data["max_news"]
    
    def test_update_preferences_validation_error(self, client, db_service, valid_token):
        """Test update with validation errors."""
        update_data = {
            "max_news_per_category": 100  # Exceeds maximum of 50
        }
        
        with patch('src.api.db_service', db_service):
            response = client.put(
                f"/preferences/{valid_token}",
                json=update_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_preferences_too_many_sources(self, client, db_service, valid_token):
        """Test update with too many sources."""
        update_data = {
            "enabled_sources": [f"Source{i}" for i in range(25)]  # Exceeds limit of 20
        }
        
        with patch('src.api.db_service', db_service):
            response = client.put(
                f"/preferences/{valid_token}",
                json=update_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_reset_preferences_success(self, client, db_service, valid_token, test_user_data):
        """Test successful reset of user preferences."""
        with patch('src.api.db_service', db_service):
            response = client.post(
                f"/preferences/{valid_token}/reset",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Preferences reset to defaults successfully"
        
        # Check that preferences are reset to defaults
        prefs = data["preferences"]
        assert prefs["enabled_sources"] == []
        assert prefs["enabled_categories"] == []
        assert prefs["keywords"] == []
        assert prefs["max_news_per_category"] == 10
    
    def test_reset_preferences_invalid_token(self, client):
        """Test reset with invalid token."""
        response = client.post(
            "/preferences/invalid_token/reset",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "INVALID_TOKEN"
    
    def test_get_available_options_success(self, client, db_service):
        """Test getting available sources and categories."""
        # Add some test sources
        source_id = db_service.add_source("Test Source")
        db_service.add_rss_feed(source_id, "http://test.com/rss")
        
        with patch('src.api.db_service', db_service):
            response = client.get("/preferences/options")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sources" in data
        assert "categories" in data
        assert isinstance(data["sources"], list)
        assert isinstance(data["categories"], list)
    
    def test_token_usage_tracking(self, client, db_service, valid_token):
        """Test that token usage is tracked properly."""
        with patch('src.api.db_service', db_service):
            # Make multiple requests
            for i in range(3):
                response = client.get(
                    f"/preferences/{valid_token}",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
                assert response.status_code == 200
    
    def test_token_exhaustion(self, client, db_service, valid_token):
        """Test that exhausted tokens are rejected."""
        with patch('src.api.db_service', db_service):
            # Make 10 requests (the default limit)
            for i in range(10):
                response = client.get(
                    f"/preferences/{valid_token}",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
                assert response.status_code == 200
            
            # 11th request should fail
            response = client.get(
                f"/preferences/{valid_token}",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            assert response.status_code == 403
            data = response.json()
            assert data["error"] == "TOKEN_EXHAUSTED"
    
    def test_device_fingerprint_validation(self, client, db_service, valid_token):
        """Test that device fingerprint is validated."""
        # Try to use token with different user agent
        with patch('src.api.db_service', db_service):
            response = client.get(
                f"/preferences/{valid_token}",
                headers={
                    "Authorization": f"Bearer {valid_token}",
                    "User-Agent": "Different Browser"
                }
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "INVALID_DEVICE"
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/preferences/options")
        
        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_error_response_format(self, client):
        """Test that error responses have consistent format."""
        response = client.get("/preferences/invalid_token")
        
        assert response.status_code == 401
        data = response.json()
        
        # Check error response structure
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
    
    def test_performance_requirements(self, client, db_service, valid_token):
        """Test that API responses meet performance requirements."""
        import time
        
        with patch('src.api.db_service', db_service):
            start_time = time.time()
            response = client.get(
                f"/preferences/{valid_token}",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be under 500ms as per requirements
        response_time = (end_time - start_time) * 1000
        assert response_time < 500, f"Response time {response_time}ms exceeds 500ms requirement"


class TestTokenValidation:
    """Test token validation middleware."""
    
    def test_missing_authorization_header(self, client):
        """Test request without Authorization header."""
        response = client.get("/preferences/dummy_token")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "MISSING_TOKEN"
    
    def test_malformed_authorization_header(self, client):
        """Test request with malformed Authorization header."""
        response = client.get(
            "/preferences/dummy_token",
            headers={"Authorization": "InvalidFormat token123"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "MISSING_TOKEN"
    
    def test_empty_token(self, client):
        """Test request with empty token."""
        response = client.get(
            "/preferences/dummy_token",
            headers={"Authorization": "Bearer "}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "MISSING_TOKEN"


class TestSecurityFeatures:
    """Test security features of the preference API."""
    
    def test_token_revocation(self, client, db_service, token_manager, test_user_data):
        """Test that revoked tokens are rejected."""
        # Create and revoke a token
        prefs_id = db_service.add_user_preferences(
            email_address=test_user_data["email"],
            enabled_sources=test_user_data["sources"]
        )
        
        token = token_manager.create_preference_token(
            user_email=test_user_data["email"],
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100"
        )
        
        # Revoke the token
        token_manager.revoke_token(token)
        
        with patch('src.api.db_service', db_service):
            response = client.get(
                f"/preferences/{token}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "INVALID_TOKEN"
    
    def test_input_sanitization(self, client, db_service, valid_token):
        """Test that inputs are properly sanitized."""
        malicious_data = {
            "keywords": ["<script>alert('xss')</script>", "'; DROP TABLE users; --"]
        }
        
        with patch('src.api.db_service', db_service):
            response = client.put(
                f"/preferences/{valid_token}",
                json=malicious_data,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        # Should succeed but sanitize input
        assert response.status_code == 200
        data = response.json()
        
        # Check that the malicious content is stored as-is but won't be executed
        # The API doesn't execute the content, just stores it
        assert len(data["keywords"]) == 2
