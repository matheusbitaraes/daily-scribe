"""
Security event logging utilities for Daily Scribe application.

This module provides structured logging for security events with
appropriate detail levels and integration with monitoring systems.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class SecurityEventType(Enum):
    """Enumeration of security event types."""
    TOKEN_CREATED = "token_created"
    TOKEN_VALIDATED = "token_validated"
    TOKEN_REVOKED = "token_revoked"
    DEVICE_MISMATCH = "device_mismatch"
    USAGE_EXCEEDED = "usage_exceeded"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityEventSeverity(Enum):
    """Enumeration of security event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityLogger:
    """Structured security event logger."""

    def __init__(self, logger_name: str = "security"):
        """
        Initialize the security logger.
        
        Args:
            logger_name: Name of the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log a security event with structured data.
        
        Args:
            event_type: Type of security event
            severity: Severity level of the event
            details: Additional event details
            user_id: User identifier (if applicable)
            ip_address: Client IP address (if applicable)
            user_agent: Client user agent (if applicable)
        """
        event_data = {
            "event_type": event_type.value,
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        
        # Add optional context
        if user_id:
            event_data["user_id"] = user_id
        if ip_address:
            event_data["ip_address"] = ip_address
        if user_agent:
            event_data["user_agent"] = user_agent[:200]  # Truncate long user agents
        
        # Log at appropriate level
        message = f"Security Event: {json.dumps(event_data)}"
        
        if severity == SecurityEventSeverity.INFO:
            self.logger.info(message)
        elif severity == SecurityEventSeverity.WARNING:
            self.logger.warning(message)
        elif severity == SecurityEventSeverity.ERROR:
            self.logger.error(message)
        elif severity == SecurityEventSeverity.CRITICAL:
            self.logger.critical(message)

    def log_token_created(
        self,
        token_id: str,
        user_id: str,
        expires_at: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log token creation event."""
        self.log_security_event(
            event_type=SecurityEventType.TOKEN_CREATED,
            severity=SecurityEventSeverity.INFO,
            details={
                "token_id": token_id,
                "expires_at": expires_at,
                "action": "Token created successfully"
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_token_validated(
        self,
        token_id: str,
        user_id: str,
        usage_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log successful token validation."""
        self.log_security_event(
            event_type=SecurityEventType.TOKEN_VALIDATED,
            severity=SecurityEventSeverity.INFO,
            details={
                "token_id": token_id,
                "usage_count": usage_count,
                "action": "Token validated successfully"
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_token_revoked(
        self,
        token_id: str,
        user_id: Optional[str] = None,
        reason: str = "Manual revocation"
    ) -> None:
        """Log token revocation event."""
        self.log_security_event(
            event_type=SecurityEventType.TOKEN_REVOKED,
            severity=SecurityEventSeverity.WARNING,
            details={
                "token_id": token_id,
                "reason": reason,
                "action": "Token revoked"
            },
            user_id=user_id
        )

    def log_device_mismatch(
        self,
        token_id: str,
        user_id: str,
        expected_fingerprint: str,
        actual_fingerprint: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log device fingerprint mismatch."""
        self.log_security_event(
            event_type=SecurityEventType.DEVICE_MISMATCH,
            severity=SecurityEventSeverity.ERROR,
            details={
                "token_id": token_id,
                "expected_fingerprint": expected_fingerprint[:16],  # Truncate for privacy
                "actual_fingerprint": actual_fingerprint[:16],
                "action": "Device fingerprint mismatch detected"
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_usage_exceeded(
        self,
        token_id: str,
        user_id: str,
        usage_count: int,
        max_usage: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log token usage limit exceeded."""
        self.log_security_event(
            event_type=SecurityEventType.USAGE_EXCEEDED,
            severity=SecurityEventSeverity.ERROR,
            details={
                "token_id": token_id,
                "usage_count": usage_count,
                "max_usage": max_usage,
                "action": "Token usage limit exceeded"
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_invalid_token(
        self,
        token_error: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log invalid token attempt."""
        self.log_security_event(
            event_type=SecurityEventType.INVALID_TOKEN,
            severity=SecurityEventSeverity.WARNING,
            details={
                "error": token_error,
                "action": "Invalid token rejected"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_expired_token(
        self,
        token_id: str,
        expired_at: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log expired token usage attempt."""
        self.log_security_event(
            event_type=SecurityEventType.EXPIRED_TOKEN,
            severity=SecurityEventSeverity.WARNING,
            details={
                "token_id": token_id,
                "expired_at": expired_at,
                "action": "Expired token rejected"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_suspicious_activity(
        self,
        activity_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log suspicious activity."""
        self.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecurityEventSeverity.CRITICAL,
            details={
                "activity_type": activity_type,
                **details,
                "action": "Suspicious activity detected"
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )


# Global security logger instance
security_logger = SecurityLogger()
