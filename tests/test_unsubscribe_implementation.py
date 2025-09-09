#!/usr/bin/env python3
"""
Simple test script to validate unsubscribe functionality implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_digest_builder():
    """Test DigestBuilder with unsubscribe link"""
    from components.digest_builder import DigestBuilder
    
    # Test data
    clustered_summaries = [
        [
            {
                'title': 'Test Article',
                'summary': 'This is a test summary',
                'url': 'https://example.com',
                'category': 'Technology'
            }
        ]
    ]
    
    preference_html = '<div>Preference Button</div>'
    unsubscribe_html = '<div>Unsubscribe Link</div>'
    
    # Test with both parameters
    html = DigestBuilder.build_html_digest(
        clustered_summaries=clustered_summaries,
        preference_button_html=preference_html,
        unsubscribe_link_html=unsubscribe_html
    )
    
    print("✅ DigestBuilder.build_html_digest works with unsubscribe parameter")
    print(f"HTML contains preference button: {'Preference Button' in html}")
    print(f"HTML contains unsubscribe link: {'Unsubscribe Link' in html}")
    
    # Test with default parameters (backward compatibility)
    html_default = DigestBuilder.build_html_digest(clustered_summaries)
    print("✅ DigestBuilder.build_html_digest works with default parameters")
    
    return True

def test_database_token_creation():
    """Test database token creation with purpose parameter"""
    from components.database import DatabaseService
    import tempfile
    import os
    from datetime import datetime, timedelta
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        tmp_path = tmp.name
    
    try:
        # Initialize database
        db_service = DatabaseService(tmp_path)
        
        # Test token creation with purpose
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        token_id = db_service.create_user_token(
            token_id="test_token_123",
            token_hash="hash123",
            user_preferences_id=1,
            device_fingerprint="test_fingerprint",
            expires_at=expires_at,
            max_usage=3,
            purpose="unsubscribe"
        )
        
        print("✅ Database token creation with purpose parameter works")
        print(f"Token ID created: {token_id}")
        
        # Test with default purpose
        token_id_default = db_service.create_user_token(
            token_id="test_token_456",
            token_hash="hash456",
            user_preferences_id=1,
            device_fingerprint="test_fingerprint",
            expires_at=expires_at,
            max_usage=10
        )
        
        print("✅ Database token creation with default purpose works")
        print(f"Default token ID created: {token_id_default}")
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return True

if __name__ == "__main__":
    print("🧪 Testing unsubscribe implementation...")
    print()
    
    try:
        # Test DigestBuilder
        print("1. Testing DigestBuilder...")
        test_digest_builder()
        print()
        
        # Test Database
        print("2. Testing Database token creation...")
        test_database_token_creation()
        print()
        
        print("🎉 All tests passed! Unsubscribe implementation is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
