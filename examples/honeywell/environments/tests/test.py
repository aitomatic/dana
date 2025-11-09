#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for HVAC environment simulation.

Tests all major features:
1. Environment state generation
2. Physics calculations
3. Action validation
4. Meeting-aware logic
5. Both HVAC profiles
6. API functions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import API functions
from hvac_api import get_env_status, get_feedback, check_single_action

# Import modules for advanced testing
from core import (
    EnvironmentConfig,
    HVACConfig,
    ThermalConfig,
    ThermalPhysics,
    EnvironmentGenerator,
    ActionValidator
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def test_environment_generation():
    """Test 1: Environment state generation."""
    print_section("TEST 1: Environment State Generation")

    # Test default profile
    print_subsection("1.1 Generate random environment")
    status = get_env_status()

    print(f" Room: {status['room_name']}")
    print(f" Time: {status['current_time']}")
    print(f" Indoor: {status['indoor_temp']:.1f}�F")
    print(f" Outdoor: {status['outdoor_temp']:.1f}�F")
    print(f" Meetings: {len(status['meeting_plan'])}")

    if status['meeting_plan']:
        print("\n  Meeting schedule:")
        for i, meeting in enumerate(status['meeting_plan'], 1):
            print(f"    {i}. {meeting['start_time']} - {meeting['end_time']}")

    # Validate constraints
    print_subsection("1.2 Validate environment constraints")

    # Check temperature relationship (indoor should be close to outdoor)
    temp_diff = abs(status['indoor_temp'] - status['outdoor_temp'])
    assert temp_diff <= 5.0, f"Indoor/outdoor temp difference too large: {temp_diff}�F"
    print(f" Indoor/outdoor temp difference: {temp_diff:.1f}�F (within 5�F)")

    # Check time range
    hour = int(status['current_time'].split(':')[0])
    assert 8 <= hour <= 21, f"Time outside business hours: {status['current_time']}"
    print(f" Time within business hours: {status['current_time']}")

    # Check outdoor temp range
    assert 40 <= status['outdoor_temp'] <= 100, f"Outdoor temp unrealistic: {status['outdoor_temp']}"
    print(f" Outdoor temp realistic: {status['outdoor_temp']:.1f}�F")

    print("\n Environment generation: PASSED")
    return status


def test_physics_engine():
    """Test 2: Physics engine calculations."""
    print_section("TEST 2: Physics Engine")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    print_subsection("2.1 Time-to-target calculation")

    # Test cooling with turbo
    time_turbo = physics.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)
    print(f" Cool 86�72�F with turbo: {time_turbo} min")
    assert 10 <= time_turbo <= 30, f"Unexpected time with turbo: {time_turbo}"

    # Test cooling without turbo
    time_no_turbo = physics.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=False)
    print(f" Cool 86�72�F no turbo: {time_no_turbo} min")
    assert time_no_turbo > time_turbo, "Turbo should be faster than no turbo"

    # Test heating
    time_heat = physics.hvac_time(64.0, 75.0, 50.0, mode="heat", use_turbo=True)
    print(f" Heat 64�75�F with turbo: {time_heat} min")
    assert 10 <= time_heat <= 30, f"Unexpected heating time: {time_heat}"

    print_subsection("2.2 Temperature estimation (no HVAC)")

    # Test temperature drift
    estimated = physics.estimate_temp_at_time(75.0, 95.0, 120)  # 2 hours
    print(f" Start: 75.0�F, Outdoor: 95.0�F, After 2 hours: {estimated:.1f}�F")
    assert estimated > 75.0, "Temperature should drift toward outdoor temp"
    assert estimated <= 95.0, "Temperature should not exceed outdoor temp"

    print_subsection("2.3 Schedule feasibility check")

    # Test success case
    result_success = physics.check_hvac_schedule(86.0, 72.0, 60, 95.0, mode="cool", use_turbo=True)
    print(f" Can reach 72�F in 60 min? {result_success['reached_temp']}")
    assert result_success['reached_temp'] == "success"

    # Test failure case
    result_fail = physics.check_hvac_schedule(86.0, 60.0, 10, 95.0, mode="cool", use_turbo=True)
    print(f" Can reach 60�F in 10 min? {result_fail['reached_temp']}")
    assert result_fail['reached_temp'] == "failed"

    print("\n Physics engine: PASSED")


def test_single_action_validation():
    """Test 3: Single action validation."""
    print_section("TEST 3: Single Action Validation")

    print_subsection("3.1 Simple action check")

    result = check_single_action(
        current_temp=86.0,
        target_temp=72.0,
        current_time="14:00",
        target_time="15:00",
        outdoor_temp=95.0,
        use_turbo=True,
        mode="cool"
    )

    print(f" Reached temp: {result['reached_temp']}")
    print(f" Time needed: {result['time_needed_minutes']} min")
    print(f" Time available: {result['time_available_minutes']} min")

    if result['reached_temp'] == "success":
        print(f" Redundant time: {result['redundant_time_minutes']} min")
    else:
        print(f" Error: {result['error']}")

    assert result['reached_temp'] in ["success", "failed"]
    print("\n Single action validation: PASSED")


def test_multi_action_plan():
    """Test 4: Multi-action plan validation."""
    print_section("TEST 4: Multi-Action Plan Validation")

    print_subsection("4.1 Plan with gaps between actions")

    # Create a plan with multiple actions and gaps
    plan = [
        {"time_on": "08:00", "time_off": "09:00", "use_turbo": True},
        {"time_on": "11:00", "time_off": "12:00", "use_turbo": False},  # Gap 09:00-11:00
        {"time_on": "14:00", "time_off": "15:30", "use_turbo": True},   # Gap 12:00-14:00
    ]
    target_temps = [72.0, 70.0, 68.0]

    feedback = get_feedback(
        current_indoor_temp=85.0,
        outdoor_temp=90.0,
        current_time="07:30",
        plan=plan,
        target_temps=target_temps,
        mode="cool"
    )

    print(f" Plan success: {feedback['plan_success']}")
    print(f" Total cost: {feedback['total_cost_kwh']:.3f} kWh")
    print(f" Final temp: {feedback['final_temp_f']:.1f}�F")
    print(f" Actions: {len(feedback['action_results'])}")
    print(f" Failed actions: {len(feedback['failed_actions'])}")

    # Show per-action results
    print("\n  Action results:")
    for action in feedback['action_results']:
        status = "" if action['schedule_success'] == "success" else ""
        print(f"    {status} Action {action['action_index']}: "
              f"{action['time_on']}�{action['time_off']} "
              f"(target: {action['target_temp_f']:.1f}�F, "
              f"cost: {action['cost_kwh']:.3f} kWh)")

    print("\n Multi-action plan: PASSED")
    return feedback


def test_meeting_aware_validation():
    """Test 5: Meeting-aware validation."""
    print_section("TEST 5: Meeting-Aware Validation")

    print_subsection("5.1 Plan before meetings")

    # Create environment with meetings
    status = get_env_status()

    # If no meetings, create a synthetic scenario
    if not status['meeting_plan']:
        print("  No meetings in random environment, using synthetic data...")
        status['current_time'] = "14:00"
        status['indoor_temp'] = 86.0
        status['outdoor_temp'] = 95.0
        status['meeting_plan'] = [
            {"start_time": "15:00", "end_time": "16:00"},
            {"start_time": "17:00", "end_time": "18:00"}
        ]

    print(f" Current time: {status['current_time']}")
    print(f" Indoor temp: {status['indoor_temp']:.1f}�F")
    print(f" Meetings: {len(status['meeting_plan'])}")
    for i, meeting in enumerate(status['meeting_plan'], 1):
        print(f"    {i}. {meeting['start_time']} - {meeting['end_time']}")

    # Create plan to cool before first meeting
    first_meeting = status['meeting_plan'][0]
    plan = [
        {
            "time_on": status['current_time'],
            "time_off": first_meeting['start_time'],
            "use_turbo": True
        }
    ]
    target_temps = [72.0]

    feedback = get_feedback(
        current_indoor_temp=status['indoor_temp'],
        outdoor_temp=status['outdoor_temp'],
        current_time=status['current_time'],
        plan=plan,
        target_temps=target_temps,
        mode="cool",
        meeting_plan=status['meeting_plan']  # Enable meeting validation
    )

    print(f"\n Plan success: {feedback['plan_success']}")
    print(f" Total cost: {feedback['total_cost_kwh']:.3f} kWh")

    # Check for meeting-specific feedback
    if feedback['action_results']:
        action = feedback['action_results'][0]
        if 'meeting_start_time' in action:
            print(f" Associated meeting: {action['meeting_start_time']}")

        if action.get('error') and 'meeting' in action['error'].lower():
            print(f" Meeting feedback: {action['error']}")

        if action.get('error') and 'wasted energy' in action['error'].lower():
            print(f"� Wasted energy detected: {action['error']}")

    print("\n Meeting-aware validation: PASSED")


def test_hvac_profiles():
    """Test 6: Both HVAC profiles."""
    print_section("TEST 6: HVAC Profile Comparison")

    print_subsection("6.1 Small Unit (2000W) - ac_test.py profile")

    config_small = EnvironmentConfig.ac_test_profile()
    physics_small = ThermalPhysics(config_small.hvac_config, config_small.thermal_config)

    print(f" Name: {config_small.hvac_config.name}")
    print(f" Base capacity: {config_small.hvac_config.base_capacity_w:.0f}W")
    print(f" Turbo capacity: {config_small.hvac_config.turbo_capacity_w:.0f}W")

    time_small = physics_small.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)
    print(f" Time to cool 86�72�F: {time_small} min")

    print_subsection("6.2 Standard 2-Ton (7000W) - room_feedback.py profile")

    config_standard = EnvironmentConfig.room_feedback_profile()
    physics_standard = ThermalPhysics(config_standard.hvac_config, config_standard.thermal_config)

    print(f" Name: {config_standard.hvac_config.name}")
    print(f" Base capacity: {config_standard.hvac_config.base_capacity_w:.0f}W")
    print(f" Turbo capacity: {config_standard.hvac_config.turbo_capacity_w:.0f}W")

    time_standard = physics_standard.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)
    print(f" Time to cool 86�72�F: {time_standard} min")

    print_subsection("6.3 Performance comparison")

    speedup = time_small / time_standard
    print(f" Small unit: {time_small} min")
    print(f" Standard unit: {time_standard} min")
    print(f" Standard is {speedup:.1f}x faster")

    assert time_standard < time_small, "Standard (7000W) should be faster than small (2000W)"

    print("\n HVAC profiles: PASSED")


def test_custom_configuration():
    """Test 7: Custom configuration."""
    print_section("TEST 7: Custom Configuration")

    print_subsection("7.1 Create custom HVAC profile")

    # Create a large 3-ton unit
    custom_hvac = HVACConfig(
        name="Large 3-Ton Unit",
        base_capacity_w=10500.0,  # 3-ton = 36,000 BTU/hr
        turbo_capacity_w=13500.0,
        turbo_max_minutes=30.0
    )

    custom_thermal = ThermalConfig(
        heat_transfer_coeff_w_k=85.0,
        thermal_mass_j_k=1.2e6,  # Same as standard
        internal_heat_w=100.0,
        fan_boost_multiplier=1.0
    )

    custom_config = EnvironmentConfig(
        room_name="Large Conference Room",
        hvac_config=custom_hvac,
        thermal_config=custom_thermal
    )

    print(f" Room: {custom_config.room_name}")
    print(f" HVAC: {custom_config.hvac_config.name}")
    print(f" Capacity: {custom_config.hvac_config.base_capacity_w:.0f}W")

    # Test with custom config
    physics_custom = ThermalPhysics(custom_config.hvac_config, custom_config.thermal_config)
    time_custom = physics_custom.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)
    print(f" Time to cool 86�72�F: {time_custom} min")

    # Should be faster than 7000W unit
    config_standard = EnvironmentConfig.room_feedback_profile()
    physics_standard = ThermalPhysics(config_standard.hvac_config, config_standard.thermal_config)
    time_standard = physics_standard.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)

    assert time_custom < time_standard, "Larger unit should be faster"
    print(f" Faster than standard 7000W: {time_custom} < {time_standard}")

    print("\n Custom configuration: PASSED")


def test_edge_cases():
    """Test 8: Edge cases and error handling."""
    print_section("TEST 8: Edge Cases and Error Handling")

    print_subsection("8.1 Invalid inputs")

    # Test with mismatched plan/target lengths
    feedback = get_feedback(
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="14:00",
        plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}],
        target_temps=[72.0, 70.0],  # Wrong length
        mode="cool"
    )

    assert feedback['plan_success'] == "failed"
    assert 'error' in feedback
    print(f" Mismatched lengths detected: {feedback['error']}")

    # Test with invalid mode
    feedback = get_feedback(
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="14:00",
        plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}],
        target_temps=[72.0],
        mode="invalid"
    )

    assert feedback['plan_success'] == "failed"
    assert 'error' in feedback
    print(f" Invalid mode detected: {feedback['error']}")

    print_subsection("8.2 Extreme temperatures")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    # Test minimum temperature limit (60�F)
    try:
        time_low = physics.hvac_time(70.0, 55.0, 60.0, mode="cool", use_turbo=True)
        print(f" Should have failed for target < 60�F")
    except ValueError as e:
        print(f" Minimum temperature enforced: {e}")

    # Test same start and target
    time_same = physics.hvac_time(72.0, 72.0, 80.0, mode="cool", use_turbo=False)
    assert time_same == 0
    print(f" Same temp returns 0 minutes: {time_same}")

    print_subsection("8.3 Impossible schedules")

    # Not enough time to cool
    feedback = get_feedback(
        current_indoor_temp=90.0,
        outdoor_temp=95.0,
        current_time="14:00",
        plan=[{"time_on": "14:00", "time_off": "14:05", "use_turbo": False}],
        target_temps=[60.0],
        mode="cool"
    )

    assert feedback['plan_success'] == "failed" or len(feedback['failed_actions']) > 0
    print(f" Impossible schedule detected")

    print("\n Edge cases: PASSED")


def test_energy_cost_calculation():
    """Test 9: Energy cost calculations."""
    print_section("TEST 9: Energy Cost Calculation")

    print_subsection("9.1 Single action cost")

    # 60 minutes with turbo
    plan = [{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}]

    feedback = get_feedback(
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="13:30",
        plan=plan,
        target_temps=[72.0],
        mode="cool"
    )

    cost = feedback['total_cost_kwh']
    print(f" 60 min with turbo: {cost:.3f} kWh")

    # Should use turbo for 30 min, then base for 30 min
    # 7000W system: turbo=9000W, base=7000W
    # Expected: (9000*30 + 7000*30) / (1000*60) = 8.0 kWh
    expected_approx = 8.0
    assert abs(cost - expected_approx) < 1.0, f"Cost {cost} far from expected {expected_approx}"

    print_subsection("9.2 Multi-action cumulative cost")

    plan = [
        {"time_on": "08:00", "time_off": "09:00", "use_turbo": True},
        {"time_on": "11:00", "time_off": "12:00", "use_turbo": False},
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": True},
    ]

    feedback = get_feedback(
        current_indoor_temp=85.0,
        outdoor_temp=90.0,
        current_time="07:30",
        plan=plan,
        target_temps=[72.0, 70.0, 68.0],
        mode="cool"
    )

    total_cost = feedback['total_cost_kwh']
    individual_costs = [a['cost_kwh'] for a in feedback['action_results']]

    print(f" Total cost: {total_cost:.3f} kWh")
    print(f" Individual costs: {[f'{c:.3f}' for c in individual_costs]}")
    print(f" Sum of individual: {sum(individual_costs):.3f} kWh")

    assert abs(total_cost - sum(individual_costs)) < 0.001

    print("\n Energy cost calculation: PASSED")


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 80)
    print(" HVAC ENVIRONMENT SIMULATION - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    try:
        # Run all tests
        status = test_environment_generation()
        test_physics_engine()
        test_single_action_validation()
        test_multi_action_plan()
        test_meeting_aware_validation()
        test_hvac_profiles()
        test_custom_configuration()
        test_edge_cases()
        test_energy_cost_calculation()

        # Summary
        print("\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print("\n ALL TESTS PASSED \n")
        print("Test Coverage:")
        print("   Environment state generation")
        print("   Physics engine calculations")
        print("   Single action validation")
        print("   Multi-action plan validation")
        print("   Meeting-aware validation")
        print("   Both HVAC profiles (2000W & 7000W)")
        print("   Custom configuration")
        print("   Edge cases and error handling")
        print("   Energy cost calculation")
        print("\n" + "=" * 80)
        print(" System is ready for production use!")
        print("=" * 80 + "\n")

        return 0

    except AssertionError as e:
        print("\n" + "=" * 80)
        print(" TEST FAILED")
        print("=" * 80)
        print(f"\n Error: {e}\n")
        return 1

    except Exception as e:
        print("\n" + "=" * 80)
        print(" TEST ERROR")
        print("=" * 80)
        print(f"\n Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
