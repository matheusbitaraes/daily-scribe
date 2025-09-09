# Email Delivery Manual Testing Checklist

## Overview
This document provides a comprehensive manual testing checklist for the Daily Scribe email delivery system after migration to AWS SES with custom domain `editor@dailyscribe.news`.

## Pre-Testing Setup

### 1. Environment Verification
- [ ] Verify AWS SES credentials are configured
- [ ] Confirm custom domain `dailyscribe.news` is verified in AWS SES
- [ ] Check DKIM records are active and verified
- [ ] Verify SPF record is configured (if required)
- [ ] Confirm DMARC policy is set appropriately

### 2. Application Configuration
- [ ] Verify `.env` file contains correct email environment variables
- [ ] Confirm `config.json` has proper email configuration
- [ ] Check that `editor@dailyscribe.news` is set as primary email address
- [ ] Verify Reply-To functionality is configured to personal Gmail

### 3. Service Health Check
- [ ] Run email health check script: `python scripts/email-health-check.py`
- [ ] Verify API health endpoint includes email service status: `curl http://localhost:8000/healthz`
- [ ] Confirm all health checks pass before proceeding

## Core Email Delivery Testing

### 1. Basic Email Sending
- [ ] **Test 1: Simple Email Delivery**
  - Send a basic test email from the system
  - Verify email arrives from `editor@dailyscribe.news`
  - Check that Reply-To header points to personal Gmail
  - Confirm email content displays correctly
  
- [ ] **Test 2: Different Sender Types**
  - Test email with `sender_type='editor'`
  - Test email with `sender_type='admin'`
  - Test email with `sender_type='support'`
  - Verify correct sender addresses are used

### 2. Daily Digest Email Testing
- [ ] **Test 3: Full Digest Email**
  - Generate a complete daily digest
  - Send to test email address
  - Verify HTML formatting is correct
  - Check that all article links work
  - Confirm preference button is present and functional
  - Test unsubscribe link functionality

- [ ] **Test 4: Mobile Email Client Compatibility**
  - View digest email on iPhone Mail app
  - View digest email on Android Gmail app
  - Verify responsive design works correctly
  - Check that buttons and links are easily clickable

### 3. Email Authentication Testing
- [ ] **Test 5: Spam Score Testing**
  - Send test email to mail-tester.com
  - Verify spam score is acceptable (8/10 or higher)
  - Check DKIM signature validation
  - Confirm SPF record validation
  - Verify DMARC policy compliance

- [ ] **Test 6: Major Email Provider Testing**
  - Send test emails to Gmail account
  - Send test emails to Outlook/Hotmail account
  - Send test emails to Yahoo account
  - Send test emails to Apple iCloud account
  - Verify all emails arrive in inbox (not spam)

## Error Handling and Fallback Testing

### 4. Error Scenario Testing
- [ ] **Test 7: Invalid Credentials Handling**
  - Temporarily use invalid AWS SES credentials
  - Verify system attempts fallback to Gmail
  - Confirm error logging is appropriate
  - Test system recovery when credentials are restored

- [ ] **Test 8: Rate Limiting Testing**
  - Send multiple emails in quick succession
  - Verify rate limiting kicks in at appropriate threshold
  - Confirm system waits appropriately before retry
  - Test that emails continue after rate limit period

- [ ] **Test 9: Network Error Simulation**
  - Temporarily block access to AWS SES
  - Verify retry logic activates
  - Confirm fallback to Gmail works
  - Test system recovery when network is restored

### 5. Performance Testing
- [ ] **Test 10: Email Delivery Time**
  - Measure time from send command to email arrival
  - Target: Email delivery within 30 seconds
  - Test during different times of day
  - Verify consistent performance

- [ ] **Test 11: Large Content Handling**
  - Send email with large digest content (100+ articles)
  - Verify email size stays within limits
  - Check that formatting remains correct
  - Confirm delivery speed is acceptable

## User Experience Testing

### 6. End-User Workflow Testing
- [ ] **Test 12: Subscription Flow**
  - Test new user email subscription process
  - Verify welcome email is sent with correct branding
  - Check that user receives digest emails
  - Confirm preference management works

- [ ] **Test 13: Preference Management**
  - Click preference button in digest email
  - Verify preference page loads correctly
  - Test changing email preferences
  - Confirm preference changes are applied

- [ ] **Test 14: Unsubscribe Flow**
  - Click unsubscribe link in digest email
  - Verify unsubscribe page loads correctly
  - Complete unsubscribe process
  - Confirm user no longer receives emails

### 7. Brand and Content Testing
- [ ] **Test 15: Professional Branding**
  - Verify sender name appears as "Daily Scribe Editor"
  - Check that email signature is professional
  - Confirm logo and branding elements are correct
  - Verify contact information is accurate

- [ ] **Test 16: Content Localization**
  - Test emails with Portuguese content
  - Verify special characters display correctly
  - Check that date/time formatting is appropriate
  - Confirm language-specific elements work

## Security and Compliance Testing

### 8. Security Testing
- [ ] **Test 17: Email Header Security**
  - Verify no sensitive information in email headers
  - Check that tracking tokens are properly secured
  - Confirm preference URLs use HTTPS
  - Verify unsubscribe links are secure

- [ ] **Test 18: Data Privacy Compliance**
  - Verify emails include required privacy information
  - Check that unsubscribe mechanism is prominent
  - Confirm contact information is provided
  - Verify compliance with email marketing laws

### 9. Monitoring and Analytics
- [ ] **Test 19: Email Delivery Monitoring**
  - Check email delivery logs for errors
  - Verify success/failure rates are tracked
  - Confirm bounce rate monitoring works
  - Test alert system for delivery failures

- [ ] **Test 20: Performance Metrics**
  - Monitor email open rates (if tracking enabled)
  - Check click-through rates on preference buttons
  - Verify unsubscribe rate tracking
  - Confirm delivery time metrics collection

## Production Deployment Testing

### 10. Pre-Production Validation
- [ ] **Test 21: Staging Environment**
  - Deploy to staging environment
  - Test complete email workflow in staging
  - Verify environment-specific configurations
  - Confirm production secrets are properly secured

- [ ] **Test 22: Database Integration**
  - Test email delivery with production database copy
  - Verify user preference handling
  - Check subscription status management
  - Confirm data consistency

### 11. Production Deployment
- [ ] **Test 23: Gradual Rollout**
  - Deploy to small subset of users first
  - Monitor delivery rates and user feedback
  - Check for any unexpected issues
  - Gradually increase rollout scope

- [ ] **Test 24: Full Production Testing**
  - Test complete system under production load
  - Monitor all email metrics in real-time
  - Verify backup systems work correctly
  - Confirm monitoring alerts function properly

## Post-Deployment Monitoring

### 12. Ongoing Monitoring
- [ ] **Week 1: Daily Monitoring**
  - Monitor email delivery rates daily
  - Check bounce and complaint rates
  - Review user feedback and support requests
  - Track any delivery issues

- [ ] **Week 2-4: Regular Monitoring**
  - Review weekly delivery statistics
  - Monitor email authentication status
  - Check domain reputation metrics
  - Analyze user engagement metrics

- [ ] **Monthly: Performance Review**
  - Review monthly delivery performance
  - Analyze cost and usage metrics
  - Check for optimization opportunities
  - Plan for any needed improvements

## Issue Resolution

### 13. Common Issues and Solutions
- [ ] **Email Not Delivered**
  - Check AWS SES sending statistics
  - Verify recipient email address is valid
  - Check for bounces or complaints
  - Review email content for spam triggers

- [ ] **Email in Spam Folder**
  - Review spam score using mail-tester.com
  - Check DKIM/SPF/DMARC authentication
  - Verify sender reputation
  - Review email content and formatting

- [ ] **Slow Email Delivery**
  - Check AWS SES service status
  - Monitor network connectivity
  - Review rate limiting settings
  - Check for queue backlog

## Testing Tools and Resources

### 14. Recommended Testing Tools
- [ ] **Email Testing Services**
  - Mail-tester.com for spam score testing
  - SendForensics for deliverability analysis
  - Email on Acid for email client testing
  - Litmus for email preview testing

- [ ] **Monitoring Tools**
  - AWS SES console for delivery statistics
  - CloudWatch for metrics and alerts
  - Application logs for error tracking
  - Custom health check endpoints

### 15. Test Email Addresses
- [ ] **Primary Testing Addresses**
  - Personal Gmail account
  - Business email account
  - Mobile email access account
  - International email provider account

- [ ] **Spam Testing Addresses**
  - mail-tester.com test address
  - SpamAssassin test service
  - Delivery testing service addresses

## Test Results Documentation

### 16. Results Tracking
- [ ] **Create Test Results Log**
  - Document each test result
  - Record any issues found
  - Note performance metrics
  - Track resolution status

- [ ] **Performance Baseline**
  - Establish delivery time baselines
  - Record success rate benchmarks
  - Document spam score improvements
  - Set monitoring thresholds

## Success Criteria

### 17. Testing Completion Criteria
- [ ] All core functionality tests pass
- [ ] Email authentication is working correctly
- [ ] Spam scores are acceptable (8/10+)
- [ ] Major email providers accept emails
- [ ] Error handling works as expected
- [ ] Performance meets or exceeds targets
- [ ] User experience is smooth and professional
- [ ] Monitoring and alerts are functional

### 18. Sign-off Requirements
- [ ] Technical team approval
- [ ] Quality assurance sign-off
- [ ] Performance metrics approval
- [ ] Security review completion
- [ ] User acceptance testing completion
- [ ] Production deployment approval

---

## Notes and Comments

**Testing Environment:**
- Date: ___________
- Tester: ___________
- Environment: ___________
- Version: ___________

**Additional Notes:**
_Use this space to record any additional observations, issues, or recommendations discovered during testing._

---

## Quick Reference Commands

```bash
# Test email health
python scripts/email-health-check.py

# Check API health with email status
curl -s http://localhost:8000/healthz | jq

# Run email delivery tests
pytest tests/test_email_delivery.py -v

# Run email integration tests
pytest tests/test_email_integration.py -v

# Check AWS SES statistics
aws ses get-send-statistics

# Verify domain and DKIM status
aws ses get-identity-verification-attributes --identities dailyscribe.news
```

This checklist should be used systematically to ensure comprehensive testing of the email delivery system before and after deployment.
