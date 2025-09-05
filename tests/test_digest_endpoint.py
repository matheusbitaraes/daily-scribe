#!/usr/bin/env python3
"""
Test script for the digest simulation endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from api import app

def test_digest_simulate_endpoint():
    """Test the /digest/simulate endpoint"""
    client = TestClient(app)
    
    # Test with an existing user email  
    response = client.get("/digest/simulate", params={
        "user_email": "matheusbitaraesdenovaes@gmail.com"
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check if response has expected structure
    data = response.json()
    assert "success" in data
    assert "html_content" in data
    assert "metadata" in data
    assert "message" in data
    
    if data["success"]:
        assert data["metadata"]["email_address"] == "matheusbitaraesdenovaes@gmail.com"
        print("✅ Digest simulation endpoint working correctly!")
    else:
        print(f"⚠️  No digest generated (might be expected): {data['message']}")
    
    return True

if __name__ == "__main__":
    try:
        test_digest_simulate_endpoint()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
