#!/usr/bin/env python3
"""Test case to verify plan failure detection works correctly."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "environments"))

from hvac_api import get_feedback

# Test Case 1: Insufficient time (should FAIL)
print("="*80)
print("TEST CASE 1: Insufficient Time")
print("="*80)
print("Scenario: Need to cool from 95°F to 65°F in only 5 minutes")
print()

feedback1 = get_feedback(
    current_indoor_temp=95.0,
    outdoor_temp=100.0,
    current_time="14:00",
    plan=[{"time_on": "14:00", "time_off": "14:05", "use_turbo": True}],
    target_temps=65.0,
    mode="cool"
)

print(f"Result: {feedback1['plan_success']}")
print(f"Total cost: {feedback1['total_cost_kwh']:.3f} kWh")
print(f"Final temp: {feedback1['final_temp_f']:.1f}°F")
if feedback1['action_results']:
    action = feedback1['action_results'][0]
    print(f"Time needed: {action['time_needed_minutes']} min")
    print(f"Time available: {action['time_available_minutes']} min")
    if action['error']:
        print(f"Error: {action['error']}")
print()

# Test Case 2: Moderate difficulty (might succeed or fail)
print("="*80)
print("TEST CASE 2: Moderate Difficulty")
print("="*80)
print("Scenario: Need to cool from 90°F to 70°F in 15 minutes")
print()

feedback2 = get_feedback(
    current_indoor_temp=90.0,
    outdoor_temp=95.0,
    current_time="14:00",
    plan=[{"time_on": "14:00", "time_off": "14:15", "use_turbo": True}],
    target_temps=70.0,
    mode="cool"
)

print(f"Result: {feedback2['plan_success']}")
print(f"Total cost: {feedback2['total_cost_kwh']:.3f} kWh")
print(f"Final temp: {feedback2['final_temp_f']:.1f}°F")
if feedback2['action_results']:
    action = feedback2['action_results'][0]
    print(f"Time needed: {action['time_needed_minutes']} min")
    print(f"Time available: {action['time_available_minutes']} min")
    if action['error']:
        print(f"Error: {action['error']}")
print()

# Test Case 3: No turbo with short time (should FAIL)
print("="*80)
print("TEST CASE 3: No Turbo, Short Time")
print("="*80)
print("Scenario: Need to cool from 85°F to 72°F in 10 minutes without turbo")
print()

feedback3 = get_feedback(
    current_indoor_temp=85.0,
    outdoor_temp=92.0,
    current_time="14:00",
    plan=[{"time_on": "14:00", "time_off": "14:10", "use_turbo": False}],
    target_temps=72.0,
    mode="cool"
)

print(f"Result: {feedback3['plan_success']}")
print(f"Total cost: {feedback3['total_cost_kwh']:.3f} kWh")
print(f"Final temp: {feedback3['final_temp_f']:.1f}°F")
if feedback3['action_results']:
    action = feedback3['action_results'][0]
    print(f"Time needed: {action['time_needed_minutes']} min")
    print(f"Time available: {action['time_available_minutes']} min")
    if action['error']:
        print(f"Error: {action['error']}")
print()

# Test Case 4: Multiple actions, one fails
print("="*80)
print("TEST CASE 4: Multiple Actions (one should fail)")
print("="*80)
print("Scenario: Two actions, second one has insufficient time")
print()

feedback4 = get_feedback(
    current_indoor_temp=88.0,
    outdoor_temp=95.0,
    current_time="14:00",
    plan=[
        {"time_on": "14:00", "time_off": "14:30", "use_turbo": True},
        {"time_on": "15:00", "time_off": "15:05", "use_turbo": False}
    ],
    target_temps=[75.0, 65.0],  # Second target is very aggressive
    mode="cool"
)

print(f"Result: {feedback4['plan_success']}")
print(f"Total cost: {feedback4['total_cost_kwh']:.3f} kWh")
print(f"Final temp: {feedback4['final_temp_f']:.1f}°F")
print(f"Failed actions: {len(feedback4['failed_actions'])}")
for i, action in enumerate(feedback4['action_results']):
    print(f"\nAction {i}:")
    print(f"  Target: {action['target_temp_f']}°F")
    print(f"  Result: {action['schedule_success']}")
    print(f"  Time needed: {action['time_needed_minutes']} min")
    print(f"  Time available: {action['time_available_minutes']} min")
    if action['error']:
        print(f"  Error: {action['error']}")
print()

print("="*80)
print("SUMMARY")
print("="*80)
results = [
    ("Test 1 (Extreme)", feedback1['plan_success']),
    ("Test 2 (Moderate)", feedback2['plan_success']),
    ("Test 3 (No turbo)", feedback3['plan_success']),
    ("Test 4 (Multiple)", feedback4['plan_success'])
]
for name, result in results:
    status = "✓" if result == "success" else "✗"
    print(f"{status} {name}: {result}")
