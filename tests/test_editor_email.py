#!/usr/bin/env python3
"""
Test script to verify that editor@dailyscribe.news email works properly.
"""

import os
import sys
sys.path.append('src')

from components.config import load_config
from components.notifier import EmailNotifier


def test_editor_email():
    """Test sending an email from editor@dailyscribe.news"""
    try:
        # Load configuration
        config = load_config()
        print(f"Loaded configuration with provider: {config.email.provider}")
        print(f"Editor email address: {config.email.addresses.get('editor', 'Not found')}")
        
        # Create notifier
        notifier = EmailNotifier(config.email)
        
        # Send test email
        test_subject = "Daily Scribe Editor - Test Email"
        test_content = """
        <html>
        <body>
        <h2>Hello from your Daily Scribe Editor!</h2>
        <p>This is a test email from <strong>editor@dailyscribe.news</strong></p>
        <p>This email address will be used for your Daily Scribe digest. You can reply to this email and I'll receive it in my personal Gmail inbox.</p>
        <p>Best regards,<br/>Your Daily Scribe Editor</p>
        </body>
        </html>
        """
        
        recipient = config.email.legacy.get('to', 'matheusbitaraesdenovaes@gmail.com')
        print(f"Sending test email to: {recipient}")
        
        # Send using the 'editor' sender type
        notifier.send_digest(test_content, recipient, test_subject, sender_type='editor')
        print("✅ Test email sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing editor@dailyscribe.news email configuration...")
    success = test_editor_email()
    
    if success:
        print("\n🎉 Email configuration test completed successfully!")
        print("Check your Gmail inbox for the test email from editor@dailyscribe.news")
    else:
        print("\n❌ Email configuration test failed!")
        sys.exit(1)
