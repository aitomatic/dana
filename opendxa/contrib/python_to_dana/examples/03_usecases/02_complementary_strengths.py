#!/usr/bin/env python3
"""
Use Case 02: Complementary Strengths

Demonstrates how Python excels at certain tasks (data manipulation, APIs, databases)
while Dana excels at others (AI reasoning, risk assessment, agent workflows).

This shows the complementary strengths of both languages working together.

Business Value: Use the best tool for each job
- Python for data processing, APIs, numerical analysis
- Dana for AI reasoning, risk assessment, planning
- Clear separation of concerns

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time

import numpy as np

from opendxa.dana import dana


def simulate_sensor_api():
    """
    Python Excellence: API simulation with realistic sensor data
    (In real world, this would be: requests.get("/api/sensors").json())
    """
    # Simulate API response with realistic industrial sensor data
    return {
        "sensors": [
            {"id": "TEMP_001", "temperature": 85.2, "pressure": 42.5, "vibration": 0.28, "location": "Reactor Zone A"},
            {"id": "TEMP_002", "temperature": 92.1, "pressure": 38.9, "vibration": 0.15, "location": "Cooling System"},
            {
                "id": "TEMP_003",
                "temperature": 105.7,  # High temperature
                "pressure": 55.2,  # High pressure
                "vibration": 0.45,  # High vibration
                "location": "Primary Heat Exchanger",
            },
        ],
        "timestamp": time.time(),
        "facility": "Manufacturing Plant A",
    }


def process_sensor_data(api_response):
    """
    Python Excellence: Data manipulation and numerical processing
    """
    sensors = api_response["sensors"]

    # Use numpy for numerical processing (Python's strength)
    temperatures = np.array([s["temperature"] for s in sensors])
    pressures = np.array([s["pressure"] for s in sensors])
    vibrations = np.array([s["vibration"] for s in sensors])

    # Statistical analysis
    stats = {
        "avg_temp": float(np.mean(temperatures)),
        "max_temp": float(np.max(temperatures)),
        "temp_std": float(np.std(temperatures)),
        "pressure_range": float(np.max(pressures) - np.min(pressures)),
        "vibration_anomalies": int(np.sum(vibrations > 0.3)),
        "sensor_count": len(sensors),
    }

    return sensors, stats


def main():
    print("🎯 Use Case 02: Complementary Strengths")
    print("=" * 45)

    # PYTHON EXCELS: API calls and data manipulation
    print("🐍 Python: Fetching sensor data from API...")
    api_response = simulate_sensor_api()

    print("🐍 Python: Processing numerical data...")
    sensors, stats = process_sensor_data(api_response)

    print(f"   📊 Processed {stats['sensor_count']} sensors")
    print(f"   📈 Avg temperature: {stats['avg_temp']:.1f}°C")
    print(f"   ⚠️  High vibration sensors: {stats['vibration_anomalies']}")

    # DANA EXCELS: AI reasoning and risk assessment
    print("\n🤖 Dana: AI risk assessment and planning...")
    dana.enable_module_imports()

    try:
        import agent_logic  # Dana module for AI reasoning

        # Dana handles complex AI reasoning for each sensor
        for sensor in sensors:
            print(f"\n🔍 Analyzing {sensor['id']} ({sensor['location']}):")

            # Dana's AI reasoning capability
            risk_level = agent_logic.assess_risk(sensor)
            print(f"   Risk Level: {risk_level}")

            # Dana's AI planning capability
            if "high" in risk_level.lower() or "critical" in risk_level.lower():
                response_plan = agent_logic.plan_response(risk_level, sensor)
                print(f"   Response Plan: {response_plan}")

        # Overall facility assessment using aggregate stats
        print("\n🏭 Facility-wide assessment:")
        facility_risk = agent_logic.assess_facility_risk(stats)
        print(f"   Overall Risk: {facility_risk}")

    finally:
        dana.disable_module_imports()

    print("\n✅ Complete! Python handled data/APIs, Dana handled AI reasoning.")
    print("\n💡 Key Takeaway:")
    print("   🐍 Python: Great for data manipulation, APIs, numerical processing")
    print("   🤖 Dana: Great for AI reasoning, risk assessment, intelligent planning")


if __name__ == "__main__":
    main()
