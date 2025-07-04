#!/usr/bin/env python3
"""
Use Case 01: Gradual Migration Path

Python developers can **incrementally adopt Dana** without rewriting entire applications.

This example demonstrates how to use Dana only for AI workflows
while keeping their Python infrastructure intact.

Business Value: Start small, minimize risk
- Incremental Dana adoption without system rewrites
- Keep existing Python infrastructure intact
- Add AI capabilities to specific workflows

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pandas as pd

from dana.dana import dana


def main():
    print("🎯 Use Case 01: Gradual Migration Path")
    print("=" * 40)

    # Step 1: Create sample sensor data
    print("📊 Python: Create sample data")
    data = pd.DataFrame(
        {
            "sensor_id": [1, 1, 2, 2, 3, 3],
            "temperature": [25.5, 26.1, 24.8, 25.2, 25.7, 26.3],
            "pressure": [101.3, 101.4, 101.2, 101.3, 101.5, 101.6],
            "vibration": [0.15, 0.16, 0.14, 0.15, 0.16, 0.17],
        }
    )
    processed = data.groupby("sensor_id")[["temperature", "pressure", "vibration"]].mean()
    print(f"Processed {len(processed)} sensors")

    # Step 2: Use Dana for AI reasoning
    print("\n🤖 Dana: Add AI insights")
    dana.enable_module_imports()

    try:
        import sensor_insights  # Dana module

        # Pick one sensor for demo
        sensor_data = processed.iloc[0].to_dict()

        # Dana handles the AI reasoning
        insights = sensor_insights.intelligent_analysis(sensor_data)

        print(f"AI Analysis: {insights}")

    finally:
        dana.disable_module_imports()

    print("\n✅ Migration Success: Started small, added AI incrementally!")
    print("💡 Next: Scale AI adoption based on success")


if __name__ == "__main__":
    main()
