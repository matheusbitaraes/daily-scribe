#!/usr/bin/env python3
"""
Test script for AWS SES email sending
"""

from src.components.config import load_config
from src.components.notifier import EmailNotifier
import traceback

print('🧪 Testing AWS SES email sending...')
print('')

config = load_config()
notifier = EmailNotifier(config.email)

# Test email content
test_subject = 'Daily Scribe AWS SES Test - Success!'
test_content = '''
<html>
<body>
<h2>🎉 Daily Scribe AWS SES Test Email</h2>
<p>Congratulations! Your AWS SES email service is working perfectly.</p>

<h3>✅ What's Working:</h3>
<ul>
    <li><strong>Domain:</strong> dailyscribe.news ✅ Verified</li>
    <li><strong>DKIM:</strong> ✅ Enabled and verified</li>
    <li><strong>Sender:</strong> noreply@dailyscribe.news</li>
    <li><strong>Provider:</strong> AWS SES</li>
    <li><strong>Authentication:</strong> ✅ Working</li>
</ul>

<p><strong>Next steps:</strong> Ready to migrate your Daily Scribe email system!</p>

<hr>
<p><small>This is a test email from Daily Scribe email migration setup.</small></p>
</body>
</html>
'''

# Send test email to your email address
test_recipient = 'matheusbitaraesdenovaes@gmail.com'

try:
    print(f'📧 Sending test email to: {test_recipient}')
    print(f'📧 From: noreply@dailyscribe.news')
    print(f'📧 Subject: {test_subject}')
    print('')
    
    notifier.send_digest(test_content, test_recipient, test_subject, 'noreply')
    print('🎉 SUCCESS! Test email sent successfully!')
    print('')
    print('✅ Check your inbox (matheusbitaraesdenovaes@gmail.com)')
    print('✅ The email should arrive from: noreply@dailyscribe.news')
    print('✅ DKIM and SPF authentication should pass')
    
except Exception as e:
    print(f'❌ ERROR: {str(e)}')
    print('Full traceback:')
    traceback.print_exc()
