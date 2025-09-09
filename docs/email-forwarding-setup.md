# Email Forwarding Setup Guide

## Overview
This guide explains how to set up email forwarding from `editor@dailyscribe.news` to your personal Gmail account so you can receive and respond to emails sent to your Daily Scribe email address.

## Current Configuration ✅
- **Email Address**: `editor@dailyscribe.news`
- **AWS SES**: Configured and verified
- **Domain**: `dailyscribe.news` is verified in AWS SES
- **Outgoing Emails**: Working perfectly via AWS SES SMTP

## Email Forwarding Setup

### Option 1: AWS SES Email Receiving (Recommended)
To receive emails sent to `editor@dailyscribe.news` in your personal Gmail:

1. **Set up MX Record in GoDaddy**:
   - Go to your GoDaddy DNS management
   - Add an MX record:
     - **Type**: MX
     - **Host**: @ (or dailyscribe.news)
     - **Points to**: `inbound-smtp.us-east-1.amazonaws.com`
     - **Priority**: 10
     - **TTL**: 1 hour

2. **Configure SES Receipt Rules** (requires S3 permissions):
   ```bash
   # Create receipt rule for forwarding
   aws ses create-receipt-rule \
     --rule-set-name daily-scribe-rules \
     --rule '{
       "Name": "forward-editor-emails",
       "Recipients": ["editor@dailyscribe.news"],
       "Actions": [{
         "BounceAction": {
           "Message": "This email has been forwarded to the Daily Scribe team.",
           "Sender": "editor@dailyscribe.news",
           "TopicArn": "arn:aws:sns:us-east-1:your-account:email-notifications"
         }
       }],
       "Enabled": true
     }'
   ```

### Option 2: Gmail Forwarding (Simpler Setup)
Since AWS setup requires additional S3 permissions, here's a simpler approach:

1. **Create a Gmail Account** for `editor@dailyscribe.news`:
   - This requires custom domain email setup through Google Workspace or similar

2. **Set up Forwarding Rules** in Gmail:
   - Forward all emails to your personal Gmail

### Option 3: Email Service Provider (Easiest)
Use a service like:
- **Google Workspace** ($6/month per user)
- **Microsoft 365** ($6/month per user)
- **Zoho Mail** (Free tier available)

## Current Status
✅ **Outgoing emails work perfectly** - Emails are sent from `editor@dailyscribe.news` via AWS SES  
⏳ **Incoming emails need MX record** - Add MX record to GoDaddy DNS to receive emails  
⏳ **Forwarding needs setup** - Choose one of the options above  

## Testing Your Setup
Once you've set up forwarding, test it by:

1. Sending an email TO `editor@dailyscribe.news` from any external email account
2. Check if it arrives in your personal Gmail
3. Reply to that email to test if replies work properly

## Alternative: Simple Reply-To Configuration
If you just want people to be able to reply and have those replies go to your personal Gmail, we can modify the email headers to include a `Reply-To` address:

```python
# In notifier.py, modify the message creation:
message["Reply-To"] = "matheusbitaraesdenovaes@gmail.com"
```

This way:
- Emails are sent FROM `editor@dailyscribe.news`
- Replies automatically go TO `matheusbitaraesdenovaes@gmail.com`
- No need for complex forwarding setup

## Recommendation
For immediate functionality, I recommend implementing the **Reply-To** solution since it's:
- ✅ Simple to implement (just a code change)
- ✅ Works immediately
- ✅ No additional AWS permissions needed
- ✅ No DNS changes required
- ✅ Professional appearance maintained

Would you like me to implement the Reply-To solution right now?
