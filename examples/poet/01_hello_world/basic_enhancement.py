#!/usr/bin/env python3
"""
POET Hello World - Basic Function Enhancement

This example demonstrates the simplest POET usage:
1. Decorate a function with @poet()
2. See automatic P→O→E enhancement
3. Get POETResult with execution context
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from opendxa.dana.poet import poet
from opendxa.common.utils.logging import DXA_LOGGER


@poet()
def calculate_sum(a: int, b: int) -> int:
    """Simple addition function that will be enhanced by POET"""
    return a + b


@poet(domain="ml_monitoring")
def detect_anomaly(value: float, threshold: float = 2.0) -> dict:
    """Anomaly detection with ML monitoring domain expertise"""
    is_anomaly = abs(value) > threshold
    return {"is_anomaly": is_anomaly, "value": value, "threshold": threshold, "confidence": 0.8 if is_anomaly else 0.9}


def main():
    """Demonstrate basic POET functionality"""
    print("🚀 POET Hello World - Basic Enhancement")
    print("=" * 50)

    print("\n1. Simple function enhancement:")
    print("   @poet() adds P→O→E phases automatically")

    try:
        # Call enhanced function
        result1 = calculate_sum(5, 3)
        print(f"   calculate_sum(5, 3) = {result1}")
        print(f"   Result type: {type(result1)}")
        print(f"   Execution ID: {result1._poet['execution_id']}")
        print(f"   Enhanced: {result1._poet['enhanced']}")

        # Access the actual result
        actual_sum = result1.unwrap()
        print(f"   Actual sum: {actual_sum}")

    except Exception as e:
        DXA_LOGGER.error(f"Error in basic enhancement: {e}")
        print(f"   ❌ Error: {e}")

    print("\n2. Domain-specific enhancement:")
    print("   @poet(domain='ml_monitoring') adds ML expertise")

    try:
        # Call ML monitoring enhanced function
        result2 = detect_anomaly(5.0, threshold=2.0)
        print(f"   detect_anomaly(5.0) = {result2}")
        print(f"   Function: {result2._poet['function_name']}")
        print(f"   Version: {result2._poet['version']}")

        # Check the enhanced result
        anomaly_data = result2.unwrap()
        print(f"   Anomaly detected: {anomaly_data['is_anomaly']}")
        print(f"   Confidence: {anomaly_data['confidence']}")

    except Exception as e:
        DXA_LOGGER.error(f"Error in domain enhancement: {e}")
        print(f"   ❌ Error: {e}")

    print("\n3. Enhanced function features:")
    print("   - Input validation (Perceive phase)")
    print("   - Error handling and reliability (Operate phase)")
    print("   - Output validation (Enforce phase)")
    print("   - Execution context tracking")
    print("   - Domain-specific intelligence")

    print("\n✅ Basic enhancement complete!")
    print("   Next: Try with_feedback.py to see learning capabilities")


if __name__ == "__main__":
    main()
