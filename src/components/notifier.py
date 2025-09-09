"""
Email Notifier for Daily Scribe application.

This module handles sending the daily digest via email with enhanced
delivery tracking, rate limiting, and error handling.
"""

import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class EmailNotifier:
    """Handles sending emails with support for multiple providers, delivery tracking, and rate limiting."""

    def __init__(self, smtp_config):
        """
        Initialize the email notifier.

        Args:
            smtp_config: Email configuration object or dictionary containing SMTP configuration.
        """
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting configuration
        self.rate_limit_window = timedelta(minutes=1)  # 1 minute window
        self.max_emails_per_window = 14  # AWS SES default sending rate
        self.email_timestamps = []
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Handle both new EmailConfig objects and legacy dictionaries
        if hasattr(smtp_config, 'provider'):
            # New EmailConfig object
            self.config = smtp_config
            self.smtp_config = {
                'smtp_server': smtp_config.smtp_server,
                'smtp_port': smtp_config.smtp_port,
                'username': smtp_config.username,
                'password': smtp_config.password
            }
        else:
            # Legacy dictionary format (backward compatibility)
            self.smtp_config = smtp_config
            self.config = None

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within the rate limit for sending emails.
        
        Returns:
            bool: True if we can send an email, False if rate limited
        """
        now = datetime.now()
        # Remove timestamps older than the rate limit window
        self.email_timestamps = [
            timestamp for timestamp in self.email_timestamps 
            if now - timestamp < self.rate_limit_window
        ]
        
        # Check if we're under the limit
        if len(self.email_timestamps) < self.max_emails_per_window:
            self.email_timestamps.append(now)
            return True
        
        return False

    def _wait_for_rate_limit(self) -> None:
        """Wait until we can send another email according to rate limits."""
        if not self.email_timestamps:
            return
            
        # Calculate how long to wait until the oldest timestamp is outside the window
        oldest_timestamp = min(self.email_timestamps)
        wait_until = oldest_timestamp + self.rate_limit_window
        now = datetime.now()
        
        if wait_until > now:
            wait_seconds = (wait_until - now).total_seconds()
            self.logger.info(f"Rate limit reached. Waiting {wait_seconds:.1f} seconds...")
            time.sleep(wait_seconds)

    def _send_email_with_retry(self, message: MIMEMultipart, sender_email: str, recipient_email: str) -> bool:
        """
        Send email with retry logic.
        
        Args:
            message: The email message to send
            sender_email: Sender email address
            recipient_email: Recipient email address
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Check rate limit before sending
                if not self._check_rate_limit():
                    self._wait_for_rate_limit()
                
                # Send the email
                with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                    server.starttls()
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                    server.sendmail(sender_email, recipient_email, message.as_string())
                
                # Log successful delivery with tracking info
                self.logger.info(
                    f"✅ Email delivered successfully: "
                    f"from={sender_email}, to={recipient_email}, "
                    f"subject='{message['Subject']}', attempt={attempt + 1}"
                )
                return True
                
            except smtplib.SMTPException as e:
                self.logger.warning(
                    f"⚠️ SMTP error on attempt {attempt + 1}/{self.max_retries}: "
                    f"from={sender_email}, to={recipient_email}, error={str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"❌ Email delivery failed after {self.max_retries} attempts: "
                        f"from={sender_email}, to={recipient_email}, final_error={str(e)}"
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"❌ Unexpected error sending email: "
                    f"from={sender_email}, to={recipient_email}, error={str(e)}"
                )
                break
                
        return False

    def send_digest(self, digest_content: str, recipient_email: str, subject: str, sender_type: str = 'editor') -> None:
        """
        Send the daily digest to the specified recipient with enhanced error handling and delivery tracking.

        Args:
            digest_content: The content of the daily digest.
            recipient_email: The email address of the recipient.
            subject: The subject of the email.
            sender_type: Type of sender address to use ('editor', 'admin', 'support')
        """
        delivery_start_time = datetime.now()
        
        try:
            # Determine sender email address
            if self.config and hasattr(self.config, 'addresses'):
                # Use new configuration with custom addresses
                sender_email = self.config.addresses.get(sender_type, self.config.addresses.get('editor', self.smtp_config['username']))
            else:
                # Use legacy configuration
                sender_email = self.smtp_config['username']
            
            # Determine reply-to address (use personal Gmail for replies)
            reply_to_email = None
            if self.config and hasattr(self.config, 'legacy') and self.config.legacy:
                reply_to_email = self.config.legacy.get('to')
            
            # Create the email message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add Reply-To header so replies go to personal Gmail
            if reply_to_email:
                message["Reply-To"] = reply_to_email
                self.logger.debug(f"Set Reply-To address: {reply_to_email}")
            
            message.attach(MIMEText(digest_content, "html"))

            # Log email preparation
            self.logger.info(
                f"📧 Preparing email: from={sender_email}, to={recipient_email}, "
                f"subject='{subject}', reply_to={reply_to_email or 'None'}"
            )

            # Send the email with retry logic
            success = self._send_email_with_retry(message, sender_email, recipient_email)
            
            if success:
                delivery_time = (datetime.now() - delivery_start_time).total_seconds()
                self.logger.info(f"📬 Email delivery completed in {delivery_time:.2f}s")
            else:
                # Try legacy fallback if available and primary delivery failed
                if self.config and hasattr(self.config, 'legacy') and self.config.legacy:
                    self.logger.warning("🔄 Attempting legacy email fallback...")
                    try:
                        self._send_via_legacy(digest_content, recipient_email, subject)
                    except Exception as legacy_error:
                        self.logger.error(f"❌ Legacy email fallback also failed: {legacy_error}")
                        raise Exception(f"Both primary and legacy email delivery failed")
                else:
                    raise Exception("Email delivery failed and no fallback available")

        except Exception as e:
            delivery_time = (datetime.now() - delivery_start_time).total_seconds()
            self.logger.error(
                f"❌ Email delivery failed after {delivery_time:.2f}s: "
                f"to={recipient_email}, error={str(e)}"
            )
            raise e

    def _send_via_legacy(self, digest_content: str, recipient_email: str, subject: str) -> None:
        """
        Send email using legacy Gmail configuration as fallback.
        
        Args:
            digest_content: The content of the daily digest.
            recipient_email: The email address of the recipient.
            subject: The subject of the email.
        """
        if not self.config or not self.config.legacy:
            raise ValueError("No legacy configuration available")
            
        legacy_config = self.config.legacy
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = legacy_config['username']
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(digest_content, "html"))

        # Send the email using legacy configuration
        with smtplib.SMTP(legacy_config['smtp_server'], legacy_config['smtp_port']) as server:
            server.starttls()
            server.login(legacy_config['username'], legacy_config['password'])
            server.sendmail(legacy_config['username'], recipient_email, message.as_string())
            self.logger.info(f"Digest sent successfully to {recipient_email} via legacy Gmail configuration")
