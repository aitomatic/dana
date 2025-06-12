#!/usr/bin/env python3
"""
Test Script for Weather-Smart Trip Planner API

This script demonstrates how to interact with the trip planner API both
programmatically and with example HTTP requests.

Usage:
    python test_trip_planner.py

Requirements:
    pip install httpx asyncio
"""

import asyncio
import json
from datetime import datetime, timedelta

import httpx


async def test_trip_planner_api():
    """Test the trip planner API with various scenarios."""
    
    # API base URL (adjust if running on different host/port)
    BASE_URL = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🌟 Testing Smart Trip Planner API powered by Dana\n")
        
        # Test 1: Root endpoint info
        print("1️⃣ Getting API information...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        api_info = response.json()
        print(f"   API: {api_info['message']}")
        print(f"   Features: {', '.join(api_info['features'])}")
        
        print("\n" + "="*60 + "\n")
        
        # Test 2: Trip planning scenarios
        test_scenarios = [
            {
                "name": "Basic Trip to San Francisco",
                "request": {
                    "destination": "San Francisco",
                    "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "duration_days": 3,
                }
            },
            # {
            #     "name": "Family Trip to Seattle",
            #     "request": {
            #         "destination": "Seattle", 
            #         "start_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            #         "duration_days": 4,
            #         "traveler_type": "family",
            #         "budget_range": "high"
            #     }
            # },
            # {
            #     "name": "Adventure Trip to Portland",
            #     "request": {
            #         "destination": "Portland",
            #         "start_date": (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
            #         "duration_days": 2,
            #         "traveler_type": "adventure", 
            #         "budget_range": "low"
            #     }
            # }
        ]
        
        for i, scenario in enumerate(test_scenarios, 2):
            print(f"{i}️⃣ Testing: {scenario['name']}")
            print("\n📤 REQUEST:")
            print(json.dumps(scenario['request'], indent=4))
            
            try:
                response = await client.post(
                    f"{BASE_URL}/trips/plan",
                    json=scenario['request'],
                    timeout=60.0  # Give Dana time to reason
                )
                
                print("\n📥 RESPONSE:")
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    trip_plan = response.json()
                    print("   ✅ Trip planned successfully!")
                    print(f"   📋 Trip plan:\n {str(trip_plan)}")
                        
                else:
                    print(f"   ❌ Request failed: {response.text}")
                    
            except httpx.TimeoutException:
                print("\n   ⏰ Request timed out (Dana reasoning may take time)")
            except Exception as e:
                print(f"\n   ❌ Error: {e}")
            
            print("\n" + "="*60 + "\n")
            
            # Small delay between requests
            await asyncio.sleep(1)


async def main():
    """Main function to run all tests."""
    
    print("🧪 Smart Trip Planner API Test Suite")
    print("=" * 50)
    print()
    
    # Check if we should run live API tests or just show examples
    try:
        # Quick connectivity check
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/", timeout=5.0)
            
        print("🚀 API is running! Executing live tests...\n")
        await test_trip_planner_api()
        
    except (httpx.ConnectError, httpx.TimeoutException):
        print("⚠️  API not running on localhost:8000")
        print("💡 To start the API, run:")
        print("   python -m uvicorn trip_planner_api:app --reload")
    
    print("\n✅ Test suite completed!")
    print("📚 For interactive API docs, visit: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main()) 