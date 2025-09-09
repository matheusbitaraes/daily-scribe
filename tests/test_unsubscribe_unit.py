#!/usr/bin/env python3
"""
Unit tests for unsubscribe functionality.
Tests both the API endpoint and the subscription service logic.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.database import DatabaseService
from components.subscription_service import SubscriptionService
from components.security.token_manager import SecureTokenManager
from fastapi.testclient import TestClient


class TestUnsubscribeService:
    """Test the unsubscribe service logic."""
    
    def setup_method(self):
        """Set up test database and services for each test."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize services
        self.db_service = DatabaseService(self.temp_db.name)
        self.subscription_service = SubscriptionService(self.db_service)
        self.token_manager = SecureTokenManager(self.db_service)
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_valid_unsubscribe_token_validation(self):
        """Test that valid unsubscribe tokens are accepted."""
        # Create a test user preferences record
        test_email = "test@example.com"
        prefs_id = self.db_service.add_user_preferences(
            email_address=test_email,
            enabled_sources=[],
            enabled_categories=[],
            keywords=[],
            max_news_per_category=10
        )
        
        # Generate unsubscribe token
        token = self.token_manager.create_unsubscribe_token(
            user_email=test_email,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        assert token is not None
        
        # Validate the token
        validation_result = self.token_manager.validate_token(
            token=token,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        assert validation_result.is_valid
        assert validation_result.user_email == test_email
    
    def test_invalid_unsubscribe_token_rejection(self):
        """Test that invalid tokens are properly rejected."""
        validation_result = self.token_manager.validate_token(
            token="invalid-token-123",
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        assert not validation_result.is_valid
        assert validation_result.error_message is not None
    
    def test_unsubscribe_service_with_valid_token(self):
        """Test the complete unsubscribe service flow with valid token."""
        # Create test user
        test_email = "unsubscribe@example.com"
        prefs_id = self.db_service.add_user_preferences(
            email_address=test_email,
            enabled_sources=[],
            enabled_categories=[],
            keywords=[],
            max_news_per_category=10
        )
        
        # Generate token
        token = self.token_manager.create_unsubscribe_token(
            user_email=test_email,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        # Process unsubscribe request
        result = self.subscription_service.process_unsubscribe_request(token)
        
        assert result['success'] is True
        assert result['email'] == test_email
        assert 'unsubscribed_at' in result
    
    def test_unsubscribe_service_with_invalid_token(self):
        """Test unsubscribe service with invalid token."""
        result = self.subscription_service.process_unsubscribe_request("invalid-token")
        
        assert result['success'] is False
        assert result['error'] == 'invalid_token'
    
    def test_unsubscribe_service_with_nonexistent_user(self):
        """Test unsubscribe with token for non-existent user."""
        # Create token for non-existent user (this shouldn't normally happen)
        # We'll test the error handling when the user preferences don't exist
        
        # Mock a token validation that returns a user that doesn't exist in preferences
        with patch.object(self.subscription_service.token_manager, 'validate_token') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=True,
                user_email="nonexistent@example.com",
                error_message=None
            )
            
            result = self.subscription_service.process_unsubscribe_request("mock-token")
            
            # Should handle gracefully - either create preferences or return appropriate error
            assert 'success' in result
            assert 'error' in result or 'email' in result


class TestUnsubscribeAPI:
    """Test the unsubscribe API endpoint."""
    
    def setup_method(self):
        """Set up test client for each test."""
        # Import here to avoid circular imports
        from api import app
        self.client = TestClient(app)
    
    def test_unsubscribe_endpoint_with_invalid_token(self):
        """Test unsubscribe endpoint with invalid token."""
        response = self.client.post(
            "/api/unsubscribe",
            json={"token": "invalid-token-123"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "invalid_token"
    
    def test_unsubscribe_endpoint_with_malformed_request(self):
        """Test unsubscribe endpoint with malformed request."""
        response = self.client.post(
            "/api/unsubscribe",
            json={"invalid_field": "test"}
        )
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_unsubscribe_endpoint_without_token(self):
        """Test unsubscribe endpoint without token field."""
        response = self.client.post(
            "/api/unsubscribe",
            json={}
        )
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_unsubscribe_endpoint_response_structure(self):
        """Test that unsubscribe endpoint returns proper error structure."""
        response = self.client.post(
            "/api/unsubscribe",
            json={"token": "test-invalid-token"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        # Check error response structure
        assert "detail" in data
        detail = data["detail"]
        assert isinstance(detail, dict)
        assert "error" in detail
        assert "code" in detail
        assert "details" in detail
    
    def test_unsubscribe_endpoint_content_type(self):
        """Test unsubscribe endpoint with wrong content type."""
        response = self.client.post(
            "/api/unsubscribe",
            data="invalid-data"
        )
        
        assert response.status_code == 422


class TestUnsubscribeTokenSecurity:
    """Test security aspects of unsubscribe tokens."""
    
    def setup_method(self):
        """Set up test database for security tests."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_service = DatabaseService(self.temp_db.name)
        self.token_manager = SecureTokenManager(self.db_service)
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_unsubscribe_token_has_proper_purpose(self):
        """Test that unsubscribe tokens are created with correct purpose."""
        test_email = "security@example.com"
        
        # Create user preferences
        self.db_service.add_user_preferences(
            email_address=test_email,
            enabled_sources=[],
            enabled_categories=[],
            keywords=[],
            max_news_per_category=10
        )
        
        # Generate unsubscribe token
        token = self.token_manager.create_unsubscribe_token(
            user_email=test_email,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        assert token is not None
        
        # Decode and verify purpose (this would require access to JWT payload)
        # For now, we'll verify through database query
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT purpose FROM user_tokens WHERE purpose = 'unsubscribe'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'unsubscribe'
    
    def test_unsubscribe_token_expiry(self):
        """Test that unsubscribe tokens have proper expiry (72 hours)."""
        test_email = "expiry@example.com"
        
        # Create user preferences
        self.db_service.add_user_preferences(
            email_address=test_email,
            enabled_sources=[],
            enabled_categories=[],
            keywords=[],
            max_news_per_category=10
        )
        
        # Generate token
        token = self.token_manager.create_unsubscribe_token(
            user_email=test_email,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        # Check expiry in database (should be ~72 hours from now)
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT expires_at, max_usage 
                FROM user_tokens 
                WHERE purpose = 'unsubscribe' 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            assert result is not None
            expires_at_str, max_usage = result
            
            # Parse expiry time
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.utcnow()
            time_diff = expires_at - now
            
            # Should be approximately 72 hours (within 1 hour tolerance)
            expected_hours = 72
            assert abs(time_diff.total_seconds() / 3600 - expected_hours) < 1
            
            # Should have limited usage (3 times)
            assert max_usage == 3
    
    def test_preference_token_cannot_unsubscribe(self):
        """Test that preference tokens cannot be used for unsubscription."""
        test_email = "mixed@example.com"
        
        # Create user preferences
        self.db_service.add_user_preferences(
            email_address=test_email,
            enabled_sources=[],
            enabled_categories=[],
            keywords=[],
            max_news_per_category=10
        )
        
        # Generate preference token (not unsubscribe token)
        preference_token = self.token_manager.create_preference_token(
            user_email=test_email,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        # Try to use preference token for unsubscription
        subscription_service = SubscriptionService(self.db_service)
        result = subscription_service.process_unsubscribe_request(preference_token)
        
        # Should fail with invalid token type error
        assert result['success'] is False
        assert result['error'] == 'invalid_token_type'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
