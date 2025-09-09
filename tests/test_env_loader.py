"""
Unit tests for environment variable loading functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from components.env_loader import get_env_var, get_jwt_secret_key


class TestEnvLoader:
    """Test cases for environment variable loading."""

    def test_get_env_var_with_existing_variable(self):
        """Test getting an existing environment variable."""
        # Set a test environment variable
        test_key = 'TEST_ENV_VAR'
        test_value = 'test_value_123'
        
        with patch.dict(os.environ, {test_key: test_value}):
            result = get_env_var(test_key)
            assert result == test_value

    def test_get_env_var_with_default(self):
        """Test getting a non-existent environment variable with default."""
        test_key = 'NON_EXISTENT_ENV_VAR'
        default_value = 'default_value_456'
        
        # Ensure the variable doesn't exist
        if test_key in os.environ:
            del os.environ[test_key]
        
        result = get_env_var(test_key, default_value)
        assert result == default_value

    def test_get_env_var_without_default_raises_keyerror(self):
        """Test that KeyError is raised when variable doesn't exist and no default provided."""
        test_key = 'NON_EXISTENT_ENV_VAR'
        
        # Ensure the variable doesn't exist
        if test_key in os.environ:
            del os.environ[test_key]
        
        with pytest.raises(KeyError, match=f"Environment variable '{test_key}' not found"):
            get_env_var(test_key)

    def test_get_jwt_secret_key_with_env_var(self):
        """Test getting JWT secret key when environment variable is set."""
        test_secret = 'test_jwt_secret_123'
        
        with patch.dict(os.environ, {'JWT_SECRET_KEY': test_secret}):
            result = get_jwt_secret_key()
            assert result == test_secret

    def test_get_jwt_secret_key_with_default(self):
        """Test getting JWT secret key when environment variable is not set."""
        # Remove JWT_SECRET_KEY if it exists
        env_without_jwt = {k: v for k, v in os.environ.items() if k != 'JWT_SECRET_KEY'}
        
        with patch.dict(os.environ, env_without_jwt, clear=True):
            result = get_jwt_secret_key()
            assert result == 'your-secret-key-here'

    def test_dotenv_loading(self):
        """Test that .env file is loaded correctly."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
            temp_env.write('TEST_DOTENV_VAR=dotenv_value_789\n')
            temp_env.write('JWT_SECRET_KEY=dotenv_jwt_secret\n')
            temp_env_path = temp_env.name
        
        try:
            # Mock the dotenv loading to use our temp file
            from dotenv import load_dotenv
            load_dotenv(temp_env_path, override=True)
            
            # Test that the variable from .env is accessible
            assert os.getenv('TEST_DOTENV_VAR') == 'dotenv_value_789'
            assert get_jwt_secret_key() == 'dotenv_jwt_secret'
            
        finally:
            # Cleanup
            os.unlink(temp_env_path)
            # Remove test variables from environment
            if 'TEST_DOTENV_VAR' in os.environ:
                del os.environ['TEST_DOTENV_VAR']


if __name__ == '__main__':
    pytest.main([__file__])
