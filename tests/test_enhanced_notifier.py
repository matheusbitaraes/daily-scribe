#!/usr/bin/env python3
"""
Test script to verify enhanced email notifier with delivery tracking and rate limiting.
"""

import os
import sys
sys.path.append('src')

from components.config import load_config
from components.notifier import EmailNotifier


def test_enhanced_notifier():
    """Test the enhanced email notifier functionality"""
    try:
        # Load configuration
        config = load_config()
        print(f"Loaded configuration with provider: {config.email.provider}")
        
        # Create enhanced notifier
        notifier = EmailNotifier(config.email)
        
        # Test enhanced logging and delivery tracking
        test_subject = "Daily Scribe - Enhanced Notifier Test"
        test_content = """
        <html>
        <body>
        <h2>Enhanced Email Notifier Test</h2>
        <p>This email tests the new enhanced features:</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3>🚀 New Features Tested:</h3>
        <ul>
        <li>✅ Enhanced delivery tracking and logging</li>
        <li>✅ Rate limiting (14 emails per minute for AWS SES)</li>
        <li>✅ Retry logic with exponential backoff</li>
        <li>✅ Better error handling and reporting</li>
        <li>✅ Reply-To functionality maintained</li>
        </ul>
        </div>
        
        <p><strong>Email Details:</strong></p>
        <ul>
        <li><strong>From:</strong> editor@dailyscribe.news</li>
        <li><strong>Reply-To:</strong> matheusbitaraesdenovaes@gmail.com</li>
        <li><strong>Provider:</strong> AWS SES with enhanced features</li>
        </ul>
        
        <p>Best regards,<br/>
        <strong>Your Enhanced Daily Scribe System</strong></p>
        </body>
        </html>
        """
        
        recipient = config.email.legacy.get('to', 'matheusbitaraesdenovaes@gmail.com')
        print(f"Sending enhanced test email to: {recipient}")
        
        # Send using the enhanced notifier
        notifier.send_digest(test_content, recipient, test_subject, sender_type='editor')
        print("✅ Enhanced email notifier test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing enhanced notifier: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing enhanced email notifier functionality...")
    success = test_enhanced_notifier()
    
    if success:
        print("\n🎉 Enhanced email notifier test completed!")
        print("\n📊 Check the logs above for detailed delivery tracking information")
        print("📧 Check your Gmail inbox for the test email")
    else:
        print("\n❌ Enhanced email notifier test failed!")
        sys.exit(1)
