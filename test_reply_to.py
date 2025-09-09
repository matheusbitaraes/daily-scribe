#!/usr/bin/env python3
"""
Test script to verify that Reply-To functionality works properly with editor@dailyscribe.news
"""

import os
import sys
sys.path.append('src')

from components.config import load_config
from components.notifier import EmailNotifier


def test_reply_to_functionality():
    """Test that emails include proper Reply-To header"""
    try:
        # Load configuration
        config = load_config()
        print(f"Loaded configuration with provider: {config.email.provider}")
        print(f"Editor email address: {config.email.addresses.get('editor', 'Not found')}")
        print(f"Legacy email (for replies): {config.email.legacy.get('to') if config.email.legacy else 'Not found'}")
        
        # Create notifier
        notifier = EmailNotifier(config.email)
        
        # Send test email with Reply-To functionality
        test_subject = "Daily Scribe Editor - Reply-To Test"
        test_content = """
        <html>
        <body>
        <h2>Hello! This is your Daily Scribe Editor</h2>
        <p>This email demonstrates the new Reply-To functionality:</p>
        
        <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #1e90ff; margin: 20px 0;">
        <h3>📧 Email Configuration:</h3>
        <p><strong>From:</strong> editor@dailyscribe.news</p>
        <p><strong>Reply-To:</strong> matheusbitaraesdenovaes@gmail.com</p>
        </div>
        
        <p><strong>What this means:</strong></p>
        <ul>
        <li>✅ You receive emails FROM the professional <code>editor@dailyscribe.news</code> address</li>
        <li>✅ When you reply, your response automatically goes TO <code>matheusbitaraesdenovaes@gmail.com</code></li>
        <li>✅ No complex forwarding setup needed</li>
        <li>✅ Professional appearance maintained</li>
        </ul>
        
        <p><strong>Try it:</strong> Reply to this email and see that it goes to your personal Gmail!</p>
        
        <p>Best regards,<br/>
        <strong>Your Daily Scribe Editor</strong><br/>
        <em>editor@dailyscribe.news</em></p>
        </body>
        </html>
        """
        
        recipient = config.email.legacy.get('to', 'matheusbitaraesdenovaes@gmail.com')
        print(f"Sending Reply-To test email to: {recipient}")
        
        # Send using the 'editor' sender type
        notifier.send_digest(test_content, recipient, test_subject, sender_type='editor')
        print("✅ Reply-To test email sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending Reply-To test email: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing Reply-To functionality for editor@dailyscribe.news...")
    success = test_reply_to_functionality()
    
    if success:
        print("\n🎉 Reply-To functionality test completed successfully!")
        print("\n📋 What to do next:")
        print("1. Check your Gmail inbox for the test email")
        print("2. Notice it comes FROM editor@dailyscribe.news")
        print("3. Click Reply and see that it goes TO matheusbitaraesdenovaes@gmail.com")
        print("4. Test replying to confirm the functionality works")
    else:
        print("\n❌ Reply-To functionality test failed!")
        sys.exit(1)
