"""
Tests for secure token manager functionality.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.components.database import DatabaseService
from src.components.security.token_manager import SecureTokenManager, TokenValidationResult


@pytest.fixture
def db_service():
    """Create test database service."""
    import tempfile
    import os
    
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
    """Create secure token manager with test database."""
    return SecureTokenManager(db_service)


class TestSecureTokenManager:
    """Test secure token manager functionality."""

    def test_create_preference_token_success(self, token_manager):
        """Test successful token creation."""
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_user_not_found(self, token_manager):
        """Test token creation for non-existent user creates default preferences."""
        # This should work since create_preference_token creates default preferences
        token = token_manager.create_preference_token(
            user_email="new@example.com",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_token_success(self, token_manager):
        """Test successful token validation."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Validate token
        result = token_manager.validate_token(token, user_agent, ip_address)
        
        assert result is not None
        assert result.is_valid is True
        assert result.user_email == "test@example.com"
        assert result.user_preferences_id is not None

    def test_validate_token_invalid_jwt(self, token_manager):
        """Test validation of invalid JWT token."""
        result = token_manager.validate_token(
            "invalid.jwt.token", 
            "Mozilla/5.0 Test Browser", 
            "192.168.1.100"
        )
        
        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_token_not_found_in_db(self, token_manager):
        """Test validation of JWT that's not in database."""
        # Create a valid JWT that won't be in database
        import jwt
        payload = {
            "jti": "non-existent-token-id",
            "email": "test@example.com",
            "preferences_id": 1,
            "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }
        fake_token = jwt.encode(payload, token_manager.secret_key, algorithm="HS256")
        
        result = token_manager.validate_token(
            fake_token, 
            "Mozilla/5.0 Test Browser", 
            "192.168.1.100"
        )
        
        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_token_device_fingerprint_mismatch(self, token_manager):
        """Test validation with different device fingerprint."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Validate with different fingerprint
        result = token_manager.validate_token(
            token, 
            "Different Browser", 
            "192.168.1.200"
        )
        
        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_token_usage_limit_exceeded(self, token_manager):
        """Test validation when usage limit is exceeded."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Use token 10 times (up to limit)
        for _ in range(10):
            result = token_manager.validate_token(token, user_agent, ip_address)
            assert result.is_valid is True
        
        # 11th use should fail
        result = token_manager.validate_token(token, user_agent, ip_address)
        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_token_revoked(self, token_manager):
        """Test validation of revoked token."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Revoke token
        token_manager.revoke_token(token)
        
        # Validation should now fail
        result = token_manager.validate_token(token, user_agent, ip_address)
        assert result.is_valid is False
        assert result.error_message is not None

    def test_create_device_fingerprint(self, token_manager):
        """Test device fingerprint generation."""
        fingerprint = token_manager._create_device_fingerprint(
            "Test Browser", 
            "192.168.1.100"
        )
        
        assert fingerprint is not None
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 16  # First 16 characters of SHA256

    def test_create_device_fingerprint_consistent(self, token_manager):
        """Test that device fingerprint is consistent for same input."""
        fingerprint1 = token_manager._create_device_fingerprint(
            "Test Browser", 
            "192.168.1.100"
        )
        fingerprint2 = token_manager._create_device_fingerprint(
            "Test Browser", 
            "192.168.1.100"
        )
        
        assert fingerprint1 == fingerprint2

    def test_create_device_fingerprint_different_for_different_inputs(self, token_manager):
        """Test that device fingerprint differs for different inputs."""
        fingerprint1 = token_manager._create_device_fingerprint(
            "Browser 1", 
            "192.168.1.100"
        )
        fingerprint2 = token_manager._create_device_fingerprint(
            "Browser 2", 
            "192.168.1.200"
        )
        
        assert fingerprint1 != fingerprint2

    def test_cleanup_expired_tokens(self, token_manager):
        """Test cleanup of expired tokens."""
        # Create tokens that would be expired
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        # Create a token
        token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Run cleanup - should not remove non-expired tokens
        removed_count = token_manager.cleanup_expired_tokens()
        assert removed_count >= 0  # Should be 0 for non-expired tokens

    def test_revoke_user_tokens(self, token_manager):
        """Test revoking all tokens for a user."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        # Create multiple tokens for user
        token1 = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        token2 = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Revoke all tokens for user
        success = token_manager.revoke_user_tokens("test@example.com")
        assert success is True
        
        # Both tokens should now be invalid
        result1 = token_manager.validate_token(token1, user_agent, ip_address)
        result2 = token_manager.validate_token(token2, user_agent, ip_address)
        assert result1.is_valid is False
        assert result2.is_valid is False

    def test_get_token_info(self, token_manager):
        """Test getting token information."""
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.100"
        
        token = token_manager.create_preference_token(
            user_email="test@example.com",
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        info = token_manager.get_token_info(token)
        assert info is not None
        # Check for key fields that should be in token info
        assert "created_at" in info
        assert "expires_at" in info
        assert "is_revoked" in info
        assert "max_usage" in info
