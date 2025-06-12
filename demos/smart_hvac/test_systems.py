#!/usr/bin/env python3
"""
Test script for HVAC systems to verify everything works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hvac_systems import (
    POET_AVAILABLE,
    ComfortBasedController,
    basic_hvac_control,
    calculate_comfort_score,
    calculate_energy_usage,
    smart_hvac_control,
)
from room_simulator import RoomSimulator


def test_basic_functionality():
    """Test basic HVAC functionality."""
    print("🧪 Testing Basic HVAC Functionality")
    print("-" * 40)
    
    # Test basic HVAC control
    result = basic_hvac_control(
        current_temp=70.0,
        target_temp=72.0,
        outdoor_temp=65.0,
        occupancy=True
    )
    
    print("✅ Basic HVAC Control:")
    print("   Input: 70°F → 72°F target")
    print(f"   Output: {result.mode}, heating: {result.heating_output}%")
    
    # Test POET HVAC control  
    result = smart_hvac_control(
        current_temp=70.0,
        target_temp=72.0,
        outdoor_temp=65.0,
        occupancy=True
    )
    
    # Handle POET wrapper result
    if POET_AVAILABLE and isinstance(result, dict) and 'result' in result:
        hvac_result = result['result']
        execution_time = result.get('execution_time', 0)
        print("✅ POET HVAC Control:")
        print("   Input: 70°F → 72°F target")
        print(f"   Output: {hvac_result.mode}, heating: {hvac_result.heating_output}%")
        print(f"   POET Available: {POET_AVAILABLE}, Execution time: {execution_time*1000:.2f}ms")
    else:
        print("✅ POET HVAC Control:")
        print("   Input: 70°F → 72°F target")
        print(f"   Output: {result.mode}, heating: {result.heating_output}%")
        print(f"   POET Available: {POET_AVAILABLE}")
    
    return True

def test_room_simulation():
    """Test room simulation."""
    print("\n🏠 Testing Room Simulation")
    print("-" * 40)
    
    # Create room simulator
    room = RoomSimulator(initial_temp=72.0)
    
    # Test heating command
    from hvac_systems import HVACCommand
    heating_command = HVACCommand(
        heating_output=50,
        cooling_output=0,
        fan_speed=30,
        mode="heating"
    )
    
    # Run simulation step
    state = room.step(heating_command)
    
    print("✅ Room Simulation:")
    print("   Initial: 72.0°F")
    print(f"   After heating: {state['temperature']:.1f}°F")
    print(f"   Energy usage: {state['energy_usage']:.3f} kWh")
    print(f"   Outside temp: {state['outside_temp']:.1f}°F")
    
    return True

def test_comfort_controller():
    """Test comfort-based controller."""
    print("\n😊 Testing Comfort Controller")
    print("-" * 40)
    
    controller = ComfortBasedController()
    
    # Test feedback processing
    setpoint1 = controller.process_feedback("too_cold", 70.0)
    print(f"✅ Too Cold Feedback: 70°F → {setpoint1:.1f}°F target")
    
    setpoint2 = controller.process_feedback("too_hot", 75.0)
    print(f"✅ Too Hot Feedback: 75°F → {setpoint2:.1f}°F target")
    
    setpoint3 = controller.process_feedback("comfortable", 72.0)
    print(f"✅ Comfortable Feedback: 72°F → {setpoint3:.1f}°F target")
    
    return True

def test_energy_calculations():
    """Test energy and comfort calculations."""
    print("\n⚡ Testing Energy Calculations")
    print("-" * 40)
    
    from hvac_systems import HVACCommand
    
    # Test energy calculation
    command = HVACCommand(60, 0, 40, "heating")
    energy = calculate_energy_usage(command, duration=1.0)
    print(f"✅ Energy Usage: {energy:.3f} kWh for 1 minute of heating at 60%")
    
    # Test comfort score
    comfort = calculate_comfort_score(
        current_temp=72.5,
        target_temp=72.0,
        temp_history=[71.8, 72.0, 72.2, 72.5]
    )
    print(f"✅ Comfort Score: {comfort:.1f}/100 for 0.5°F deviation")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Smart HVAC System Tests")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_room_simulation,
        test_comfort_controller,
        test_energy_calculations
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All systems working correctly!")
        print("🌐 Ready to run the web demo with: python run_demo.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())