#!/usr/bin/env python3
"""
Test script to verify authentication fixes
"""
import requests
import json

def test_token_validation():
    """Test token validation endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing Authentication Fixes")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Simple token (should fail)",
            "token": "test_token",
            "expected_status": 401
        },
        {
            "name": "JWT format token (should fail but not loop)",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "expected_status": 401
        },
        {
            "name": "Empty token (should fail)",
            "token": "",
            "expected_status": 404
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['name']}")
        print(f"Token: {test_case['token'][:20]}..." if len(test_case['token']) > 20 else f"Token: {test_case['token']}")
        
        try:
            if test_case['token']:
                url = f"{base_url}/preferences/{test_case['token']}"
            else:
                url = f"{base_url}/preferences/"
                
            response = requests.get(url, timeout=5)
            
            print(f"Status Code: {response.status_code}")
            print(f"Expected: {test_case['expected_status']}")
            
            if response.status_code == test_case['expected_status']:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)
    
    print("\n✅ Authentication tests completed!")

if __name__ == "__main__":
    test_token_validation()
