#!/usr/bin/env python3
"""
Test script for the available dates endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from api import app

def test_available_dates_endpoint():
    """Test the /digest/available-dates endpoint"""
    client = TestClient(app)
    
    # Test without any filters
    print("Testing /digest/available-dates without filters...")
    response = client.get("/digest/available-dates")
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check if response has expected structure
    assert "success" in data
    assert "dates" in data
    assert "total_dates" in data
    assert "message" in data
    
    if data["success"] and data["dates"]:
        print(f"✅ Found {data['total_dates']} dates with articles")
        print(f"First few dates: {data['dates'][:3]}")
        
        # Verify date format and sorting
        dates = [item["date"] for item in data["dates"]]
        assert all(len(d) == 10 for d in dates), "All dates should be in YYYY-MM-DD format"
        assert dates == sorted(dates, reverse=True), "Dates should be sorted in descending order"
        
        print("✅ Date format and sorting verified")
    else:
        print(f"⚠️  No dates found: {data['message']}")
    
    # Test with date range filters
    print("\nTesting with date filters...")
    response = client.get("/digest/available-dates", params={
        "start_date": "2025-09-01",
        "end_date": "2025-09-04"
    })
    
    print(f"Filtered Status Code: {response.status_code}")
    filtered_data = response.json()
    print(f"Filtered dates count: {filtered_data.get('total_dates', 0)}")
    
    return True

if __name__ == "__main__":
    try:
        test_available_dates_endpoint()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
