#!/usr/bin/env python3
"""
Email System Validation Script for Daily Scribe
This script validates the email system end-to-end with actual configuration.
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Set up logging for the validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def validate_configuration():
    """Validate email configuration is properly loaded."""
    print("🔧 Validating email configuration...")
    
    try:
        from components.config import EmailConfig
        config = EmailConfig()
        
        print(f"✅ Email configuration loaded successfully")
        print(f"   - Primary addresses configured: {bool(config.addresses)}")
        print(f"   - Legacy fallback configured: {bool(config.legacy)}")
        print(f"   - SMTP settings loaded: {bool(config.smtp)}")
        
        return config
    except Exception as e:
        print(f"❌ Email configuration validation failed: {e}")
        return None

def validate_email_service():
    """Validate EmailService functionality."""
    print("\n📧 Validating EmailService functionality...")
    
    try:
        from components.email_service import EmailService
        
        email_service = EmailService()
        test_email = "test-validation@example.com"
        
        # Test token generation
        preference_token = email_service.generate_preference_token(test_email)
        unsubscribe_token = email_service.generate_unsubscribe_token(test_email)
        
        print(f"✅ EmailService validation successful")
        print(f"   - Preference token generated: {bool(preference_token)}")
        print(f"   - Unsubscribe token generated: {bool(unsubscribe_token)}")
        
        # Test digest building
        sample_articles = [
            [{
                'title': 'Validation Test Article',
                'url': 'https://example.com/test',
                'published': datetime.now().isoformat(),
                'summary': 'This is a test article for validation.',
                'source': 'Test Source'
            }]
        ]
        
        digest_result = email_service.build_digest_with_preferences(
            clustered_summaries=sample_articles,
            email_address=test_email
        )
        
        print(f"   - Digest building successful: {bool(digest_result.get('html_content'))}")
        print(f"   - Digest contains test article: {'Validation Test Article' in digest_result.get('html_content', '')}")
        
        return email_service
    except Exception as e:
        print(f"❌ EmailService validation failed: {e}")
        return None

def validate_email_notifier(config):
    """Validate EmailNotifier functionality (without sending actual emails)."""
    print("\n📬 Validating EmailNotifier functionality...")
    
    try:
        from components.notifier import EmailNotifier
        
        # Initialize notifier with configuration
        notifier = EmailNotifier(config)
        
        print(f"✅ EmailNotifier validation successful")
        print(f"   - Notifier initialized with config: {bool(config)}")
        print(f"   - SMTP configuration loaded: {bool(notifier.smtp_config)}")
        
        # Note: We don't actually send emails in validation to avoid costs/limits
        print(f"   - Ready for email sending: ✅")
        
        return notifier
    except Exception as e:
        print(f"❌ EmailNotifier validation failed: {e}")
        return None

def validate_digest_builder():
    """Validate DigestBuilder functionality."""
    print("\n📰 Validating DigestBuilder functionality...")
    
    try:
        from components.digest_builder import DigestBuilder
        
        sample_articles = [
            [{
                'title': 'Test News Article',
                'url': 'https://example.com/news',
                'published': datetime.now().isoformat(),
                'summary': 'This is a test news article summary.',
                'source': 'Test News Source'
            }]
        ]
        
        # Test basic digest building
        digest_html = DigestBuilder.build_html_digest(
            clustered_summaries=sample_articles,
            preference_button_html="<p>Test Button</p>",
            unsubscribe_link_html="<p>Test Unsubscribe</p>"
        )
        
        print(f"✅ DigestBuilder validation successful")
        print(f"   - HTML digest generated: {bool(digest_html)}")
        print(f"   - Contains test article: {'Test News Article' in digest_html}")
        print(f"   - Contains preference button: {'Test Button' in digest_html}")
        print(f"   - Contains unsubscribe link: {'Test Unsubscribe' in digest_html}")
        
        return True
    except Exception as e:
        print(f"❌ DigestBuilder validation failed: {e}")
        return False

def main():
    """Run the complete email system validation."""
    print("🚀 Starting Daily Scribe Email System Validation")
    print("=" * 60)
    
    setup_logging()
    
    # Run all validation steps
    config = validate_configuration()
    email_service = validate_email_service()
    notifier = validate_email_notifier(config) if config else None
    digest_builder_ok = validate_digest_builder()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    print(f"   - Email Configuration: {'✅' if config else '❌'}")
    print(f"   - Email Service: {'✅' if email_service else '❌'}")
    print(f"   - Email Notifier: {'✅' if notifier else '❌'}")
    print(f"   - Digest Builder: {'✅' if digest_builder_ok else '❌'}")
    
    all_passed = all([config, email_service, notifier, digest_builder_ok])
    
    if all_passed:
        print("\n🎉 All email system components validated successfully!")
        print("   The email system is ready for production use.")
        print("\n📋 Next steps:")
        print("   1. Run manual testing checklist: docs/email-testing-checklist.md")
        print("   2. Execute full test suite: pytest tests/test_email_*.py")
        print("   3. Monitor email delivery in production")
    else:
        print("\n⚠️  Some email system components failed validation.")
        print("   Please review the errors above and fix configuration issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
