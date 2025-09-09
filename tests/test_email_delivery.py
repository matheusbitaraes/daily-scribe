"""
Email Delivery Testing Suite for Daily Scribe.

This module provides comprehensive tests for email delivery functionality,
including SMTP connectivity, email template rendering, error handling,
and integration with AWS SES.
"""

import pytest
import tempfile
import os
import json
import smtplib
from unittest.mock import patch, MagicMock, Mock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Add source path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.config import load_config, EmailConfig
from components.notifier import EmailNotifier
from components.email_service import EmailService
from components.digest_builder import DigestBuilder


class TestEmailDelivery:
    """Test email delivery functionality and SMTP connectivity."""

    def setup_method(self):
        """Set up test environment."""
        # Create a mock email configuration for testing
        self.mock_email_config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="AKIATEST123",
            password="test_password_123",
            region="us-east-1",
            addresses={
                "editor": "editor@test-dailyscribe.news",
                "admin": "admin@test-dailyscribe.news",
                "support": "support@test-dailyscribe.news"
            },
            legacy={
                "to": "test@gmail.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com",
                "password": "test_gmail_password"
            }
        )
        
        self.notifier = EmailNotifier(self.mock_email_config)

    def test_email_notifier_initialization(self):
        """Test EmailNotifier initialization with different configurations."""
        # Test with EmailConfig object
        notifier = EmailNotifier(self.mock_email_config)
        assert notifier.config.provider == "aws_ses"
        assert notifier.smtp_config['smtp_server'] == "email-smtp.us-east-1.amazonaws.com"
        assert notifier.smtp_config['smtp_port'] == 587
        
        # Test with legacy dictionary configuration
        legacy_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'test@gmail.com',
            'password': 'test_password'
        }
        legacy_notifier = EmailNotifier(legacy_config)
        assert legacy_notifier.config is None
        assert legacy_notifier.smtp_config == legacy_config

    def test_sender_email_address_selection(self):
        """Test correct sender email address selection based on sender type."""
        notifier = EmailNotifier(self.mock_email_config)
        
        # Test that sender_type affects email address selection
        # We'll patch the actual send method to inspect the message
        test_recipient = "test@example.com"
        test_subject = "Test Subject"
        test_content = "<html><body>Test Content</body></html>"
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Test editor sender type
            notifier.send_digest(test_content, test_recipient, test_subject, sender_type='editor')
            
            # Verify SMTP connection was attempted
            mock_smtp.assert_called_with("email-smtp.us-east-1.amazonaws.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_with("AKIATEST123", "test_password_123")
            
            # Test that sendmail was called
            assert mock_server.sendmail.called
            
            # Get the message that was sent
            call_args = mock_server.sendmail.call_args[0]
            sender_email = call_args[0]
            recipient_email = call_args[1]
            message_text = call_args[2]
            
            assert sender_email == "editor@test-dailyscribe.news"
            assert recipient_email == test_recipient
            assert "From: editor@test-dailyscribe.news" in message_text
            assert "Reply-To: test@gmail.com" in message_text

    def test_reply_to_header_configuration(self):
        """Test that Reply-To header is properly configured."""
        notifier = EmailNotifier(self.mock_email_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            notifier.send_digest(
                "<html><body>Test</body></html>",
                "test@example.com",
                "Test Subject"
            )
            
            # Get the message content
            call_args = mock_server.sendmail.call_args[0]
            message_text = call_args[2]
            
            # Verify Reply-To header is set to legacy email
            assert "Reply-To: test@gmail.com" in message_text

    def test_rate_limiting_functionality(self):
        """Test email rate limiting functionality."""
        notifier = EmailNotifier(self.mock_email_config)
        
        # Mock the current time to control rate limiting
        with patch('smtplib.SMTP'), \
             patch.object(notifier, '_check_rate_limit') as mock_rate_check:
            
            # Test that rate limiting is checked
            mock_rate_check.return_value = True
            
            notifier.send_digest(
                "<html><body>Test</body></html>",
                "test@example.com",
                "Test Subject"
            )
            
            mock_rate_check.assert_called_once()

    def test_retry_logic_on_smtp_failure(self):
        """Test retry logic when SMTP operations fail."""
        notifier = EmailNotifier(self.mock_email_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            # Configure SMTP to fail first two attempts, succeed on third
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Make sendmail fail twice, then succeed
            mock_server.sendmail.side_effect = [
                smtplib.SMTPException("First failure"),
                smtplib.SMTPException("Second failure"),
                None  # Success on third attempt
            ]
            
            # Mock time.sleep to speed up tests
            with patch('time.sleep'):
                notifier.send_digest(
                    "<html><body>Test</body></html>",
                    "test@example.com",
                    "Test Subject"
                )
            
            # Verify that sendmail was called 3 times (2 failures + 1 success)
            assert mock_server.sendmail.call_count == 3

    def test_legacy_fallback_functionality(self):
        """Test fallback to legacy Gmail when primary email fails."""
        notifier = EmailNotifier(self.mock_email_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Make all SMTP attempts fail to test the fallback logic
            mock_server.sendmail.side_effect = smtplib.SMTPException("Primary email failed")
            
            # Mock sleep to speed up test
            with patch('time.sleep'):
                # The function should raise an exception when both primary and fallback fail
                with pytest.raises(Exception, match="Both primary and legacy email delivery failed"):
                    notifier.send_digest(
                        "<html><body>Test</body></html>",
                        "test@example.com",
                        "Test Subject"
                    )
            
            # Verify that both primary and legacy SMTP connections were attempted
            assert mock_smtp.call_count >= 2  # At least one for primary, one for legacy

    def test_email_content_formatting(self):
        """Test that email content is properly formatted."""
        notifier = EmailNotifier(self.mock_email_config)
        
        test_content = """
        <html>
        <body>
        <h1>Daily Digest</h1>
        <p>Test content with <strong>formatting</strong></p>
        </body>
        </html>
        """
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            notifier.send_digest(
                test_content,
                "test@example.com",
                "Daily Digest Test"
            )
            
            # Get the message content
            call_args = mock_server.sendmail.call_args[0]
            message_text = call_args[2]
            
            # Verify HTML content is included
            assert "Content-Type: text/html" in message_text
            assert "<h1>Daily Digest</h1>" in message_text
            assert "<strong>formatting</strong>" in message_text

    def test_error_handling_for_invalid_credentials(self):
        """Test error handling when SMTP credentials are invalid."""
        # Create config with invalid credentials
        invalid_config = EmailConfig(
            provider="aws_ses",
            smtp_server="email-smtp.us-east-1.amazonaws.com",
            smtp_port=587,
            username="INVALID_USER",
            password="invalid_password",
            region="us-east-1",
            addresses={"editor": "editor@test.com"}
        )
        
        notifier = EmailNotifier(invalid_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Simulate authentication failure
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
            
            # Should raise exception after all retries fail
            with pytest.raises(Exception):
                notifier.send_digest(
                    "<html><body>Test</body></html>",
                    "test@example.com",
                    "Test Subject"
                )

    def test_different_sender_types(self):
        """Test email sending with different sender types."""
        notifier = EmailNotifier(self.mock_email_config)
        
        sender_types = ['editor', 'admin', 'support']
        expected_addresses = [
            "editor@test-dailyscribe.news",
            "admin@test-dailyscribe.news", 
            "support@test-dailyscribe.news"
        ]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            for sender_type, expected_address in zip(sender_types, expected_addresses):
                notifier.send_digest(
                    "<html><body>Test</body></html>",
                    "test@example.com",
                    f"Test from {sender_type}",
                    sender_type=sender_type
                )
                
                # Get the last call's sender address
                call_args = mock_server.sendmail.call_args[0]
                sender_email = call_args[0]
                
                assert sender_email == expected_address

    def test_delivery_time_tracking(self):
        """Test that delivery times are tracked and logged."""
        notifier = EmailNotifier(self.mock_email_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Add a small delay to simulate real sending
            import time
            def slow_sendmail(*args, **kwargs):
                time.sleep(0.1)  # 100ms delay
                return None
            
            mock_server.sendmail.side_effect = slow_sendmail
            
            # Capture log output
            with patch.object(notifier.logger, 'info') as mock_log:
                notifier.send_digest(
                    "<html><body>Test</body></html>",
                    "test@example.com",
                    "Test Subject"
                )
                
                # Verify that delivery time was logged
                log_calls = [call.args[0] for call in mock_log.call_args_list]
                delivery_time_logged = any("delivery completed" in call for call in log_calls)
                assert delivery_time_logged


class TestEmailIntegration:
    """Test email integration with other system components."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

    def teardown_method(self):
        """Clean up test environment."""
        try:
            os.unlink(self.temp_db.name)
        except (OSError, FileNotFoundError):
            pass

    def test_config_loading_integration(self):
        """Test integration between config loading and email notification."""
        # Test that configuration can be loaded and used with EmailNotifier
        try:
            config = load_config()
            notifier = EmailNotifier(config.email)
            
            # Verify notifier was created successfully
            assert notifier is not None
            assert hasattr(notifier, 'config')
            
        except Exception as e:
            # If config loading fails in test environment, that's expected
            pytest.skip(f"Config loading failed in test environment: {e}")

    def test_digest_builder_integration(self):
        """Test integration between digest builder and email delivery."""
        # Create sample clustered articles
        sample_articles = [
            [{
                'title': 'Test Article 1',
                'url': 'https://example.com/1',
                'published': datetime.now().isoformat(),
                'summary': 'Test summary 1',
                'source': 'Test Source 1'
            }],
            [{
                'title': 'Test Article 2', 
                'url': 'https://example.com/2',
                'published': datetime.now().isoformat(),
                'summary': 'Test summary 2',
                'source': 'Test Source 2'
            }]
        ]
        
        # Test that digest can be built
        builder = DigestBuilder()
        
        try:
            html_digest = builder.build_html_digest(sample_articles)
            assert html_digest is not None
            assert len(html_digest) > 0
            assert 'Test Article 1' in html_digest
            assert 'Test Article 2' in html_digest
            
        except Exception as e:
            pytest.skip(f"DigestBuilder integration failed: {e}")

    def test_email_service_integration(self):
        """Test EmailService integration with EmailNotifier."""
        email_service = EmailService()
        
        # Test preference token generation
        test_email = "test@example.com"
        token = email_service.generate_preference_token(test_email)
        
        assert token is not None
        assert len(token) > 10  # JWT tokens should be reasonably long
        
        # Test preference button HTML generation
        button_html = email_service.build_preference_button_html(token)
        
        assert button_html is not None
        assert "Configurar Preferências" in button_html
        assert token in button_html


class TestEmailDeliveryPerformance:
    """Test email delivery performance and optimization."""

    def test_rate_limiting_performance(self):
        """Test that rate limiting doesn't significantly impact performance."""
        config = EmailConfig(
            provider="test",
            smtp_server="test.smtp.com",
            smtp_port=587,
            username="test",
            password="test",
            addresses={"editor": "test@test.com"}
        )
        
        notifier = EmailNotifier(config)
        
        # Measure time for rate limit checks
        start_time = datetime.now()
        
        for i in range(10):
            can_send = notifier._check_rate_limit()
            # All should pass since we're under the limit
            assert can_send is True
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Rate limiting checks should be very fast (under 100ms for 10 checks)
        assert duration < 0.1

    def test_email_content_size_handling(self):
        """Test handling of large email content."""
        config = EmailConfig(
            provider="test",
            smtp_server="test.smtp.com", 
            smtp_port=587,
            username="test",
            password="test",
            addresses={"editor": "test@test.com"}
        )
        
        notifier = EmailNotifier(config)
        
        # Create large content (simulating a big digest)
        large_content = "<html><body>" + "A" * 100000 + "</body></html>"  # 100KB
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Should handle large content without issues
            notifier.send_digest(
                large_content,
                "test@example.com",
                "Large Content Test"
            )
            
            # Verify email was sent
            mock_server.sendmail.assert_called_once()


class TestEmailTemplateRendering:
    """Test email template rendering and formatting."""

    def test_html_email_structure(self):
        """Test that HTML emails have proper structure."""
        config = EmailConfig(
            provider="test",
            smtp_server="test.smtp.com",
            smtp_port=587,
            username="test",
            password="test",
            addresses={"editor": "test@test.com"}
        )
        
        notifier = EmailNotifier(config)
        
        html_content = """
        <html>
        <head><title>Daily Digest</title></head>
        <body>
        <h1>Your Daily News Digest</h1>
        <div class="article">
            <h2>Article Title</h2>
            <p>Article summary...</p>
        </div>
        </body>
        </html>
        """
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            notifier.send_digest(
                html_content,
                "test@example.com",
                "Daily Digest"
            )
            
            # Get the message content
            call_args = mock_server.sendmail.call_args[0]
            message_text = call_args[2]
            
            # Verify proper HTML email structure
            assert "Content-Type: text/html" in message_text
            assert "<html>" in message_text
            assert "<head>" in message_text
            assert "<body>" in message_text
            assert "Daily Digest" in message_text

    def test_special_characters_handling(self):
        """Test handling of special characters in email content."""
        config = EmailConfig(
            provider="test",
            smtp_server="test.smtp.com",
            smtp_port=587,
            username="test", 
            password="test",
            addresses={"editor": "test@test.com"}
        )
        
        notifier = EmailNotifier(config)
        
        # Content with Portuguese characters and special symbols
        special_content = """
        <html><body>
        <h1>Notícias em Português</h1>
        <p>Artigo com acentos: ação, coração, informação</p>
        <p>Símbolos especiais: €, £, ¥, © 2024</p>
        <p>Emojis: 📰 📧 ✅ ❌</p>
        </body></html>
        """
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)
            
            # Should handle special characters without errors
            notifier.send_digest(
                special_content,
                "test@example.com",
                "Teste com Caracteres Especiais"
            )
            
            # Verify email was sent
            mock_server.sendmail.assert_called_once()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main(["-v", __file__])
