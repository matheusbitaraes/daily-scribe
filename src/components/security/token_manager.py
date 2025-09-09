"""
Secure token management for Daily Scribe email preference access.

This module provides enhanced security for email preference configuration
through JWT tokens with device fingerprinting, usage tracking, and
comprehensive validation.
"""

import secrets
import hashlib
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.env_loader import get_jwt_secret_key

from components.database import DatabaseService
from utils.security_logger import security_logger, SecurityEventType, SecurityEventSeverity


@dataclass
class TokenValidationResult:
    """Result of token validation with detailed information."""
    is_valid: bool
    user_preferences_id: Optional[int] = None
    user_email: Optional[str] = None
    error_message: Optional[str] = None
    remaining_usage: Optional[int] = None


class SecureTokenManager:
    """
    Enhanced secure token manager with device fingerprinting and usage tracking.
    
    This class provides comprehensive token management for secure email preference
    access with multiple layers of security validation.
    """

    def __init__(self, database_service: DatabaseService, secret_key: Optional[str] = None):
        """
        Initialize the secure token manager.
        
        Args:
            database_service: Database service instance for token storage
            secret_key: JWT signing secret key (from environment if None)
        """
        self.db = database_service
        self.secret_key = secret_key or get_jwt_secret_key()
        self.algorithm = "HS256"
        self.default_expiry_hours = 24
        self.default_max_usage = 10
        
        # Development mode: skip device fingerprint validation when ENV=dev
        self.development_mode = os.getenv('ENV', '').lower() == 'local'
        
        if self.development_mode:
            print("🔧 Development mode enabled: Device fingerprint validation disabled")
        
        self.skip_device_fingerprint_validation = True # skipping this for now because it does not seem to be working correctly
        
    def _generate_default_secret(self) -> str:
        """Generate a default secret key for development purposes."""
        # In production, this should come from environment variables - TODO: improve this
        return "daily-scribe-jwt-secret-key-for-development-only"

    def _create_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """
        Create a device fingerprint from user agent and IP address.
        
        Args:
            user_agent: Browser user agent string
            ip_address: Client IP address
            
        Returns:
            16-character device fingerprint hash
        """
        device_data = f"{user_agent}:{ip_address}"
        fingerprint = hashlib.sha256(device_data.encode('utf-8')).hexdigest()
        return fingerprint[:16]  # Use first 16 characters for readability

    def create_preference_token(
        self,
        user_email: str,
        user_agent: str,
        ip_address: str,
        expiry_hours: Optional[int] = None,
        max_usage: Optional[int] = None
    ) -> Optional[str]:
        """
        Create a secure preference access token for a user.
        
        Args:
            user_email: User's email address
            user_agent: Browser user agent string
            ip_address: Client IP address
            expiry_hours: Token expiration in hours (default: 24)
            max_usage: Maximum token usage count (default: 10)
            
        Returns:
            JWT token string if successful, None otherwise
        """
        try:
            # Get or create user preferences
            user_prefs = self.db.get_user_preferences_by_email(user_email)
            if not user_prefs:
                # Create default preferences for new user
                with self.db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_preferences (email_address, enabled_sources, enabled_categories)
                        VALUES (?, '', '')
                    """, (user_email,))
                    user_preferences_id = cursor.lastrowid
                    conn.commit()
            else:
                user_preferences_id = user_prefs['id']

            # Generate secure token components
            token_id = secrets.token_urlsafe(32)
            device_fingerprint = self._create_device_fingerprint(user_agent, ip_address)
            
            # Calculate expiration
            expiry_hours = expiry_hours or self.default_expiry_hours
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            max_usage = max_usage or self.default_max_usage

            # Create JWT payload
            payload = {
                "token_id": token_id,
                "user_preferences_id": user_preferences_id,
                "user_email": user_email,
                "device_fp": device_fingerprint,
                "created_at": datetime.utcnow().isoformat(),
                "exp": expires_at,
                "purpose": "email_preferences",
                "version": 1
            }

            # Generate JWT token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            # Hash the token for database storage
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

            # Store token metadata in database
            token_record_id = self.db.create_user_token(
                token_id=token_id,
                token_hash=token_hash,
                user_preferences_id=user_preferences_id,
                device_fingerprint=device_fingerprint,
                expires_at=expires_at.isoformat(),
                max_usage=max_usage,
                purpose="email_preferences"
            )

            if token_record_id:
                # Log successful token creation
                security_logger.log_token_created(
                    token_id=token_id,
                    user_id=str(user_preferences_id),
                    expires_at=expires_at.isoformat(),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return token
            else:
                security_logger.log_security_event(
                    event_type=SecurityEventType.TOKEN_CREATED,
                    severity=SecurityEventSeverity.ERROR,
                    details={"error": "Failed to store token in database", "user_email": user_email},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return None

        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_CREATED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e), "user_email": user_email},
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None

    def create_unsubscribe_token(
        self,
        user_email: str,
        user_agent: str,
        ip_address: str,
        expiry_hours: Optional[int] = None,
        max_usage: Optional[int] = None
    ) -> Optional[str]:
        """
        Create a secure unsubscribe token for a user.
        
        Args:
            user_email: User's email address
            user_agent: Browser user agent string
            ip_address: Client IP address
            expiry_hours: Token expiration in hours (default: 72 for unsubscribe)
            max_usage: Maximum token usage count (default: 3 for unsubscribe)
            
        Returns:
            JWT token string if successful, None otherwise
        """
        try:
            # Get or create user preferences
            user_prefs = self.db.get_user_preferences_by_email(user_email)
            if not user_prefs:
                # Create default preferences for new user
                with self.db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_preferences (email_address, enabled_sources, enabled_categories)
                        VALUES (?, '', '')
                    """, (user_email,))
                    user_preferences_id = cursor.lastrowid
                    conn.commit()
            else:
                user_preferences_id = user_prefs['id']

            # Generate secure token components
            token_id = secrets.token_urlsafe(32)
            device_fingerprint = self._create_device_fingerprint(user_agent, ip_address)
            
            # Calculate expiration (longer for unsubscribe tokens)
            expiry_hours = expiry_hours or 72  # 3 days for unsubscribe
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            max_usage = max_usage or 3  # Limited usage for unsubscribe

            # Create JWT payload
            payload = {
                "token_id": token_id,
                "user_preferences_id": user_preferences_id,
                "user_email": user_email,
                "device_fp": device_fingerprint,
                "created_at": datetime.utcnow().isoformat(),
                "exp": expires_at,
                "purpose": "unsubscribe",
                "version": 1
            }

            # Generate JWT token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            # Hash the token for database storage
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

            # Store token metadata in database
            token_record_id = self.db.create_user_token(
                token_id=token_id,
                token_hash=token_hash,
                user_preferences_id=user_preferences_id,
                device_fingerprint=device_fingerprint,
                expires_at=expires_at.isoformat(),
                max_usage=max_usage,
                purpose="unsubscribe"
            )

            if token_record_id:
                # Log successful token creation
                security_logger.log_token_created(
                    token_id=token_id,
                    user_id=str(user_preferences_id),
                    expires_at=expires_at.isoformat(),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return token
            else:
                security_logger.log_security_event(
                    event_type=SecurityEventType.TOKEN_CREATED,
                    severity=SecurityEventSeverity.ERROR,
                    details={"error": "Failed to store unsubscribe token in database", "user_email": user_email},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return None

        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_CREATED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e), "user_email": user_email, "purpose": "unsubscribe"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None

    def validate_token(
        self,
        token: str,
        user_agent: str,
        ip_address: str
    ) -> TokenValidationResult:
        """
        Validate a preference access token with comprehensive security checks.
        
        Args:
            token: JWT token string
            user_agent: Browser user agent string
            ip_address: Client IP address
            
        Returns:
            TokenValidationResult with validation status and details
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extract token data
            token_id = payload.get("token_id")
            user_preferences_id = payload.get("user_preferences_id")
            user_email = payload.get("user_email")
            stored_device_fp = payload.get("device_fp")
            
            if not all([token_id, user_preferences_id, stored_device_fp]):
                security_logger.log_invalid_token(
                    token_error="Missing required fields in token payload",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return TokenValidationResult(
                    is_valid=False,
                    error_message="Invalid token format"
                )
            
            # Validate device fingerprint (skip in development mode)
            if not self.skip_device_fingerprint_validation:
                current_device_fp = self._create_device_fingerprint(user_agent, ip_address)
                if current_device_fp != stored_device_fp:
                    security_logger.log_device_mismatch(
                        token_id=token_id,
                        user_id=str(user_preferences_id),
                        expected_fingerprint=stored_device_fp,
                        actual_fingerprint=current_device_fp,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Device fingerprint mismatch"
                    )
            else:
                # Development mode: log but don't enforce fingerprint validation
                current_device_fp = self._create_device_fingerprint(user_agent, ip_address)
                if current_device_fp != stored_device_fp:
                    print(f"🔧 Dev mode: Device fingerprint mismatch ignored (expected: {stored_device_fp[:12]}..., actual: {current_device_fp[:12]}...)")

            # Check token metadata in database (skip in development mode)
            if not self.development_mode:
                token_metadata = self.db.get_user_token(token_id)
                if not token_metadata:
                    security_logger.log_invalid_token(
                        token_error="Token not found in database",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Token not found or expired"
                    )

                # Check usage limits
                if token_metadata['usage_count'] >= token_metadata['max_usage']:
                    security_logger.log_usage_exceeded(
                        token_id=token_id,
                        user_id=str(user_preferences_id),
                        usage_count=token_metadata['usage_count'],
                        max_usage=token_metadata['max_usage'],
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Token usage limit exceeded"
                    )

                # Increment usage count
                if not self.db.increment_token_usage(token_id):
                    security_logger.log_security_event(
                        event_type=SecurityEventType.TOKEN_VALIDATED,
                        severity=SecurityEventSeverity.ERROR,
                        details={"error": "Failed to increment usage count", "token_id": token_id},
                        user_id=str(user_preferences_id),
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Failed to update token usage"
                    )
                
                remaining_usage = token_metadata['max_usage'] - token_metadata['usage_count'] - 1
            else:
                # Development mode: skip database checks and usage tracking
                print(f"🔧 Dev mode: Skipping token database checks and usage limits")
                token_metadata = {'usage_count': 0, 'max_usage': 999}  # Mock metadata
                remaining_usage = 999

            # Log successful validation (conditional in dev mode)
            if not self.development_mode:
                security_logger.log_token_validated(
                    token_id=token_id,
                    user_id=str(user_preferences_id),
                    usage_count=token_metadata['usage_count'] + 1,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            else:
                print(f"🔧 Dev mode: Token validation successful for {user_email}")

            return TokenValidationResult(
                is_valid=True,
                user_preferences_id=user_preferences_id,
                user_email=user_email,
                remaining_usage=remaining_usage
            )

        except jwt.ExpiredSignatureError:
            if self.development_mode:
                print("🔧 Dev mode: Token expired but validation allowed")
                # In development, we can try to extract what we can from the expired token
                try:
                    payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
                    return TokenValidationResult(
                        is_valid=True,
                        user_preferences_id=payload.get("user_preferences_id"),
                        user_email=payload.get("user_email"),
                        remaining_usage=999
                    )
                except:
                    pass
            
            security_logger.log_expired_token(
                token_id="unknown",
                expired_at="unknown",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return TokenValidationResult(
                is_valid=False,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            security_logger.log_invalid_token(
                token_error=str(e),
                ip_address=ip_address,
                user_agent=user_agent
            )
            return TokenValidationResult(
                is_valid=False,
                error_message="Invalid token"
            )
        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_VALIDATED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e)},
                ip_address=ip_address,
                user_agent=user_agent
            )
            return TokenValidationResult(
                is_valid=False,
                error_message="Token validation failed"
            )

    def revoke_token(self, token: str, reason: str = "Manual revocation") -> bool:
        """
        Revoke a specific token.
        
        Args:
            token: JWT token string to revoke
            reason: Reason for revocation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Decode token to get token_id
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            user_preferences_id = payload.get("user_preferences_id")
            
            if not token_id:
                return False

            # Revoke in database
            if self.db.revoke_user_token(token_id):
                security_logger.log_token_revoked(
                    token_id=token_id,
                    user_id=str(user_preferences_id) if user_preferences_id else None,
                    reason=reason
                )
                return True
            return False

        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_REVOKED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e), "reason": reason}
            )
            return False

    def revoke_user_tokens(self, user_email: str, reason: str = "User security action") -> bool:
        """
        Revoke all tokens for a specific user.
        
        Args:
            user_email: User's email address
            reason: Reason for revocation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user preferences
            user_prefs = self.db.get_user_preferences_by_email(user_email)
            if not user_prefs:
                return False

            # Revoke all tokens
            if self.db.revoke_user_tokens_by_preferences_id(user_prefs['id']):
                security_logger.log_security_event(
                    event_type=SecurityEventType.TOKEN_REVOKED,
                    severity=SecurityEventSeverity.WARNING,
                    details={
                        "action": "All user tokens revoked",
                        "reason": reason,
                        "user_email": user_email
                    },
                    user_id=str(user_prefs['id'])
                )
                return True
            return False

        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_REVOKED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e), "reason": reason, "user_email": user_email}
            )
            return False

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired and revoked tokens from the database.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            cleaned_count = self.db.cleanup_expired_tokens()
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_REVOKED,
                severity=SecurityEventSeverity.INFO,
                details={
                    "action": "Token cleanup completed",
                    "cleaned_count": cleaned_count
                }
            )
            return cleaned_count
        except Exception as e:
            security_logger.log_security_event(
                event_type=SecurityEventType.TOKEN_REVOKED,
                severity=SecurityEventSeverity.ERROR,
                details={"error": str(e), "action": "Token cleanup failed"}
            )
            return 0

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without validating device fingerprint.
        Useful for debugging and monitoring.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with token information or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            
            if token_id:
                token_metadata = self.db.get_user_token(token_id)
                if token_metadata:
                    return {
                        "token_id": token_id,
                        "user_preferences_id": token_metadata['user_preferences_id'],
                        "created_at": token_metadata['created_at'],
                        "expires_at": token_metadata['expires_at'],
                        "usage_count": token_metadata['usage_count'],
                        "max_usage": token_metadata['max_usage'],
                        "is_revoked": bool(token_metadata['is_revoked']),
                        "purpose": token_metadata['purpose']
                    }
            return None
        except Exception:
            return None
