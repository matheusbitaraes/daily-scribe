# Manual Testing Guide for Unsubscription Flow

This document provides step-by-step instructions for manually testing the complete unsubscription journey.

## Prerequisites

1. **Backend Server Running**
   - Start the API server: `uvicorn api:app --app-dir src --reload`
   - Verify running at: http://localhost:8000

2. **Frontend Server Running**
   - Navigate to frontend directory: `cd frontend`
   - Start the frontend: `npm start`
   - Verify running at: http://localhost:3000

3. **Test Database Setup**
   - Ensure you have a test subscription in the database
   - You can create one using the subscription API endpoint

## Test Scenarios

### 1. Complete Happy Path Test

**Objective**: Test the full unsubscription flow from email to confirmation

**Steps**:
1. **Generate Test Token**
   ```bash
   curl -X POST "http://localhost:8000/api/create-unsubscribe-token" \
        -H "Content-Type: application/json" \
        -d '{"email": "test@example.com"}'
   ```
   
2. **Note the Token**
   - Copy the `token` value from the response
   - Example: `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

3. **Access Unsubscribe Page**
   - Open: `http://localhost:3000/unsubscribe/{TOKEN}`
   - Replace `{TOKEN}` with the actual token

4. **Verify Page Elements**
   - [ ] Page loads without errors
   - [ ] "Confirm Unsubscription" heading visible
   - [ ] Explanation text about email unsubscription
   - [ ] "Yes, Unsubscribe Me" button visible
   - [ ] "Cancel" button visible
   - [ ] Responsive design on mobile/desktop

5. **Test Confirmation Flow**
   - Click "Yes, Unsubscribe Me"
   - [ ] Button shows "Processing..." state
   - [ ] Buttons are disabled during processing
   - [ ] Success page appears with confirmation message
   - [ ] Email address is displayed correctly
   - [ ] "Return to Homepage" button works
   - [ ] "Subscribe Again" button works

6. **Verify Backend State**
   ```bash
   curl -X GET "http://localhost:8000/api/subscription-status/test@example.com"
   ```
   - [ ] Status should be "unsubscribed"
   - [ ] `unsubscribed_at` timestamp should be recent

### 2. Invalid Token Test

**Objective**: Test error handling for invalid/expired tokens

**Steps**:
1. **Use Invalid Token**
   - Access: `http://localhost:3000/unsubscribe/invalid-token-123`

2. **Verify Error Handling**
   - Click "Yes, Unsubscribe Me"
   - [ ] Error page appears
   - [ ] "Unsubscription Failed" heading visible
   - [ ] Clear error message about invalid/expired link
   - [ ] "Try Again" button works (returns to confirmation)
   - [ ] "Return to Homepage" button works

### 3. Missing Token Test

**Objective**: Test handling of missing token parameter

**Steps**:
1. **Access Without Token**
   - Navigate to: `http://localhost:3000/unsubscribe/`

2. **Verify Error Handling**
   - [ ] Error message: "No unsubscribe token provided"
   - [ ] "Return to Homepage" button works

### 4. Network Error Test

**Objective**: Test handling of network connectivity issues

**Steps**:
1. **Stop Backend Server**
   - Stop the uvicorn server

2. **Attempt Unsubscription**
   - Use a valid token format
   - Click "Yes, Unsubscribe Me"

3. **Verify Network Error Handling**
   - [ ] Error page appears
   - [ ] Network error message displayed
   - [ ] "Try Again" button works
   - [ ] Can retry after restarting server

### 5. Already Unsubscribed Test

**Objective**: Test handling of already unsubscribed emails

**Steps**:
1. **Use Token for Already Unsubscribed Email**
   - First unsubscribe an email successfully
   - Try to use another token for the same email

2. **Verify Graceful Handling**
   - [ ] Appropriate message for already unsubscribed status
   - [ ] No error state, just informational message

### 6. Token Expiry Test

**Objective**: Test token expiration (72-hour limit)

**Steps**:
1. **Simulate Expired Token**
   - Wait 72+ hours with a real token, OR
   - Modify token creation to use past timestamp for testing

2. **Verify Expiry Handling**
   - [ ] Clear message about expired link
   - [ ] Option to request new unsubscribe link

### 7. Token Usage Limit Test

**Objective**: Test 3-use limit on tokens

**Steps**:
1. **Use Same Token Multiple Times**
   - Use a token 3 times successfully
   - Try to use it a 4th time

2. **Verify Usage Limit**
   - [ ] First 3 uses work normally
   - [ ] 4th use shows appropriate error
   - [ ] Error explains token usage limit

### 8. Mobile Responsiveness Test

**Objective**: Test responsive design on various screen sizes

**Steps**:
1. **Test Different Screen Sizes**
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)

2. **Verify Responsive Elements**
   - [ ] Page layout adapts to screen size
   - [ ] Buttons remain accessible
   - [ ] Text is readable at all sizes
   - [ ] Navigation works on touch devices

### 9. Browser Compatibility Test

**Objective**: Test across different browsers

**Browsers to Test**:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Verify**:
- [ ] Page loads correctly
- [ ] JavaScript functionality works
- [ ] CSS styling appears correctly
- [ ] API calls succeed

### 10. Performance Test

**Objective**: Test page load and interaction performance

**Steps**:
1. **Measure Load Times**
   - Use browser dev tools Network tab
   - [ ] Initial page load < 2 seconds
   - [ ] API response time < 1 second

2. **Test Under Load**
   - Open multiple tabs simultaneously
   - [ ] Performance remains acceptable

## Post-Testing Verification

### Database State Checks
```bash
# Check subscription status
curl -X GET "http://localhost:8000/api/subscription-status/{email}"

# Check token usage
curl -X GET "http://localhost:8000/api/token-info/{token}"
```

### Log File Checks
```bash
# Check server logs for errors
tail -f server.log

# Check for any database errors
grep -i error data/digest_history.db.log
```

## Test Checklist Summary

**Functional Tests**:
- [ ] Happy path unsubscription works
- [ ] Invalid token handling
- [ ] Missing token handling
- [ ] Network error handling
- [ ] Already unsubscribed handling
- [ ] Token expiry handling
- [ ] Token usage limit handling

**UI/UX Tests**:
- [ ] Mobile responsiveness
- [ ] Browser compatibility
- [ ] Loading states
- [ ] Error messages
- [ ] Navigation flows

**Security Tests**:
- [ ] Token validation
- [ ] Purpose-specific tokens
- [ ] Usage tracking
- [ ] Expiry enforcement

**Performance Tests**:
- [ ] Page load times
- [ ] API response times
- [ ] Concurrent usage

## Troubleshooting Common Issues

### Frontend Not Loading
- Check if `npm start` is running
- Verify no port conflicts (3000)
- Check browser console for errors

### API Errors
- Verify backend server is running on port 8000
- Check API endpoint URLs match
- Verify database is accessible

### Token Issues
- Ensure token format is correct (JWT)
- Check token hasn't expired (72 hours)
- Verify token usage count < 3

### Browser Issues
- Clear browser cache
- Disable browser extensions
- Check console for JavaScript errors

## Test Data Cleanup

After testing, clean up test data:
```bash
# Remove test subscriptions
curl -X DELETE "http://localhost:8000/api/subscription/test@example.com"

# Clear test tokens (tokens auto-expire, but can be manually cleared if needed)
```

## Reporting Issues

When reporting issues found during testing:
1. Include browser and version
2. Provide exact steps to reproduce
3. Include error messages from console
4. Attach screenshots if relevant
5. Note any backend log errors
