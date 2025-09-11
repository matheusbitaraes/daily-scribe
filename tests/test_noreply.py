#!/usr/bin/env python3
"""
Test AWS SES email sending with detailed logging
"""

from src.components.config import load_config
from src.components.notifier import EmailNotifier
import logging
import sys

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print('🧪 Testing AWS SES with noreply@dailyscribe.news')
print('=' * 60)

try:
    # Load configuration
    config = load_config()
    logger.info(f"✅ Configuration loaded successfully")
    logger.info(f"Provider: {config.email.provider}")
    logger.info(f"SMTP Server: {config.email.smtp_server}")
    logger.info(f"Username: {config.email.username}")
    logger.info(f"Addresses: {config.email.addresses}")
    
    # Create notifier
    notifier = EmailNotifier(config.email)
    logger.info("✅ EmailNotifier created")
    
    # Test email content
    test_subject = 'Daily Scribe AWS SES Test - noreply@dailyscribe.news'
    test_content = '''
    <html>
    <body>
    <h2>🎉 SUCCESS! AWS SES is Working!</h2>
    <p>This email was sent from: <strong>noreply@dailyscribe.news</strong></p>
    <p>Using: <strong>AWS SES</strong></p>
    <p>Authentication: <strong>DKIM ✅ SPF ✅</strong></p>
    
    <h3>Email Migration Complete!</h3>
    <ul>
        <li>✅ Custom domain configured</li>
        <li>✅ AWS SES working</li>
        <li>✅ Professional sender address</li>
        <li>✅ Email authentication enabled</li>
    </ul>
    
    <p>Daily Scribe is now ready for production email delivery!</p>
    </body>
    </html>
    '''
    
    recipient = 'matheusbitaraesdenovaes@gmail.com'
    
    print('')
    logger.info(f"📧 Sending test email...")
    logger.info(f"📧 To: {recipient}")
    logger.info(f"📧 From: noreply@dailyscribe.news")
    logger.info(f"📧 Subject: {test_subject}")
    print('')
    
    # Send email with explicit sender type
    notifier.send_digest(test_content, recipient, test_subject, 'noreply')
    
    print('🎉 SUCCESS! Email sent successfully!')
    print('✅ Check your inbox for email from: noreply@dailyscribe.news')
    print('✅ The email should show proper DKIM/SPF authentication')
    
except Exception as e:
    logger.error(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
