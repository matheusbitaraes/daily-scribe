# User Story: Secure Email Preference Configuration

## Epic: User Personalization and Security

### Story: Email Preference Configuration with Secure Access

**As a** Daily Scribe user receiving email digests,  
**I want** to configure my email preferences including categories, sources, and keywords through a secure web interface,  
**so that** I can personalize my digest content and ensure only I can modify my settings.

---

## Background & Context

Currently, Daily Scribe have the tables with the customized categories for each user but that is not available to be modified by them. So, we need a screen to:
- Customize which categories they're interested in
- Select preferred news sources
- Set keywords for content filtering

This feature will provide a secure, user-specific configuration interface accessible via a button in the email digest, ensuring each user can only access and modify their own preferences.

---

## Detailed Requirements

### Functional Requirements

**FR1: Secure Access Mechanism**
- Each email digest shall contain a unique, secure "Configure Preferences" button/link
- The link shall contain an enhanced cryptographically secure token with multiple validation layers
- Tokens shall include device fingerprinting, usage limits, and shorter expiration (24 hours)
- Token validation shall include device fingerprinting and usage count tracking
- Invalid, expired, or overused tokens shall redirect to an error page with clear messaging
- System shall provide immediate token revocation capability for security events

**FR2: User Preference Interface**
- The preferences page shall display the current user's email address (read-only) for confirmation
- Users can select/deselect categories of interest (Technology, Politics, Business, Sports, etc.)
- Users can configure preferred news sources with checkboxes or multi-select
- Users can add custom keywords for content filtering (include/exclude lists)

**FR3: Preference Persistence**
- All preference changes shall be immediately saved to the database
- The system shall provide visual feedback when changes are saved successfully
- Users can reset preferences to default values
- The system shall maintain an audit log of preference changes for debugging

**FR4: Security Controls**
- Each user can only access their own preference page via their unique token
- Attempting to access another user's preferences shall result in access denied
- All preference API endpoints shall validate token ownership before allowing modifications
- Tokens shall be invalidated after password changes or account security events

**FR5: Email Integration**
- The "Configure Preferences" button in emails shall be prominently displayed
- The button shall open the preferences page in a new browser tab/window
- The preferences page shall work well on both desktop and mobile devices

---

## Technical Requirements

### TR1: Database Schema
### TR1: Database Schema
- Create `user_tokens` table for secure access token management with expiration
- Implement proper foreign key relationships and constraints

### TR2: API Endpoints
- `GET /preferences/{token}` - Retrieve user preferences by token
- `PUT /preferences/{token}` - Update user preferences
- `POST /preferences/{token}/reset` - Reset preferences to defaults
- All endpoints shall validate token authenticity and ownership

### TR3: Enhanced Token Security
- Use cryptographically secure random token generation (32+ bytes with secrets.token_urlsafe)
- Implement JWT tokens with device fingerprinting and usage tracking
- Token expiration reduced to 24 hours for improved security
- Store token metadata in database including device fingerprint hash and usage count
- Maximum usage limit per token (default: 10 uses) to prevent abuse
- Immediate token revocation capability for security events
- Security event logging for monitoring suspicious access attempts

#### Device Fingerprinting Implementation
```python
# Enhanced token creation with device fingerprinting
def create_preference_token(user_id: str, user_agent: str, ip_address: str) -> str:
    device_data = f"{user_agent}:{ip_address}"
    device_fingerprint = hashlib.sha256(device_data.encode()).hexdigest()[:16]
    
    token_id = secrets.token_urlsafe(32)
    payload = {
        "token_id": token_id,
        "user_id": user_id,
        "device_fp": device_fingerprint,
        "created_at": datetime.utcnow().isoformat(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "purpose": "email_preferences",
        "version": 1
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

#### Alternative Security Approaches Considered
1. **One-Time Passwords (OTP)**: Higher security but adds friction requiring email re-check
2. **Traditional Login**: Most secure but high abandonment rate for preference changes
3. **Magic Links with longer expiration**: Current approach balances security and UX
4. **JWT with refresh tokens**: More complex but allows longer sessions with security

### TR4: Frontend Implementation
- Create responsive React components for preference configuration
- Implement form validation and error handling
- Add loading states and success/error notifications
- Ensure accessibility compliance (ARIA labels, keyboard navigation)

---

## User Interface Requirements

### UI1: Email Button
- Clear, prominent "⚙️ Configure Email Preferences" button in digest emails
- Button styling consistent with email design
- Hover states and clear call-to-action
- make this button appear in the beginning of the email digest

### UI2: Preferences Page Layout
```
┌─────────────────────────────────────────────┐
│ Daily Scribe - Email Preferences            │
│ Configuring for: user@example.com           │
├─────────────────────────────────────────────┤
│                                             │
│ 📊 Categories of Interest                   │
│ ☑ Technology     ☑ Business     ☐ Sports   │
│ ☑ Politics       ☐ Entertainment ☐ Health  │
│                                             │
│ 📰 Preferred Sources                        │
│ ☑ Reuters        ☑ AP News      ☐ CNN      │
│ ☑ BBC           ☐ The Guardian   ☐ NPR      │
│                                             │
│ 🔍 Keywords:[AI, machine learning, startups] │
│                                             │
│ [Save Changes] [Reset to Defaults]          │
└─────────────────────────────────────────────┘
```

### UI3: Mobile Responsiveness
- Stack sections vertically on mobile devices
- Touch-friendly checkbox and button sizes
- Readable text sizes without zooming

---

## Security Analysis and Implementation

### Token-Based Approach Analysis

#### ✅ **Advantages:**
- **Frictionless UX**: One-click access from email
- **No additional authentication**: Users don't need to remember passwords
- **Stateless**: Tokens can be validated without session storage
- **Time-limited**: Automatic expiration reduces long-term risk

#### ❌ **Challenges:**
- **Email vulnerability**: If email is compromised, token is exposed
- **URL sharing risk**: Users might accidentally share preference links
- **Limited revocation**: Hard to invalidate specific tokens quickly
- **Replay attacks**: Token can be used multiple times until expiration

### Alternative Security Approaches Evaluated

#### 1. One-Time Passwords (OTP)
```python
# When user clicks email button, generate 6-digit code
# User enters code on preferences page
def generate_otp(user_id: str) -> str:
    code = secrets.randbelow(900000) + 100000  # 6-digit code
    cache.set(f"otp:{user_id}", str(code), expire=300)  # 5-minute expiration
    return str(code)
```
**Trade-offs:**
- ✅ More secure (requires active user verification)
- ❌ Extra friction (user must check email again)

#### 2. Email + Password Authentication
```python
# Traditional login flow with redirect
@app.route("/login")
def login_with_redirect():
    return_url = request.args.get("return_url", "/preferences")
    # Standard username/password flow
    # Redirect to preferences after successful auth
```
**Trade-offs:**
- ✅ Most secure (user must know password)
- ✅ Familiar UX pattern
- ❌ High friction (many users won't complete flow)

#### 3. JWT with Short Expiration + Refresh
```python
# Short-lived access token (15 min) + longer refresh token
def create_token_pair(user_id: str):
    access_token = jwt.encode({
        "user_id": user_id,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }, SECRET_KEY)
    
    refresh_token = jwt.encode({
        "user_id": user_id,
        "type": "refresh", 
        "exp": datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY)
    
    return access_token, refresh_token
```
**Trade-offs:**
- ✅ Better security (short-lived tokens)
- ✅ Automatic refresh
- ❌ More complex implementation

### Recommended Enhanced Token System

```python
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SecureToken:
    """Enhanced secure token with multiple validation layers"""
    user_id: str
    token_hash: str
    device_fingerprint: str
    created_at: datetime
    expires_at: datetime
    usage_count: int = 0
    max_usage: int = 10  # Limit token reuse

class SecureTokenManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_preference_token(
        self, 
        user_id: str, 
        user_agent: str, 
        ip_address: str,
        expiry_hours: int = 24  # Much shorter than 30 days
    ) -> str:
        """Create a secure, limited-use preference token"""
        
        # Create device fingerprint
        device_data = f"{user_agent}:{ip_address}"
        device_fingerprint = hashlib.sha256(device_data.encode()).hexdigest()[:16]
        
        # Generate cryptographically secure token
        token_id = secrets.token_urlsafe(32)
        
        # Create JWT with multiple validation factors
        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "device_fp": device_fingerprint,
            "created_at": datetime.utcnow().isoformat(),
            "exp": datetime.utcnow() + timedelta(hours=expiry_hours),
            "purpose": "email_preferences",
            "version": 1  # For token format versioning
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Store token metadata in database for validation
        self._store_token_metadata(token_id, user_id, device_fingerprint, expiry_hours)
        
        return token
    
    def validate_token(
        self, 
        token: str, 
        user_agent: str, 
        ip_address: str
    ) -> Optional[str]:
        """Validate token with multiple security checks"""
        
        try:
            # Decode JWT
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Extract token data
            token_id = payload["token_id"]
            user_id = payload["user_id"]
            stored_device_fp = payload["device_fp"]
            
            # Validate device fingerprint
            current_device_data = f"{user_agent}:{ip_address}"
            current_device_fp = hashlib.sha256(current_device_data.encode()).hexdigest()[:16]
            
            if current_device_fp != stored_device_fp:
                self._log_security_event("device_mismatch", token_id, user_id)
                return None
            
            # Check token metadata in database
            token_metadata = self._get_token_metadata(token_id)
            if not token_metadata or token_metadata.usage_count >= token_metadata.max_usage:
                self._log_security_event("usage_exceeded", token_id, user_id)
                return None
            
            # Increment usage count
            self._increment_token_usage(token_id)
            
            return user_id
            
        except jwt.InvalidTokenError:
            return None
    
    def revoke_user_tokens(self, user_id: str) -> None:
        """Revoke all tokens for a user (e.g., on password change)"""
        # Implementation to invalidate all user tokens
        pass
    
    def _store_token_metadata(self, token_id: str, user_id: str, device_fp: str, expiry_hours: int):
        """Store token metadata for validation"""
        # Implementation to store in database
        pass
    
    def _get_token_metadata(self, token_id: str) -> Optional[SecureToken]:
        """Retrieve token metadata"""
        # Implementation to fetch from database
        pass
    
    def _increment_token_usage(self, token_id: str):
        """Track token usage"""
        # Implementation to increment usage counter
        pass
    
    def _log_security_event(self, event_type: str, token_id: str, user_id: str):
        """Log security events for monitoring"""
        # Implementation for security logging
        pass
```

### Key Security Enhancements

1. **Device Fingerprinting**: Ties token to specific browser/device combination
2. **Usage Limits**: Token becomes invalid after maximum uses (default: 10)
3. **Shorter Expiration**: 24 hours instead of 30 days reduces exposure window
4. **Security Logging**: Comprehensive audit trail for suspicious activities
5. **Immediate Revocation**: Can invalidate all user tokens instantly
6. **Multi-layer Validation**: JWT + database metadata + device fingerprint

### Security Event Monitoring

The system shall log and monitor:
- Invalid token usage attempts
- Device fingerprint mismatches
- Usage limit exceeded events
- Expired token access attempts
- Suspicious access patterns (multiple failed validations)

---

## Acceptance Criteria

### AC1: Email Access
- ✅ Email digest contains working "Configure Preferences" button
- ✅ Button opens preferences page in new tab with user's current settings loaded
- ✅ Invalid tokens show appropriate error message

### AC2: Preference Management
- ✅ Users can select/deselect categories and see changes reflected immediately
- ✅ Users can add/remove preferred sources
- ✅ Users can manage keyword include/exclude lists

### AC3: Security Validation
- ✅ User A cannot access User B's preferences even with token manipulation
- ✅ Expired tokens properly redirect to error page
- ✅ All preference changes are validated server-side

### AC4: Persistence and Feedback
- ✅ Preference changes are saved immediately and persist across sessions
- ✅ Success/error messages are displayed for user actions
- ✅ Reset functionality works correctly

---

## Security Considerations

### Data Protection
- Tokens shall be transmitted over HTTPS only
- Preference data shall be properly sanitized before storage
- User input validation on both client and server side

### Access Control
- Implement rate limiting on preference endpoints
- Log access attempts for security monitoring
- Provide mechanism to revoke all tokens for a user

### Privacy
- Allow users to delete their account and all associated data
- Provide clear privacy policy about data usage
- Enable users to export their preference data

---

## Implementation Priority

1. **Phase 1:** Database schema and basic token system
2. **Phase 2:** API endpoints with security validation
3. **Phase 3:** Basic frontend preference interface
4. **Phase 4:** Email integration and button implementation
5. **Phase 5:** Mobile responsiveness and UX polish
6. **Phase 6:** Advanced features (audit logging, token refresh)

---

## Dependencies

- Existing email digest system
- User management/database system
- Frontend framework (React)
- Email template system
- HTTPS/SSL certificate for secure token transmission

---

## Success Metrics

- User preference adoption rate (target: >60% of active users)
- Preference page bounce rate (target: <20%)
- Token security incidents (target: 0)
- User satisfaction with personalization features
- Reduction in unsubscribe rates due to better customization

---

## Future Enhancements

- A/B testing for different digest layouts
- AI-powered content recommendations based on reading history
- Social sharing preferences
- Digest preview before delivery
