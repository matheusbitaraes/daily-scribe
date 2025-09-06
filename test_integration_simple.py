"""
Simple integration test for digest service with email preferences.
"""

import tempfile
import os
from unittest.mock import patch

from src.components.digest_service import DigestService
from src.components.digest_builder import DigestBuilder


def test_digest_service_integration():
    """Test that DigestService integrates with EmailService."""
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Create digest service
        digest_service = DigestService()
        
        # Test that email_service is initialized
        assert hasattr(digest_service, 'email_service')
        assert digest_service.email_service is not None
        
        # Create sample data
        email = "test@example.com"
        clustered_articles = [
            [
                {
                    'title': 'Test Article',
                    'url': 'https://example.com/test',
                    'published': '2024-01-01T12:00:00Z',
                    'summary': 'Test summary',
                    'source': 'Test Source'
                }
            ]
        ]
        
        # Mock the build_html_digest to focus on our integration
        with patch.object(DigestBuilder, 'build_html_digest') as mock_builder:
            mock_builder.return_value = "<html><body>Test digest content</body></html>"
            
            # Mock the news curator to return our test data
            with patch('src.components.digest_service.NewsCurator') as mock_curator_class:
                mock_curator = mock_curator_class.return_value
                mock_curator.curate_and_cluster_for_user.return_value = clustered_articles
                
                # Mock the clusterer
                with patch('src.components.digest_service.ArticleClusterer') as mock_clusterer_class:
                    mock_clusterer = mock_clusterer_class.return_value
                    
                    # Generate digest
                    result = digest_service.generate_digest_for_user(email)
                    
                    # Verify the result
                    assert result["success"] is True
                    assert "html_content" in result
                    
                    # Verify that preference button is included
                    html_content = result["html_content"]
                    if isinstance(html_content, dict):
                        # If the method returns a dict, extract the HTML
                        html_content = html_content.get("html_content", str(html_content))
                    
                    # Should contain preference configuration elements
                    assert "Configurar Preferências" in str(html_content) or "preference" in str(html_content).lower()
                    
        print("✅ DigestService successfully integrated with EmailService")
        print(f"✅ Result structure: {list(result.keys())}")
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except (OSError, FileNotFoundError):
            pass


if __name__ == "__main__":
    test_digest_service_integration()
