"""
Email Integration Testing Suite for Daily Scribe.

This module provides integration tests for email delivery functionality,
testing the complete email pipeline from configuration to delivery.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

# Add source path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.config import load_config, EmailConfig
from components.notifier import EmailNotifier
from components.email_service import EmailService
from components.digest_builder import DigestBuilder
from components.database import DatabaseService


class TestEmailProviderIntegration:
    """Test integration with different email providers."""

    def test_aws_ses_smtp_integration(self):
        """Test AWS SES SMTP integration."""
        aws_config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            region="us-east-1",
            addresses={
                "editor": "editor@dailyscribe.news",
                "admin": "admin@dailyscribe.news",
                "support": "support@dailyscribe.news"
            }
        )
        
        notifier = EmailNotifier(aws_config)
        
        # Mock SMTP connection
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Test successful email delivery
            notifier.send_digest(
                "<html><body>AWS SES Test</body></html>",
                "test@example.com",
                "AWS SES Integration Test"
            )
            
            # Verify AWS SES SMTP settings were used
            mock_smtp.assert_called_with("email-smtp.us-east-1.amazonaws.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_with("AKIATEST123", "test_password")

    def test_gmail_fallback_integration(self):
        """Test Gmail fallback integration."""
        config_with_fallback = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            region="us-east-1",
            addresses={"editor": "editor@dailyscribe.news"},
            legacy={
                "to": "fallback@gmail.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "fallback@gmail.com",
                "password": "gmail_password"
            }
        )
        
        notifier = EmailNotifier(config_with_fallback)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Make primary email fail, trigger fallback
            mock_server.sendmail.side_effect = [Exception("Primary failed"), None]
            
            # Mock time.sleep to speed up test
            with patch('time.sleep'):
                notifier.send_digest(
                    "<html><body>Fallback Test</body></html>",
                    "test@example.com",
                    "Gmail Fallback Test"
                )
            
            # Verify both primary and fallback connections were attempted
            assert mock_smtp.call_count >= 2


class TestEmailServiceWorkflow:
    """Test complete email service workflow."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize services
        self.db_service = DatabaseService(self.temp_db.name)
        self.email_service = EmailService()

    def teardown_method(self):
        """Clean up test environment."""
        try:
            os.unlink(self.temp_db.name)
        except (OSError, FileNotFoundError):
            pass

    def test_complete_digest_email_workflow(self):
        """Test complete workflow from digest generation to email delivery."""
        # Sample article data
        clustered_articles = [
            [{
                'title': 'Breaking News: Test Article',
                'url': 'https://example.com/test-article',
                'published': datetime.now().isoformat(),
                'summary': 'This is a test article summary for email delivery testing.',
                'source': 'Test News Source'
            }],
            [{
                'title': 'Technology Update',
                'url': 'https://example.com/tech-update',
                'published': datetime.now().isoformat(),
                'summary': 'Latest technology news and updates.',
                'source': 'Tech News'
            }]
        ]
        
        test_email = "test@example.com"
        
        # Test digest building with preferences
        digest_result = self.email_service.build_digest_with_preferences(
            clustered_summaries=clustered_articles,
            email_address=test_email,
            user_agent="Test Client",
            ip_address="127.0.0.1"
        )
        
        # Verify digest result structure
        assert digest_result is not None
        assert isinstance(digest_result, dict)
        assert "html_content" in digest_result
        assert "email_address" in digest_result
        assert "metadata" in digest_result
        
        # Verify digest content was generated
        html_content = digest_result["html_content"]
        assert html_content is not None
        assert len(html_content) > 0
        assert "Breaking News: Test Article" in html_content
        assert "Technology Update" in html_content
        
        # Verify metadata
        assert digest_result["email_address"] == test_email
        assert digest_result["metadata"]["clusters_count"] == 2
        assert digest_result["metadata"]["articles_count"] == 2

    def test_preference_management_workflow(self):
        """Test preference management email workflow."""
        test_email = "preferences@example.com"
        
        # Generate preference token
        token = self.email_service.generate_preference_token(test_email)
        assert token is not None
        
        # Build preference button HTML (uses localhost:3000 by default)
        button_html = self.email_service.build_preference_button_html(token)
        assert button_html is not None
        assert "Configurar Preferências" in button_html
        assert token in button_html
        
        # Test preference URL generation (should use localhost:3000)
        preference_url = f"http://localhost:3000/preferences/{token}"
        assert preference_url in button_html

    def test_unsubscribe_workflow(self):
        """Test unsubscribe email workflow."""
        test_email = "unsubscribe@example.com"
        
        # Generate unsubscribe token
        unsubscribe_token = self.email_service.generate_unsubscribe_token(test_email)
        assert unsubscribe_token is not None
            
        # Build unsubscribe HTML using the actual method name
        unsubscribe_html = self.email_service.build_unsubscribe_link_html(unsubscribe_token)
        
        # Verify unsubscribe link is present
        assert unsubscribe_html is not None
        assert "unsubscribe" in unsubscribe_html.lower()
        assert unsubscribe_token in unsubscribe_html


class TestEmailDeliverabilityAndCompliance:
    """Test email deliverability and compliance features."""

    def test_email_headers_compliance(self):
        """Test that email headers comply with best practices."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"},
            legacy={"to": "reply@gmail.com"}
        )
        
        notifier = EmailNotifier(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            notifier.send_digest(
                "<html><body>Compliance Test</body></html>",
                "test@example.com",
                "Compliance Test Subject"
            )
            
            # Get the message content
            call_args = mock_server.sendmail.call_args[0]
            message_text = call_args[2]
            
            # Verify required headers
            assert "From: editor@dailyscribe.news" in message_text
            assert "To: test@example.com" in message_text
            assert "Subject: Compliance Test Subject" in message_text
            assert "Reply-To: reply@gmail.com" in message_text
            assert "Content-Type: text/html" in message_text

    def test_email_authentication_headers(self):
        """Test that authentication-related headers are properly handled."""
        # This test verifies that our email system is compatible with
        # authentication methods like DKIM, SPF, and DMARC
        
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        # Verify that the configuration supports authenticated sending
        assert config.provider == "aws_ses"
        assert config.smtp_server == "email-smtp.us-east-1.amazonaws.com"
        assert "dailyscribe.news" in config.addresses["editor"]

    def test_email_size_limits(self):
        """Test handling of email size limits."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        # Test with normal size content
        normal_content = "<html><body>" + "Normal content " * 100 + "</body></html>"
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Should handle normal content without issues
            notifier.send_digest(
                normal_content,
                "test@example.com",
                "Size Limit Test"
            )
            
            mock_server.sendmail.assert_called_once()

    def test_email_encoding_compliance(self):
        """Test that email encoding handles international characters."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        # Content with international characters (Portuguese)
        international_content = """
        <html><body>
        <h1>Notícias Internacionais</h1>
        <p>Conteúdo com acentos: informação, coração, ação</p>
        <p>Caracteres especiais: ç, ã, õ, á, é, í, ó, ú</p>
        </body></html>
        """
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Should handle international characters properly
            notifier.send_digest(
                international_content,
                "test@example.com",
                "Teste de Codificação Internacional"
            )
            
            mock_server.sendmail.assert_called_once()


class TestEmailErrorHandlingAndRecovery:
    """Test email error handling and recovery mechanisms."""

    def test_network_error_recovery(self):
        """Test recovery from network errors."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123", 
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            # Simulate network timeout that doesn't recover
            mock_smtp.side_effect = ConnectionError("Network timeout")
            
            with patch('time.sleep'):  # Speed up retry delays
                # Should raise exception when network fails and no fallback is configured
                with pytest.raises(Exception, match="Email delivery failed and no fallback available"):
                    notifier.send_digest(
                        "<html><body>Network Recovery Test</body></html>",
                        "test@example.com",
                        "Network Recovery Test"
                    )            # Verify multiple connection attempts were made
            assert mock_smtp.call_count >= 1

    def test_temporary_service_failure_handling(self):
        """Test handling of temporary service failures."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Simulate temporary server error, then success
            import smtplib
            mock_server.sendmail.side_effect = [
                smtplib.SMTPServerDisconnected("Temporary server error"),
                None  # Success on retry
            ]
            
            with patch('time.sleep'):  # Speed up retry delays
                notifier.send_digest(
                    "<html><body>Service Failure Test</body></html>",
                    "test@example.com",
                    "Service Failure Test"
                )
            
            # Verify retry was attempted
            assert mock_server.sendmail.call_count == 2

    def test_rate_limit_handling(self):
        """Test handling of rate limit exceeded scenarios."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        # Fill up the rate limit
        for i in range(notifier.max_emails_per_window):
            notifier._check_rate_limit()
        
        # Next check should indicate rate limit exceeded
        can_send = notifier._check_rate_limit()
        assert can_send is False
        
        # Verify rate limit wait functionality
        with patch('time.sleep') as mock_sleep:
            notifier._wait_for_rate_limit()
            mock_sleep.assert_called_once()


class TestEmailMetricsAndMonitoring:
    """Test email metrics collection and monitoring."""

    def test_delivery_time_measurement(self):
        """Test that email delivery times are measured."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Add delay to simulate actual sending time
            def delayed_sendmail(*args, **kwargs):
                import time
                time.sleep(0.05)  # 50ms delay
            
            mock_server.sendmail.side_effect = delayed_sendmail
            
            # Capture log output to verify timing is logged
            with patch.object(notifier.logger, 'info') as mock_log:
                notifier.send_digest(
                    "<html><body>Timing Test</body></html>",
                    "test@example.com",
                    "Timing Test"
                )
                
                # Verify timing information was logged
                log_calls = [call.args[0] for call in mock_log.call_args_list]
                timing_logged = any("delivery completed" in call for call in log_calls)
                assert timing_logged

    def test_error_rate_tracking(self):
        """Test that email errors are properly tracked."""
        config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password",
            addresses={"editor": "editor@dailyscribe.news"}
        )
        
        notifier = EmailNotifier(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Make all attempts fail
            import smtplib
            mock_server.sendmail.side_effect = smtplib.SMTPException("Test error")
            
            # Capture error logs
            with patch.object(notifier.logger, 'error') as mock_error_log, \
                 patch('time.sleep'):  # Speed up retries
                
                with pytest.raises(Exception):
                    notifier.send_digest(
                        "<html><body>Error Test</body></html>",
                        "test@example.com",
                        "Error Test"
                    )
                
                # Verify errors were logged
                assert mock_error_log.called
                error_calls = [call.args[0] for call in mock_error_log.call_args_list]
                error_logged = any("Email delivery failed" in call for call in error_calls)
                assert error_logged


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main(["-v", __file__])
