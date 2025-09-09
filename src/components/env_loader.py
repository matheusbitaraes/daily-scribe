"""
Environment variable loader for Daily Scribe application.

This module ensures that environment variables from .env files are loaded
consistently across the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file once when this module is imported
load_dotenv()

def get_env_var(key: str, default: str = None) -> str:
    """
    Get an environment variable with optional default value.
    
    Args:
        key: Environment variable name
        default: Default value if environment variable is not found
        
    Returns:
        Environment variable value or default
        
    Raises:
        KeyError: If environment variable is not found and no default is provided
    """
    value = os.getenv(key, default)
    if value is None:
        raise KeyError(f"Environment variable '{key}' not found and no default provided")
    return value

def get_jwt_secret_key() -> str:
    """
    Get the JWT secret key from environment variables.
    
    Returns:
        JWT secret key
        
    Raises:
        KeyError: If JWT_SECRET_KEY is not set in environment
    """
    return get_env_var('JWT_SECRET_KEY', 'your-secret-key-here')
