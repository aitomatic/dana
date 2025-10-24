#!/usr/bin/env python3
"""Test validation of HVAC plans with meeting constraints."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "environments"))

from hvac_api import get_feedback

print("="*80)
print("TEST: Meeting Start Time Validation")
print("="*80)
print()

# Reproduce the scenario from user's output
print("Scenario: Room needs heating before meetings")
print("  Current: 61.2°F at 12:14")
print("  Outdoor: 61.8°F")
print("  Meetings:")
print("    1. 14:24 - 15:44")
print("    2. 16:50 - 18:10  ← Problem here!")
print("    3. 20:55 - 22:00")
print()

# The agent's plan (from user's output)
plan = [
    {"time_on": "12:14", "time_off": "14:24", "use_turbo": True},
    {"time_on": "14:24", "time_off": "15:44", "use_turbo": False},
    {"time_on": "16:50", "time_off": "18:10", "use_turbo": True},   # ← HVAC turns on at meeting start!
    {"time_on": "20:55", "time_off": "22:00", "use_turbo": True}
]

meeting_plan = [
    {"start_time": "14:24", "end_time": "15:44"},
    {"start_time": "16:50", "end_time": "18:10"},
    {"start_time": "20:55", "end_time": "22:00"}
]

feedback = get_feedback(
    current_indoor_temp=61.2,
    outdoor_temp=61.8,
    current_time="12:14",
    plan=plan,
    target_temps=72.0,
    mode="heat",
    meeting_plan=meeting_plan
)

print("Validation Results:")
print("="*80)
print(f"Plan Status: {feedback['plan_success']}")
print(f"Total Cost: {feedback['total_cost_kwh']:.3f} kWh")
print(f"Final Temp: {feedback['final_temp_f']:.1f}°F")
print()

if feedback['failed_actions']:
    print(f"❌ FAILED ACTIONS: {len(feedback['failed_actions'])}")
    for failed in feedback['failed_actions']:
        print(f"\n  Action {failed['action_index']}: {failed['time_on']} - {failed['time_off']}")
        print(f"  Target: {failed['target_temp_f']}°F")
        print(f"  Error: {failed['error']}")
else:
    print("✓ All actions passed")

print()
print("Action Details:")
print("="*80)
cost_sum = 0.0
for action in feedback['action_results']:
    status_icon = "✓" if action['schedule_success'] == 'success' else "❌"
    print(f"\n{status_icon} Action {action['action_index']}: {action['time_on']} → {action['time_off']}")
    print(f"  Start temp: {action['start_temp_f']:.1f}°F")
    print(f"  Target: {action['target_temp_f']}°F")
    print(f"  Status: {action['schedule_success']}")
    print(f"  Cost: {action['cost_kwh']:.3f} kWh")
    cost_sum += action['cost_kwh']
    if action['error']:
        print(f"  Error: {action['error']}")
    elif action['reached_time']:
        print(f"  Reached at: {action['reached_time']}")
        print(f"  Time needed: {action['time_needed_minutes']} min")
        print(f"  Time available: {action['time_available_minutes']} min")

print()
print(f"Cost Verification:")
print(f"  Sum of action costs: {cost_sum:.3f} kWh")
print(f"  Reported total:      {feedback['total_cost_kwh']:.3f} kWh")
if abs(cost_sum - feedback['total_cost_kwh']) < 0.001:
    print(f"  ✓ Match!")
else:
    print(f"  ❌ MISMATCH!")

print()
print("="*80)
print("EXPECTED BEHAVIOR:")
print("  - Actions 2 and 3 should FAIL because HVAC turns on at meeting start")
print("  - Room needs pre-heating BEFORE meeting starts, not during")
print("="*80)
