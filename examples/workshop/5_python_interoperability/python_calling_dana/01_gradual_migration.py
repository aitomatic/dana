#!/usr/bin/env python3
"""
Example 1: Gradual Migration - Start Small, Scale Smart

Demonstrates how to incrementally add Dana AI to existing Python systems
without changing any existing code.

Key Insight: You don't need to rebuild - just enhance!
"""

import logging

import pandas as pd

from opendxa.dana import dana

# Hide all INFO logs system-wide
logging.getLogger().setLevel(logging.WARNING)


def main():
    print("\n" + "="*80)
    print("🎯  \033[1;36mExample 1: Gradual Migration - Enhance Existing Systems\033[0m")
    print("="*80 + "\n")
    
    # EXISTING PYTHON SYSTEM (Don't touch this!)
    print("\033[1;33m📊 EXISTING: Your working Python data processing\033[0m")
    sensor_data = pd.DataFrame({
        "equipment_id": ["PUMP_001", "PUMP_002", "MOTOR_003"],
        "temperature": [85.2, 87.1, 89.3],
        "pressure": [42.1, 43.8, 44.2],
        "vibration": [0.25, 0.28, 0.30]
    })
    
    # Your existing business logic (unchanged)
    processed_data = sensor_data.groupby('equipment_id').mean()
    print(f"\033[32m✅ Processed {len(processed_data)} equipment readings\033[0m\n")
    
    # NEW: Add AI intelligence in 2 lines (zero risk!)
    print("\033[1;34m🤖 NEW: Add AI insights without changing existing code\033[0m")
    print("-"*80)
    
    for equipment_id, readings in processed_data.iterrows():
        # THIS IS THE ONLY LINE YOU NEED TO ADD!
        ai_insights = dana.reason(f"""
            Analyze equipment health:
            Equipment: {equipment_id}
            Temperature: {readings['temperature']:.1f}°C
            Pressure: {readings['pressure']:.1f} PSI  
            Vibration: {readings['vibration']:.2f}
            
            Provide: health_status, maintenance_prediction, priority_level
        """)
        
        print(f"\033[36m  🔧 {equipment_id}:\033[0m")
        print(f"     \033[37m{ai_insights}\033[0m")
        print("-"*80)
    
    print("\n\033[1;32m✅ RESULT: Your system now has AI superpowers!\033[0m")
    print("\033[1;33m💡 Next step: Add more AI modules as you see value\033[0m\n")


if __name__ == "__main__":
    main() 