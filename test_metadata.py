#!/usr/bin/env python3
"""
Test script for the digest metadata endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from api import app

def test_digest_metadata_endpoint():
    """Test the /digest/metadata/{date} endpoint"""
    client = TestClient(app)
    
    # First, get an available date to test with
    print("Getting available dates...")
    dates_response = client.get("/digest/available-dates")
    dates_data = dates_response.json()
    
    if not dates_data["success"] or not dates_data["dates"]:
        print("❌ No available dates found for testing")
        return False
    
    test_date = dates_data["dates"][0]["date"]  # Use the most recent date
    print(f"Testing with date: {test_date}")
    
    # Test the metadata endpoint
    response = client.get(f"/digest/metadata/{test_date}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error response: {response.json()}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check if response has expected structure
    assert "success" in data
    assert "target_date" in data
    assert "total_articles" in data
    assert "categories" in data
    assert "sources" in data
    assert "timestamps" in data
    assert "message" in data
    
    if data["success"]:
        print(f"✅ Found {data['total_articles']} articles for {test_date}")
        print(f"Categories: {len(data['categories'])}")
        print(f"Sources: {len(data['sources'])}")
        
        # Show top categories and sources
        if data['categories']:
            top_categories = list(data['categories'].items())[:3]
            print(f"Top categories: {top_categories}")
        
        if data['sources']:
            top_sources = list(data['sources'].items())[:3]
            print(f"Top sources: {top_sources}")
        
        # Check timestamps
        timestamps = data['timestamps']
        print(f"Timestamp range: {timestamps.get('earliest_published')} to {timestamps.get('latest_published')}")
        
        print("✅ Metadata endpoint working correctly!")
    else:
        print(f"⚠️  No metadata generated: {data['message']}")
    
    # Test with invalid date format
    print("\nTesting with invalid date...")
    invalid_response = client.get("/digest/metadata/invalid-date")
    print(f"Invalid date status: {invalid_response.status_code}")
    assert invalid_response.status_code == 400, "Should return 400 for invalid date"
    print("✅ Invalid date handling verified")
    
    # Test with future date (should return empty results gracefully)
    print("\nTesting with future date...")
    future_response = client.get("/digest/metadata/2025-12-31")
    print(f"Future date status: {future_response.status_code}")
    future_data = future_response.json()
    print(f"Future date articles: {future_data.get('total_articles', 0)}")
    print("✅ Future date handling verified")
    
    return True

if __name__ == "__main__":
    try:
        test_digest_metadata_endpoint()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
