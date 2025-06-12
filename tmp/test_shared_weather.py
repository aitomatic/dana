#!/usr/bin/env python3
"""Test that both room simulators use the same outside temperature"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "demos", "smart_hvac"))

from room_simulator import RoomSimulator
from hvac_systems import HVACCommand

print("=== Testing Shared Weather Service ===")

# Create two room simulators (like in the demo)
room1 = RoomSimulator(initial_temp=72.0)
room2 = RoomSimulator(initial_temp=72.0)

# Create a simple HVAC command
test_command = HVACCommand(heating_output=0, cooling_output=0, fan_speed=20, mode="idle")

print("Initial outside temperatures:")
print(f"Room 1: {room1.state.outside_temp}°F")
print(f"Room 2: {room2.state.outside_temp}°F")
print(f"Same initial temp: {room1.state.outside_temp == room2.state.outside_temp}")

print("\nRunning 10 simulation steps...")
for i in range(10):
    result1 = room1.step(test_command)
    result2 = room2.step(test_command)

    outside_temp1 = result1["outside_temp"]
    outside_temp2 = result2["outside_temp"]

    print(f"Step {i+1}: Room1={outside_temp1}°F, Room2={outside_temp2}°F, Same={outside_temp1 == outside_temp2}")

print("\n✅ Test completed! Both rooms should show identical outside temperatures.")
