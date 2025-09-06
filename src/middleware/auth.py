"""
Authentication middleware for Daily Scribe API.

This module provides token-based authentication for the preference
configuration endpoints using the SecureTokenManager.
"""

import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..components.database import DatabaseService
from ..components.security.token_manager import SecureTokenManager, TokenValidationResult
from ..models.preferences import ErrorResponse

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for token authentication
security = HTTPBearer(auto_error=False)


class TokenAuthMiddleware:
    """Token authentication middleware for preference API endpoints."""
    
    def __init__(self, db_service: DatabaseService):
        """
        Initialize the authentication middleware.
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
        self.token_manager = SecureTokenManager(db_service)
    
    def extract_client_info(self, request: Request) -> Tuple[str, str]:
        """
        Extract client information from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (user_agent, ip_address)
        """
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        # Extract IP address, considering proxies
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP", "") or
            getattr(request.client, "host", "unknown")
        )
        
        return user_agent, ip_address
    
    def validate_preference_token(
        self, 
        request: Request, 
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> TokenValidationResult:
        """
        Validate token for preference access.
        
        Args:
            request: FastAPI request object
            credentials: HTTP authorization credentials
            
        Returns:
            TokenValidationResult with validation details
            
        Raises:
            HTTPException: If token is invalid or missing
        """
        # Check if token is provided
        if not credentials or not credentials.credentials:
            logger.warning(f"Missing token in request from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error="MISSING_TOKEN",
                    message="Authorization token is required for this endpoint"
                ).dict(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        user_agent, ip_address = self.extract_client_info(request)
        
        # Validate token using SecureTokenManager
        try:
            result = self.token_manager.validate_token(token, user_agent, ip_address)
            
            if not result.is_valid:
                logger.warning(
                    f"Invalid token attempt from {ip_address} - {result.error_message}"
                )
                
                # Determine appropriate error response based on error type
                if "expired" in (result.error_message or "").lower():
                    error_code = "TOKEN_EXPIRED"
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif "fingerprint" in (result.error_message or "").lower():
                    error_code = "INVALID_DEVICE"
                    status_code = status.HTTP_403_FORBIDDEN
                elif "usage limit" in (result.error_message or "").lower():
                    error_code = "TOKEN_EXHAUSTED"
                    status_code = status.HTTP_403_FORBIDDEN
                else:
                    error_code = "INVALID_TOKEN"
                    status_code = status.HTTP_401_UNAUTHORIZED
                
                raise HTTPException(
                    status_code=status_code,
                    detail=ErrorResponse(
                        error=error_code,
                        message=result.error_message or "Token validation failed",
                        details={"token_hint": token[:8] + "..." if len(token) > 8 else "***"}
                    ).dict()
                )
            
            logger.info(
                f"Valid token access from {ip_address} for user {result.user_email} "
                f"(remaining uses: {result.remaining_usage})"
            )
            
            return result
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error="VALIDATION_ERROR",
                    message="Unable to validate token at this time"
                ).dict()
            )


# Create a dependency function for FastAPI
def get_auth_middleware() -> TokenAuthMiddleware:
    """
    Dependency to get authentication middleware instance.
    
    Returns:
        TokenAuthMiddleware instance
    """
    from ..components.database import DatabaseService
    db_service = DatabaseService()
    return TokenAuthMiddleware(db_service)


async def require_valid_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = security,
    auth_middleware: TokenAuthMiddleware = None
) -> TokenValidationResult:
    """
    FastAPI dependency for token validation.
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials
        auth_middleware: Authentication middleware instance
        
    Returns:
        TokenValidationResult if token is valid
        
    Raises:
        HTTPException: If token is invalid
    """
    if auth_middleware is None:
        auth_middleware = get_auth_middleware()
    
    return auth_middleware.validate_preference_token(request, credentials)
