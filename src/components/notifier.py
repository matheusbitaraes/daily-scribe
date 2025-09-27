"""
Email Notifier for Daily Scribe application.

This module handles sending the daily digest via email with enhanced
delivery tracking, rate limiting, and error handling.
"""

import logging
import os
import resend
from datetime import datetime


class EmailNotifier:
    """Handles sending emails with support for multiple providers, delivery tracking, and rate limiting."""

    def __init__(self):
        """
        Initialize the email notifier.

        """
        self.logger = logging.getLogger(__name__)
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        resend.api_key = self.resend_api_key

    def _send_email(self, subject: str, html_content: str, sender_email: str, recipient_email: str) -> bool:
        r = resend.Emails.send({
        "from": sender_email,
        "to": recipient_email,
        "subject": subject,
        "html": html_content
        })
        return r

    def send_email(self, subject: str, html_content: str, recipient_email: str, sender_email: str = None) -> bool:
        """
        Send an email with the specified subject and HTML content.

        Args:
            subject: The subject of the email.
            html_content: The HTML content of the email.
            sender_email: The email address of the sender.
            recipient_email: The email address of the recipient.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        max_retries = 3
        sender_email = sender_email or os.getenv('EMAIL_FROM_ADMIN', 'admin@dailyscribe.news')
        for attempt in range(1, max_retries + 1):
            try:
                if self._send_email(subject, html_content, sender_email, recipient_email):
                    return True
            except Exception as e:
                self.logger.error(f"Attempt {attempt} failed to send email to {recipient_email}: {str(e)}")
                if attempt == max_retries:
                    self.logger.error(f"All {max_retries} attempts failed to send email to {recipient_email}")
                    return False
        return False
    
    def send_digest(self, digest_content: str, recipient_email: str, sender_email: str, subject: str) -> None:
        """
        Send the daily digest to the specified recipient.

        Args:
            digest_content: The content of the daily digest.
            recipient_email: The email address of the recipient.
            subject: The subject of the email.
        """
        delivery_start_time = datetime.now()
        
        try:
            # Log email preparation
            self.logger.info(
                f"📧 Preparing email: from={sender_email}, to={recipient_email}, subject='{subject}'"
            )

            response = resend.Emails.send({
                "from": sender_email,
                "to": recipient_email,
                "subject": subject,
                "html": digest_content
                })
            
            if response:
                delivery_time = (datetime.now() - delivery_start_time).total_seconds()
                self.logger.info(f"📬 Email delivery completed in {delivery_time:.2f}s")
            else:
                raise Exception("Email delivery failed after retries")

        except Exception as e:
            delivery_time = (datetime.now() - delivery_start_time).total_seconds()
            self.logger.error(
                f"❌ Email delivery failed after {delivery_time:.2f}s: "
                f"to={recipient_email}, error={str(e)}"
            )
            raise e
