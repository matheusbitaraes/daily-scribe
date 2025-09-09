# Task Breakdown: Custom Domain Email Migration

## Executive Summary

This task involves migrating from the current personal Gmail-based email system to a professional custom domain email setup for Daily Scribe. The migration will enhance the platform's credibility, improve deliverability, and provide better branding for the news digest service. The implementation includes setting up a custom domain, configuring email services, updating all email-related code, and ensuring proper email authentication.

## Analysis Phase

### Current State
- **Email Provider**: Gmail (smtp.gmail.com)
- **From Address**: matheusbitaraesdenovaes@gmail.com
- **Authentication**: App-specific password
- **Configuration**: Hardcoded in config.json
- **Usage**: Daily digest delivery, preference management, subscription/unsubscription

### Target State
- **Custom Domain**: dailyscribe.news
- **Email Addresses**: 
  - noreply@dailyscribe.news (digest delivery)
  - admin@dailyscribe.news (administrative communications)
  - support@dailyscribe.news (user support)
- **Provider Options**: AWS SES, SendGrid, Mailgun, or Google Workspace
- **Enhanced Features**: Better deliverability, SPF/DKIM/DMARC, professional branding

### Impact Assessment
- **Backend Changes**: Email configuration, SMTP settings, sender addresses
- **Frontend Changes**: Email display in UI, branding updates
- **Documentation**: Email setup guides, configuration instructions
- **Testing**: Email delivery, authentication, deliverability testing

---

## Task Breakdown Structure

## Phase 1: Domain and Email Service Setup

### Task 1: Domain Registration and DNS Configuration
**Type:** Infrastructure  
**Priority:** High  
**Estimated Time:** 2-4 hours  
**Dependencies:** None

#### Description
Register a custom domain for Daily Scribe and configure DNS settings to support email delivery with proper authentication records.

#### Technical Details
- **Domain Options**: dailyscribe.news, daily-scribe.com, or similar
- **DNS Provider**: Cloudflare, AWS Route 53, or domain registrar
- **Required Records**: MX, SPF, DKIM, DMARC
- **Subdomain Strategy**: Use mail.dailyscribe.news for email services

#### Acceptance Criteria
- [x] Domain registered and active
- [x] DNS zone configured with email provider requirements
- [ ] MX records pointing to chosen email service (optional - Reply-To implemented instead)
- [ ] SPF record configured for email authentication (**NEEDED**)
- [x] Initial DKIM and DMARC records in place
- [x] Domain propagation verified (24-48 hours)

#### Notes/Considerations
- Choose domain that's memorable and professional
- Consider future branding and expansion plans
- Ensure domain doesn't conflict with existing services
- Plan for email service provider migration flexibility

---

### Task 2: Email Service Provider Selection and Setup
**Type:** Infrastructure  
**Priority:** High  
**Estimated Time:** 3-6 hours  
**Dependencies:** Task 1 (Domain registration)

#### Description
Research, select, and configure a professional email service provider that offers SMTP services, good deliverability, and reasonable pricing for Daily Scribe's volume.

#### Technical Details
- **Provider Options**: 
  - AWS SES (cost-effective, good integration)
  - SendGrid (reliable, good UI)
  - Mailgun (developer-friendly)
  - Google Workspace (familiar interface)
- **Configuration**: SMTP credentials, sending limits, authentication
- **Features Needed**: SMTP relay, deliverability tracking, bounce handling

#### Acceptance Criteria
- [x] Email service provider account created and verified
- [x] Domain verified with chosen provider
- [x] SMTP credentials generated and tested
- [x] Sending limits understood and documented
- [x] DKIM keys generated and added to DNS
- [x] Test email successfully sent and received
- [x] Deliverability monitoring configured

#### Progress Notes
- ✅ AWS SES selected as email provider
- ✅ DNS configuration documented with actual values
- ✅ AWS account configured and working
- ✅ Domain added to AWS SES (✅ **VERIFIED!**)
- ✅ DKIM tokens generated (✅ **VERIFIED!**)
- ✅ DNS records added to GoDaddy
- ✅ SMTP credentials generated and configured in .env
- ✅ Configuration system updated to load .env file
- ✅ Email verification completed in AWS SES
- ✅ **Email sent successfully from noreply@dailyscribe.news**
- ✅ AWS SES fully functional and ready for production

#### Notes/Considerations
- Start with AWS SES for cost-effectiveness
- Ensure provider supports needed email volume (current ~10 emails/day)
- Plan for growth and increased volume
- Consider backup provider strategy
- Document setup process for reproducibility

---

## Phase 2: Backend Email System Migration

### Task 3: Email Configuration Refactoring
**Type:** Backend  
**Priority:** High  
**Estimated Time:** 4-6 hours  
**Dependencies:** Task 2 (Email service setup)

#### Description
Refactor the email configuration system to support multiple email addresses for different purposes and new SMTP settings.

#### Technical Details
- **Files to Modify**:
  - `config.json` - Email configuration structure
  - `src/components/notifier.py` - SMTP configuration
  - `src/components/email_service.py` - Sender address logic
- **New Configuration Structure**:
  ```json
  {
    "email": {
      "provider": "aws_ses",
      "smtp_server": "email-smtp.us-east-1.amazonaws.com",
      "smtp_port": 587,
      "username": "AKIAIOSFODNN7EXAMPLE",
      "addresses": {
        "noreply": "noreply@dailyscribe.news",
        "admin": "admin@dailyscribe.news",
        "support": "support@dailyscribe.news"
      }
    }
  }
  ```

#### Acceptance Criteria
- [x] New email configuration structure implemented
- [x] Multiple sender addresses supported
- [x] SMTP configuration updated for new provider
- [x] Environment variable support for sensitive credentials
- [x] Backward compatibility maintained during transition
- [x] Configuration validation implemented
- [x] All email sending functions updated

#### Notes/Considerations
- Keep sensitive credentials in environment variables
- Implement configuration validation to prevent errors
- Consider email address rotation capabilities
- Plan for gradual migration to minimize disruption

---

### Task 4: Email Service Provider Integration
**Type:** Backend  
**Priority:** High  
**Estimated Time:** 6-8 hours  
**Dependencies:** Task 3 (Configuration refactoring)

#### Description
Integrate the chosen email service provider's SDK or SMTP service into the Daily Scribe backend, replacing the current Gmail integration.

#### Technical Details
- **Files to Modify**:
  - `src/components/notifier.py` - SMTP client implementation
  - `requirements.txt` - Add email provider SDK
  - `src/components/email_service.py` - Update sender logic
- **Provider-Specific Integration**:
  - AWS SES: Use boto3 SDK or SMTP
  - SendGrid: Use sendgrid-python SDK
  - Mailgun: Use requests library or SDK
- **Features to Implement**:
  - Delivery status tracking
  - Bounce/complaint handling
  - Email templates support

#### Acceptance Criteria
- [x] Email provider SDK integrated and configured
- [x] SMTP authentication working with new credentials
- [x] All email types (digest, preferences, unsubscribe) functional
- [x] Error handling for email service failures
- [x] Delivery tracking and logging implemented
- [ ] Bounce and complaint handling configured (AWS SES console setup needed)
- [x] Rate limiting and retry logic implemented

#### Progress Notes
- ✅ AWS SES SMTP integration fully functional
- ✅ Enhanced EmailNotifier with delivery tracking, rate limiting (14 emails/min), and retry logic
- ✅ Exponential backoff retry strategy (3 attempts with 2s, 4s, 8s delays)
- ✅ Comprehensive logging for email delivery monitoring
- ✅ Reply-To functionality working (replies go to personal Gmail)
- ✅ Legacy fallback maintained for reliability
- ⚠️ Bounce/complaint handling requires AWS SES console configuration (SNS topics)

#### Notes/Considerations
- Implement proper error handling for service outages
- Add monitoring for email delivery failures
- Consider implementing email queue for high volume
- Plan for provider-specific feature utilization

---

### Task 5: Email Template and Branding Updates
**Type:** Backend/Frontend  
**Priority:** Medium  
**Estimated Time:** 4-6 hours  
**Dependencies:** Task 4 (Provider integration)

#### Description
Update all email templates to use the new custom domain addresses and improve branding consistency across all email communications.

#### Technical Details
- **Files to Modify**:
  - `src/components/digest_builder.py` - Email HTML templates
  - `src/components/email_service.py` - Preference button links
  - Email template CSS and styling
- **Updates Required**:
  - From addresses using custom domain
  - Footer branding and contact information
  - Unsubscribe links with new domain
  - Preference management links
  - Logo and visual branding

#### Acceptance Criteria
- [ ] All email templates updated with new domain addresses
- [ ] Consistent branding across all email types
- [ ] Professional footer with contact information
- [ ] Updated unsubscribe and preference links
- [ ] Mobile-responsive email templates
- [ ] Brand logo integrated in emails
- [ ] Legal compliance text updated

#### Notes/Considerations
- Maintain consistent visual identity
- Ensure mobile responsiveness
- Include required legal compliance text
- Test across different email clients
- Consider internationalization for Portuguese users

---

## Phase 3: Configuration and Environment Updates

### Task 6: Environment Variable Management
**Type:** Backend  
**Priority:** Medium  
**Estimated Time:** 2-3 hours  
**Dependencies:** Task 3 (Configuration refactoring)

#### Description
Implement secure environment variable management for email credentials and migrate sensitive information out of config files.

#### Technical Details
- **Files to Create/Modify**:
  - `.env.example` - Template for environment variables
  - `src/utils/config_loader.py` - Environment variable loading
  - `docker-compose.yml` - Environment configuration
  - Documentation for environment setup
- **Environment Variables**:
  ```env
  EMAIL_SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE
  EMAIL_SMTP_PASSWORD=BM+7XYZ1234567890
  EMAIL_FROM_NOREPLY=noreply@dailyscribe.news
  EMAIL_FROM_ADMIN=admin@dailyscribe.news
  EMAIL_FROM_SUPPORT=support@dailyscribe.news
  ```

#### Acceptance Criteria
- [x] Sensitive email credentials moved to environment variables
- [x] `.env.example` file created with all required variables
- [x] Configuration loader updated to use environment variables
- [x] Docker Compose configuration updated
- [x] Development setup documentation updated
- [x] Production deployment guide updated
- [x] Validation for required environment variables

#### Notes/Considerations
- Never commit actual credentials to version control
- Provide clear setup instructions for developers
- Implement fallback behavior for missing variables
- Consider using secret management tools for production

---

### Task 7: Docker and Deployment Configuration
**Type:** DevOps  
**Priority:** Medium  
**Estimated Time:** 3-4 hours  
**Dependencies:** Task 6 (Environment variables)

#### Description
Update Docker configuration and deployment scripts to support the new email service provider and custom domain setup.

#### Technical Details
- **Files to Modify**:
  - `docker-compose.yml` - Environment variables
  - `docker-compose.prod.yml` - Production email settings
  - `Dockerfile` - Dependencies for email provider
  - Deployment scripts and documentation
- **Configuration Updates**:
  - Email service provider SDK dependencies
  - Environment variable mappings
  - Health checks for email connectivity
  - Volume mounts for configuration files

#### Acceptance Criteria
- [x] Docker containers build with new email dependencies
- [x] Environment variables properly configured in containers
- [x] Production deployment updated with new email settings
- [x] Health checks include email service connectivity
- [x] Documentation updated for deployment process
- [x] Backup email configuration strategy documented
- [x] Container restart policies configured

#### Notes/Considerations
- Ensure email service connectivity in containerized environment
- Plan for email service outages and fallback strategies
- Document the complete deployment process
- Consider using Docker secrets for production credentials

---

## Phase 4: Testing and Quality Assurance

### Task 8: Email Delivery Testing Suite
**Type:** Testing  
**Priority:** High  
**Estimated Time:** 4-5 hours  
**Dependencies:** Task 4 (Provider integration)

#### Description
Create comprehensive tests for email delivery functionality, including unit tests, integration tests, and manual testing procedures.

#### Technical Details
- **Files to Create/Modify**:
  - `tests/test_email_delivery.py` - Email delivery tests
  - `tests/test_email_integration.py` - Integration tests
  - Manual testing checklist and procedures
- **Test Coverage**:
  - SMTP connectivity and authentication
  - Email template rendering
  - Different email types (digest, preferences, etc.)
  - Error handling and retry logic
  - Deliverability and spam score testing

#### Acceptance Criteria
- [ ] Unit tests for all email-related functions
- [ ] Integration tests with email service provider
- [ ] Mock email testing for development
- [ ] Manual testing checklist created
- [ ] Spam score testing with mail-tester.com
- [ ] Cross-platform email client testing
- [ ] Error handling and retry logic tested

#### Notes/Considerations
- Use email testing services for spam score verification
- Test with various email clients (Gmail, Outlook, etc.)
- Implement proper mocking for unit tests
- Document manual testing procedures

---

### Task 9: Migration Testing and Validation
**Type:** Testing  
**Priority:** High  
**Estimated Time:** 3-4 hours  
**Dependencies:** Task 8 (Email testing suite)

#### Description
Conduct thorough testing of the migration from personal Gmail to custom domain email system to ensure all functionality works correctly.

#### Technical Details
- **Testing Scenarios**:
  - Daily digest delivery with new sender address
  - Preference management emails
  - Subscription and unsubscription flows
  - Error handling and fallback scenarios
  - Performance and delivery time testing
- **Validation Points**:
  - Email authentication (SPF, DKIM, DMARC)
  - Deliverability to major email providers
  - Mobile email client compatibility
  - Link functionality in emails

#### Acceptance Criteria
- [ ] All email types delivered successfully with new domain
- [ ] Email authentication passes verification
- [ ] Deliverability tested across major email providers
- [ ] Mobile email client compatibility verified
- [ ] All links in emails functional and correct
- [ ] Error scenarios handled gracefully
- [ ] Performance meets or exceeds current delivery times

#### Notes/Considerations
- Test with real user email addresses during migration
- Monitor delivery rates and bounce rates
- Document any issues and resolution steps
- Plan for rollback if critical issues arise

---

## Phase 5: Documentation and User Communication

### Task 10: Documentation Updates
**Type:** Documentation  
**Priority:** Medium  
**Estimated Time:** 3-4 hours  
**Dependencies:** Task 9 (Migration validation)

#### Description
Update all project documentation to reflect the new custom domain email system and provide setup instructions for developers and administrators.

#### Technical Details
- **Files to Update**:
  - `README.md` - Email configuration section
  - `docs/environment-variables-guide.md` - Email variables
  - `docs/deployment-checklist.md` - Email service setup
  - `docs/user-guide.md` - Updated sender addresses
  - API documentation for email-related endpoints
- **New Documentation**:
  - Email service provider setup guide
  - Email authentication configuration guide
  - Troubleshooting guide for email delivery issues

#### Acceptance Criteria
- [ ] All documentation updated with new email addresses
- [ ] Email service provider setup guide created
- [ ] Environment variable documentation complete
- [ ] Deployment checklist includes email configuration
- [ ] User guide reflects new sender addresses
- [ ] Troubleshooting guide for email issues created
- [ ] API documentation updated for email endpoints

#### Notes/Considerations
- Include screenshots and step-by-step instructions
- Document common issues and solutions
- Provide guidance for different deployment scenarios
- Keep documentation up-to-date with any changes

---

### Task 11: User Communication and Migration Notice
**Type:** Communication  
**Priority:** Low  
**Estimated Time:** 2-3 hours  
**Dependencies:** Task 9 (Migration validation)

#### Description
Prepare and send communication to existing users about the email sender address change and any actions they need to take.

#### Technical Details
- **Communication Methods**:
  - Email announcement about sender address change
  - Website notice during the transition period
  - Update to email signatures and footers
- **Content to Include**:
  - Explanation of the change and benefits
  - New sender addresses to whitelist
  - Instructions for updating email filters
  - Contact information for support

#### Acceptance Criteria
- [ ] User communication email drafted and reviewed
- [ ] Website notice prepared for transition period
- [ ] Email signatures updated with new addresses
- [ ] Support documentation for user questions created
- [ ] Communication sent to all active users
- [ ] User support process documented
- [ ] Feedback collection mechanism implemented

#### Notes/Considerations
- Send communication well before the migration
- Provide clear instructions for users
- Monitor for increased support requests
- Consider gradual rollout to minimize impact

---

## Implementation Timeline

### Week 1: Infrastructure Setup
- **Days 1-2**: Domain registration and DNS configuration (Tasks 1-2)
- **Days 3-5**: Email service provider setup and testing

### Week 2: Backend Development
- **Days 1-3**: Email configuration refactoring (Task 3)
- **Days 4-5**: Provider integration and testing (Task 4)

### Week 3: Configuration and Testing
- **Days 1-2**: Environment and deployment configuration (Tasks 6-7)
- **Days 3-5**: Comprehensive testing and validation (Tasks 8-9)

### Week 4: Documentation and Launch
- **Days 1-2**: Documentation updates (Task 10)
- **Days 3-4**: User communication and final preparation (Task 11)
- **Day 5**: Migration execution and monitoring

## Resource Requirements

### Technical Skills
- **Domain Management**: DNS configuration, domain registration
- **Email Services**: SMTP configuration, email authentication
- **Backend Development**: Python, email libraries, configuration management
- **DevOps**: Docker, environment configuration, deployment
- **Testing**: Unit testing, integration testing, email delivery testing

### Tools and Services
- **Domain Registrar**: Namecheap, GoDaddy, or similar
- **DNS Provider**: Cloudflare, AWS Route 53
- **Email Service**: AWS SES, SendGrid, or Mailgun
- **Email Testing**: mail-tester.com, SendForensics
- **Monitoring**: Email delivery monitoring tools

### Budget Considerations
- **Domain Registration**: $10-20/year
- **Email Service**: $5-50/month depending on volume
- **DNS Service**: Free to $5/month
- **Email Testing Tools**: Free to $20/month

## Risk Assessment

### Technical Risks
- **Email Deliverability**: New domain may have lower initial reputation
  - *Mitigation*: Warm up domain gradually, implement proper authentication
- **Service Provider Outages**: Email service dependency
  - *Mitigation*: Implement fallback provider, monitor service status
- **Configuration Errors**: Incorrect SMTP or DNS settings
  - *Mitigation*: Thorough testing, documentation, rollback plan

### Business Risks
- **User Confusion**: Users may not recognize new sender address
  - *Mitigation*: Clear communication, gradual transition
- **Spam Filtering**: Emails may be filtered as spam initially
  - *Mitigation*: Authentication setup, user whitelisting instructions
- **Migration Downtime**: Temporary email delivery issues
  - *Mitigation*: Careful timing, monitoring, quick rollback capability

### Operational Risks
- **Increased Support**: Users may need help with email changes
  - *Mitigation*: Prepare support documentation, clear instructions
- **Cost Overruns**: Email service costs higher than expected
  - *Mitigation*: Monitor usage, implement cost alerts

## Success Criteria

### Technical Success
- ✅ All emails delivered successfully with new custom domain
- ✅ Email authentication (SPF, DKIM, DMARC) passes verification
- ✅ 99%+ delivery rate maintained or improved
- ✅ Email delivery times within acceptable ranges
- ✅ All email functionality working (digest, preferences, unsubscribe)

### User Experience Success
- ✅ No increase in user-reported email delivery issues
- ✅ Improved email reputation and deliverability
- ✅ Professional branding enhances user trust
- ✅ Smooth transition with minimal user confusion

### Operational Success
- ✅ Reduced dependency on personal email accounts
- ✅ Improved monitoring and analytics for email delivery
- ✅ Scalable email infrastructure for future growth
- ✅ Proper documentation and procedures in place

## Post-Migration Monitoring

### Metrics to Track
- **Delivery Rates**: Track successful email delivery percentages
- **Bounce Rates**: Monitor hard and soft bounces
- **User Engagement**: Open rates and click-through rates
- **Support Requests**: Monitor for email-related user issues
- **Authentication**: Track SPF, DKIM, and DMARC pass rates

### Monitoring Period
- **Week 1**: Daily monitoring of all metrics
- **Month 1**: Weekly monitoring and adjustment
- **Ongoing**: Monthly review and optimization

### Optimization Actions
- Adjust email authentication settings based on feedback
- Fine-tune spam score optimization
- Update documentation based on real-world experience
- Plan for additional features like email analytics

---

## Appendix

### Email Provider Comparison

| Provider | Pros | Cons | Cost | Best For |
|----------|------|------|------|----------|
| AWS SES | Very cost-effective, integrates with AWS | Setup complexity | $0.10/1000 emails | Cost-conscious, AWS users |
| SendGrid | Easy setup, good analytics | Higher cost | $14.95/month | Quick deployment |
| Mailgun | Developer-friendly, good API | Limited free tier | $35/month | High-volume sending |
| Google Workspace | Familiar interface, integrated | Higher cost, less flexibility | $6/user/month | Small teams, simplicity |

### Sample Configuration Files

#### .env.example
```env
# Email Service Configuration
EMAIL_PROVIDER=aws_ses
EMAIL_SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE
EMAIL_SMTP_PASSWORD=BM+7XYZ1234567890

# Email Addresses
EMAIL_FROM_NOREPLY=noreply@dailyscribe.news
EMAIL_FROM_ADMIN=admin@dailyscribe.news
EMAIL_FROM_SUPPORT=support@dailyscribe.news

# Email Settings
EMAIL_RATE_LIMIT=14
EMAIL_RETRY_ATTEMPTS=3
EMAIL_TIMEOUT=30
```

#### DNS Records Example
```
# MX Records
dailyscribe.news. MX 10 inbound-smtp.us-east-1.amazonaws.com.

# SPF Record
dailyscribe.news. TXT "v=spf1 include:amazonses.com ~all"

# DKIM Records (generated by email provider)
selector1._domainkey.dailyscribe.news. CNAME selector1.dailyscribe.news.dkim.amazonses.com.

# DMARC Record
_dmarc.dailyscribe.news. TXT "v=DMARC1; p=quarantine; rua=mailto:admin@dailyscribe.news"
```

---

## Relevant Files

### Backend Files - Task 3 Completed ✅
- `config.json` - Updated email configuration structure for AWS SES
- `src/components/config.py` - Enhanced EmailConfig class with multi-address support and environment variables
- `src/components/notifier.py` - Updated EmailNotifier with custom sender addresses and legacy fallback
- `.env.example` - Added email service environment variables template
- `.specs/.tasks/aws-ses-dns-setup.md` - DNS configuration guide for AWS SES

### Configuration Files Modified
- Email configuration now supports AWS SES and multiple sender addresses
- Environment variables for secure credential management
- Backward compatibility with existing Gmail configuration
- Legacy fallback system for seamless migration
