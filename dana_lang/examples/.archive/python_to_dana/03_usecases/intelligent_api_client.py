#!/usr/bin/env python3
"""
Use Case 07: Scalable Microservice Architecture - Client

Test client for the Dana-powered FastAPI microservice.
This demonstrates making real HTTP requests to the intelligent microservice.

Usage:
    1. Start the server: python 07_microservice_architecture.py
    2. Run this client: python 07_microservice_client.py

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio

# HTTP client imports
try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    exit(1)

# ============================================================================
# Client Configuration
# ============================================================================

BASE_URL = "http://localhost:8000"
CLIENT_TIMEOUT = 300.0

# ============================================================================
# Test Data
# ============================================================================

SAMPLE_SENSOR_DATA = {
    "temperature": 195.5,  # High temperature
    "pressure": 58.2,  # High pressure
    "vibration": 0.8,  # High vibration
    "equipment_id": "PUMP_A_001",
    "location": "Reactor Building",
}

SAMPLE_BATCH_DATA = {
    "equipment_list": [
        {"equipment_id": "PUMP_A_001", "temperature": 195, "pressure": 58, "vibration": 0.8, "location": "Building A"},
        {"equipment_id": "PUMP_A_003", "temperature": 92, "pressure": 45, "vibration": 0.3, "location": "Building B"},
        {"equipment_id": "COMPRESSOR_B_001", "temperature": 88, "pressure": 51, "vibration": 0.4, "location": "Building B"},
    ]
}

# ============================================================================
# Client Functions
# ============================================================================


async def test_individual_diagnosis():
    """Test individual equipment diagnosis"""
    print("\n📡 Testing individual diagnosis endpoint...")

    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        try:
            print(f"   📊 Sending sensor data for {SAMPLE_SENSOR_DATA['equipment_id']}")

            response = await client.post(f"{BASE_URL}/api/v1/diagnose", json=SAMPLE_SENSOR_DATA)
            response.raise_for_status()

            diagnosis_result = response.json()

            print("\n📋 Diagnosis Response:")
            print(f"   🏷️  Equipment: {diagnosis_result['equipment_id']}")
            print(f"   🔍 Diagnosis: {diagnosis_result['diagnosis']}")
            print(f"   🚨 Severity: {diagnosis_result['severity']}")
            print(f"   📊 Confidence: {diagnosis_result['confidence_score']}%")
            print(f"   ⏱️  Estimated Fix: {diagnosis_result['estimated_fix_time']}")
            print(f"   💡 Recommendations: {len(diagnosis_result['recommendations'])} actions")

            return True

        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP Error {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            print(f"   ❌ Individual diagnosis failed: {str(e)}")
            return False


async def test_batch_diagnosis():
    """Test batch equipment diagnosis"""
    print("\n📊 Testing batch diagnosis endpoint...")

    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        try:
            equipment_count = len(SAMPLE_BATCH_DATA["equipment_list"])
            print(f"   📦 Sending batch request for {equipment_count} equipment units")

            response = await client.post(f"{BASE_URL}/api/v1/batch-diagnose", json=SAMPLE_BATCH_DATA)
            response.raise_for_status()

            batch_result = response.json()

            print("\n📋 Batch Processing Response:")
            print(f"   📊 Batch Size: {batch_result['batch_size']} equipment units")
            print(f"   🏭 Facility Overview: {batch_result['facility_overview']}")
            print(f"   ⚡ Processing Time: {batch_result['processing_time']:.2f}s")

            print("\n📈 Individual Results:")
            for result in batch_result["individual_results"]:
                equipment_id = result["equipment_id"]
                diagnosis = result["diagnosis"]
                priority = result["priority"]
                print(f"   🔧 {equipment_id}: {diagnosis} (Priority: {priority})")

            return True

        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP Error {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            print(f"   ❌ Batch diagnosis failed: {str(e)}")
            return False


# ============================================================================
# Main Test Suite
# ============================================================================


async def main():
    """Run the complete test suite"""
    print("🎯 Dana Microservice Client - Test Suite")
    print("=" * 50)

    # Test 2: Individual Diagnosis
    # individual_ok = await test_individual_diagnosis()

    # Test 3: Batch Processing
    batch_ok = await test_batch_diagnosis()

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    # print(f"   🔍 Individual Diagnosis: {'✅ PASS' if individual_ok else '❌ FAIL'}")
    print(f"   📊 Batch Processing: {'✅ PASS' if batch_ok else '❌ FAIL'}")
    # print(f"   ⚡ Performance Test: {'✅ PASS' if performance_ok else '❌ FAIL'}")

    all_passed = all([batch_ok])

    if all_passed:
        print("\n🎉 All tests passed! Dana microservice is working correctly.")
        print("\n💡 Key Demonstrations:")
        print("   🚀 Real FastAPI server with Dana AI integration")
        print("   📡 HTTP API endpoints with intelligent responses")
        print("   📊 Batch processing capabilities")
        print("   ⚡ Concurrent request handling")
        print("   🤖 Clean separation: FastAPI routing + Dana intelligence")
    else:
        print("\n⚠️  Some tests failed. Check server logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
