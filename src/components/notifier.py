"""
Email Notifier for Daily Scribe application.

This module handles sending the daily digest via email.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any


class EmailNotifier:
    """Handles sending emails."""

    def __init__(self, smtp_config: Dict[str, Any]):
        """
        Initialize the email notifier.

        Args:
            smtp_config: A dictionary containing SMTP configuration.
        """
        self.logger = logging.getLogger(__name__)
        self.smtp_config = smtp_config

    def send_digest(self, digest_content: str, recipient_email: str, subject: str) -> None:
        """
        Send the daily digest to the specified recipient.

        Args:
            digest_content: The content of the daily digest.
            recipient_email: The email address of the recipient.
            subject: The subject of the email.
        """
        try:
            # Create the email message
            message = MIMEMultipart()
            message["From"] = self.smtp_config['username']
            message["To"] = recipient_email
            message["Subject"] = subject
            message.attach(MIMEText(digest_content, "html"))

            # Send the email
            with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.sendmail(self.smtp_config['username'], recipient_email, message.as_string())
                self.logger.info(f"Digest sent successfully to {recipient_email}")

        except Exception as e:
            self.logger.error(f"Failed to send digest to {recipient_email}: {e}")
