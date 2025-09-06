"""
Test email service integration with digest system.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
import json

from src.components.email_service import EmailService
from src.components.database import DatabaseService
from src.components.digest_builder import DigestBuilder


class TestEmailServiceIntegration:
    """Test email service integration with digest system."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database service with temp database
        self.db_service = DatabaseService(self.temp_db.name)
        self.email_service = EmailService()

    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.temp_db.name)
            except (OSError, FileNotFoundError):
                pass

    def test_preference_token_generation(self):
        """Test that preference tokens can be generated."""
        email = "test@example.com"
        
        # Should create user preferences if they don't exist
        token = self.email_service.generate_preference_token(email)
        
        assert token is not None
        assert len(token) > 20  # JWT tokens are long

    def test_preference_button_html_generation(self):
        """Test that preference button HTML is generated correctly."""
        token = "test_token_123"
        
        button_html = self.email_service.build_preference_button_html(token)
        
        assert button_html is not None
        assert "Configurar Preferências" in button_html  # Portuguese text
        assert token in button_html
        assert "background-color: #0a97f5" in button_html  # Button color

    def test_digest_with_preferences_integration(self):
        """Test that digest is built with preference button."""
        email = "test@example.com"
        
        # Sample clustered articles
        clustered_articles = [
            [
                {
                    'title': 'Test Article 1',
                    'url': 'https://example.com/1',
                    'published': '2024-01-01T12:00:00Z',
                    'summary': 'Test summary 1',
                    'source': 'Test Source'
                }
            ]
        ]
        
        with patch.object(DigestBuilder, 'build_html_digest') as mock_builder:
            mock_builder.return_value = "<html><body>Original digest content</body></html>"
            
            result = self.email_service.build_digest_with_preferences(
                clustered_summaries=clustered_articles,
                email_address=email
            )
            
            assert result is not None
            # Should contain either HTML content or dict with content
            if isinstance(result, dict):
                assert "html_content" in result or "content" in result
            else:
                assert "Configurar Preferências" in result
                assert "Original digest content" in result

    def test_email_service_fallback_behavior(self):
        """Test that email service handles errors gracefully."""
        email = "test@example.com"
        clustered_articles = []
        
        # Should not fail even with empty articles
        result = self.email_service.build_digest_with_preferences(
            clustered_summaries=clustered_articles,
            email_address=email
        )
        
        assert result is not None
        # Should handle empty articles gracefully
        if isinstance(result, dict):
            assert "error" in result or "html_content" in result

    def test_preference_button_accessibility(self):
        """Test that preference button includes accessibility features."""
        token = "test_token"
        
        button_html = self.email_service.build_preference_button_html(token)
        
        # Should include accessibility-friendly design
        assert 'rel="noopener"' in button_html  # Security feature
        assert 'target="_blank"' in button_html  # Opens in new tab

    def test_preference_button_fallback_link(self):
        """Test that preference button has proper structure without fallback link."""
        token = "test_token"
        
        button_html = self.email_service.build_preference_button_html(token)
        
        # Should include main button link
        assert "daily-scribe.com" in button_html  # Base URL
        assert "⚙️ Configurar Preferências" in button_html  # Main button text
        # Should NOT have fallback link anymore (simplified design)
        assert button_html.lower().count('configurar') == 1  # Only one instance

    @patch('src.components.email_service.DatabaseService')
    def test_database_integration_mock(self, mock_db):
        """Test email service with mocked database calls."""
        # Mock database responses
        mock_instance = MagicMock()
        mock_db.return_value = mock_instance
        mock_instance.get_user_preferences.return_value = None
        mock_instance.add_user_preferences.return_value = True
        
        # Create EmailService with mocked database
        with patch('src.components.email_service.DatabaseService', return_value=mock_instance):
            email_service = EmailService()
            
            # Mock the token manager to avoid JSON serialization issues
            with patch.object(email_service, 'token_manager') as mock_token_manager:
                mock_token_manager.create_preference_token.return_value = "mocked_token"
                
                token = email_service.generate_preference_token("test@example.com")
                
                assert token == "mocked_token"

    def test_multiple_token_generation(self):
        """Test that multiple tokens can be generated for same user."""
        email = "test@example.com"
        
        token1 = self.email_service.generate_preference_token(email)
        token2 = self.email_service.generate_preference_token(email)
        
        assert token1 is not None
        assert token2 is not None
        # Tokens should be different (each has unique timestamp/device info)
        assert token1 != token2


if __name__ == "__main__":
    pytest.main([__file__])
