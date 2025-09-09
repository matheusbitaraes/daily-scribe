#!/usr/bin/env python3
"""
Test script for subscription API endpoints.
"""

import sys
import json
import time
import requests
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "api.test@example.com"

def test_api_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> Dict[str, Any]:
    """Test an API endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else {},
            "success": response.status_code < 400
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "response": {"error": str(e)},
            "success": False
        }

def main():
    """Run API endpoint tests."""
    print("Testing Daily Scribe Subscription API Endpoints")
    print("=" * 50)
    
    # Test 1: Valid subscription request
    print("\\n1. Testing valid subscription request...")
    result = test_api_endpoint("POST", "/subscribe", {"email": TEST_EMAIL})
    print(f"Status: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    if result['success']:
        print("✅ Valid subscription request works")
    else:
        print("❌ Valid subscription request failed")
        return False
    
    # Test 2: Duplicate subscription request
    print("\\n2. Testing duplicate subscription request...")
    result = test_api_endpoint("POST", "/subscribe", {"email": TEST_EMAIL})
    print(f"Status: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    if result['status_code'] == 409:
        print("✅ Duplicate subscription properly rejected")
    else:
        print("❌ Duplicate subscription not properly handled")
    
    # Test 3: Invalid email format
    print("\\n3. Testing invalid email format...")
    result = test_api_endpoint("POST", "/subscribe", {"email": "invalid-email"})
    print(f"Status: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    if result['status_code'] == 422:  # Pydantic validation error
        print("✅ Invalid email format properly rejected")
    else:
        print("❌ Invalid email format not properly handled")
    
    # Test 4: Get verification token and test verification
    print("\\n4. Testing email verification...")
    
    # Get token from database (simulating email link click)
    sys.path.insert(0, 'src')
    import sqlite3
    
    try:
        conn = sqlite3.connect('data/digest_history.db')
        cursor = conn.cursor()
        cursor.execute('SELECT verification_token FROM pending_subscriptions WHERE email = ?', (TEST_EMAIL,))
        token_row = cursor.fetchone()
        conn.close()
        
        if token_row:
            token = token_row[0]
            print(f"Found verification token: {token[:10]}...")
            
            # Test verification
            result = test_api_endpoint("GET", "/verify-email", params={"token": token})
            print(f"Status: {result['status_code']}")
            print(f"Response: {json.dumps(result['response'], indent=2)}")
            
            if result['success']:
                print("✅ Email verification works")
            else:
                print("❌ Email verification failed")
        else:
            print("❌ No verification token found in database")
            
    except Exception as e:
        print(f"❌ Error testing verification: {e}")
    
    # Test 5: Invalid verification token
    print("\\n5. Testing invalid verification token...")
    result = test_api_endpoint("GET", "/verify-email", params={"token": "invalid-token-123"})
    print(f"Status: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    if result['status_code'] == 400:
        print("✅ Invalid token properly rejected")
    else:
        print("❌ Invalid token not properly handled")
    
    # Test 6: Generate unsubscribe token (requires real user)
    print("\\n6. Testing unsubscribe token generation...")
    try:
        # First create a subscription and verify it to have a real user
        print("  - Creating test subscription for unsubscribe testing...")
        test_unsubscribe_email = "unsubscribe.test@example.com"
        
        # Subscribe
        sub_result = test_api_endpoint("POST", "/subscribe", {"email": test_unsubscribe_email})
        if sub_result['success']:
            print(f"  ✅ Test subscription created for {test_unsubscribe_email}")
            
            # Try to generate an unsubscribe token using the email service
            # Note: This would normally be done through email generation, but we'll test the endpoint directly
            print("  - Testing unsubscribe with invalid token...")
            unsubscribe_result = test_api_endpoint("POST", "/unsubscribe", {"token": "invalid-unsubscribe-token"})
            print(f"  Status: {unsubscribe_result['status_code']}")
            print(f"  Response: {json.dumps(unsubscribe_result['response'], indent=2)}")
            
            if unsubscribe_result['status_code'] == 400:
                print("  ✅ Invalid unsubscribe token properly rejected")
            else:
                print("  ❌ Invalid unsubscribe token not properly handled")
        else:
            print(f"  ❌ Failed to create test subscription: {sub_result['response']}")
            
    except Exception as e:
        print(f"❌ Error testing unsubscribe: {e}")
    
    # Test 7: Test unsubscribe with malformed request
    print("\\n7. Testing unsubscribe with malformed request...")
    result = test_api_endpoint("POST", "/unsubscribe", {"invalid_field": "test"})
    print(f"Status: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    if result['status_code'] == 422:  # FastAPI validation error
        print("✅ Malformed request properly rejected")
    else:
        print("❌ Malformed request not properly handled")
    
    # Test 8: Test unsubscribe endpoint response structure
    print("\\n8. Testing unsubscribe endpoint response structure...")
    result = test_api_endpoint("POST", "/unsubscribe", {"token": "structure-test-token"})
    print(f"Status: {result['status_code']}")
    
    # Check if response has expected error structure
    response = result['response']
    if 'detail' in response and isinstance(response['detail'], dict):
        detail = response['detail']
        if 'error' in detail and 'code' in detail and 'details' in detail:
            print("✅ Unsubscribe error response has correct structure")
        else:
            print("❌ Unsubscribe error response missing required fields")
    else:
        print("❌ Unsubscribe response doesn't have expected structure")
    
    print("\\n" + "=" * 50)
    print("API endpoint testing complete!")
    print("\\nNote: For complete end-to-end testing, you would need to:")
    print("1. Generate a real unsubscribe token from the email service")
    print("2. Test the frontend UnsubscribePage component")
    print("3. Verify database state changes")
    print("4. Test email digest exclusion after unsubscription")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            main()
        else:
            print("❌ Server health check failed")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the server first:")
        print("cd /path/to/daily-scribe && python -m uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000")
