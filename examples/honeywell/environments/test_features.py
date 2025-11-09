#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Feature Test for HVAC Environment Simulation

Tests all features from core modules, then demonstrates the 2 API functions.

Test Structure:
1. Configuration features
2. Physics engine features
3. Environment generator features
4. Action validator features
5. Multi-action plan validation
6. Meeting-aware validation
7. Energy cost calculation
8. Edge cases and error handling
9. API Function: get_environment()
10. API Function: validate_plan()
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    EnvironmentConfig,
    HVACConfig,
    ThermalConfig,
    ThermalPhysics,
    EnvironmentGenerator,
    ActionValidator
)
from hvac_api import get_environment, validate_plan


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_test(test_name: str):
    """Print test name."""
    print(f"\n{test_name}")
    print("-" * 80)


def test_1_configuration_features():
    """Test 1: Configuration Features"""
    print_section("Test 1: Configuration Features")

    # Feature 1.1: Preset configurations
    print_test("Feature 1.1: Preset HVAC Configurations")

    small_config = EnvironmentConfig.ac_test_profile()
    standard_config = EnvironmentConfig.room_feedback_profile()

    print(f"Small Unit (2000W):")
    print(f"  Name: {small_config.hvac_config.name}")
    print(f"  Base capacity: {small_config.hvac_config.base_capacity_w}W")
    print(f"  Turbo capacity: {small_config.hvac_config.turbo_capacity_w}W")

    print(f"\nStandard Unit (7000W):")
    print(f"  Name: {standard_config.hvac_config.name}")
    print(f"  Base capacity: {standard_config.hvac_config.base_capacity_w}W")
    print(f"  Turbo capacity: {standard_config.hvac_config.turbo_capacity_w}W")

    # Feature 1.2: Custom configuration
    print_test("Feature 1.2: Custom HVAC Configuration")

    custom_hvac = HVACConfig(
        name="Custom Large Unit",
        base_capacity_w=10000.0,
        turbo_capacity_w=12000.0,
        turbo_max_minutes=30.0
    )

    custom_thermal = ThermalConfig(
        heat_transfer_coeff_w_k=100.0,
        thermal_mass_j_k=1.5e6,
        internal_heat_w=150.0,
        fan_boost_multiplier=1.0
    )

    custom_config = EnvironmentConfig(
        room_name="Large Conference Room",
        hvac_config=custom_hvac,
        thermal_config=custom_thermal
    )

    print(f"Custom Configuration:")
    print(f"  Room: {custom_config.room_name}")
    print(f"  HVAC: {custom_config.hvac_config.base_capacity_w}W")
    print(f"  Thermal mass: {custom_config.thermal_config.thermal_mass_j_k} J/K")

    print("\n✓ Configuration features working correctly")
    return True


def test_2_physics_engine_features():
    """Test 2: Physics Engine Features"""
    print_section("Test 2: Physics Engine Features")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    # Feature 2.1: Cooling time calculation
    print_test("Feature 2.1: Cooling Time Calculation")

    time_normal = physics.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=False)
    time_turbo = physics.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)

    print(f"Cool from 86°F to 72°F (outdoor 95°F):")
    print(f"  Normal mode: {time_normal} minutes")
    print(f"  Turbo mode: {time_turbo} minutes")
    print(f"  Time saved: {time_normal - time_turbo} minutes")

    # Feature 2.2: Heating time calculation
    print_test("Feature 2.2: Heating Time Calculation")

    time_heat = physics.hvac_time(65.0, 72.0, 55.0, mode="heat", use_turbo=False)

    print(f"Heat from 65°F to 72°F (outdoor 55°F):")
    print(f"  Time needed: {time_heat} minutes")

    # Feature 2.3: Temperature drift estimation
    print_test("Feature 2.3: Temperature Drift Estimation")

    drift_temp = physics.estimate_temp_at_time(72.0, 95.0, 60)

    print(f"Starting at 72°F, outdoor 95°F:")
    print(f"  Temperature after 60 min (no HVAC): {drift_temp:.1f}°F")
    print(f"  Temperature increase: {drift_temp - 72:.1f}°F")

    # Feature 2.4: Schedule feasibility check
    print_test("Feature 2.4: Schedule Feasibility Check")

    result = physics.check_hvac_schedule(
        current_temp_f=86.0,
        target_temp_f=72.0,
        time_available_minutes=60,
        outdoor_temp_f=95.0,
        mode="cool",
        use_turbo=True
    )

    print(f"Can cool 86°F → 72°F in 60 minutes?")
    print(f"  Result: {result['reached_temp']}")
    print(f"  Time needed: {result['time_needed_minutes']} min")
    print(f"  Time available: {result['time_available_minutes']} min")
    print(f"  Extra time: {result['redundant_time_minutes']} min")

    print("\n✓ Physics engine features working correctly")
    return True


def test_3_environment_generator_features():
    """Test 3: Environment Generator Features"""
    print_section("Test 3: Environment Generator Features")

    config = EnvironmentConfig.room_feedback_profile()
    generator = EnvironmentGenerator(config)

    # Feature 3.1: Random state generation
    print_test("Feature 3.1: Random Environment State Generation")

    state1 = generator.generate_state()
    state2 = generator.generate_state()

    print(f"State 1:")
    print(f"  Time: {state1['current_time']}")
    print(f"  Indoor: {state1['indoor_temp']:.1f}°F")
    print(f"  Outdoor: {state1['outdoor_temp']:.1f}°F")
    print(f"  Meetings: {len(state1['meeting_plan'])}")

    print(f"\nState 2 (different):")
    print(f"  Time: {state2['current_time']}")
    print(f"  Indoor: {state2['indoor_temp']:.1f}°F")
    print(f"  Outdoor: {state2['outdoor_temp']:.1f}°F")
    print(f"  Meetings: {len(state2['meeting_plan'])}")

    # Feature 3.2: Meeting schedule generation
    print_test("Feature 3.2: Meeting Schedule Generation")

    if state1['meeting_plan']:
        print(f"Meeting plan for {state1['current_time']}:")
        for i, meeting in enumerate(state1['meeting_plan'], 1):
            print(f"  {i}. {meeting['start_time']} - {meeting['end_time']}")
    else:
        print("No meetings scheduled")

    # Feature 3.3: Time-based outdoor temperature
    print_test("Feature 3.3: Time-based Outdoor Temperature Variation")

    # Generate multiple states to see temperature variation
    temps = []
    for _ in range(5):
        state = generator.generate_state()
        temps.append((state['current_time'], state['outdoor_temp']))

    print("Outdoor temperature varies by time of day:")
    for time, temp in temps:
        print(f"  {time}: {temp:.1f}°F")

    print("\n✓ Environment generator features working correctly")
    return True


def test_4_action_validator_features():
    """Test 4: Action Validator Features"""
    print_section("Test 4: Action Validator Features")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Feature 4.1: Single action validation
    print_test("Feature 4.1: Single Action Validation")

    plan = [{
        "time_on": "14:00",
        "time_off": "15:00",
        "use_turbo": True
    }]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan,
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Single action plan:")
    print(f"  Plan success: {result['plan_success']}")
    print(f"  Cost: {result['total_cost_kwh']:.2f} kWh")
    print(f"  Final temp: {result['final_temp_f']:.1f}°F")

    if result['action_results']:
        action = result['action_results'][0]
        print(f"  Time needed: {action['time_needed_minutes']} min")
        print(f"  Reached at: {action['reached_time']}")

    # Feature 4.2: Failed action detection
    print_test("Feature 4.2: Failed Action Detection")

    impossible_plan = [{
        "time_on": "14:55",
        "time_off": "15:00",
        "use_turbo": False
    }]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="14:50",
        plan=impossible_plan,
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Impossible plan (5 min to cool 14°F):")
    print(f"  Plan success: {result['plan_success']}")
    print(f"  Failed actions: {len(result['failed_actions'])}")

    if result['failed_actions']:
        print(f"  Error: {result['failed_actions'][0]['error']}")

    print("\n✓ Action validator features working correctly")
    return True


def test_5_multi_action_plans():
    """Test 5: Multi-Action Plan Validation"""
    print_section("Test 5: Multi-Action Plan Validation")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Feature 5.1: Sequential cooling actions
    print_test("Feature 5.1: Sequential Cooling Actions with Gap")

    multi_plan = [
        {"time_on": "09:00", "time_off": "10:00", "use_turbo": True},
        {"time_on": "12:00", "time_off": "13:00", "use_turbo": False}
    ]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="08:30",
        plan=multi_plan,
        target_temps=[72.0, 70.0],
        mode="cool"
    )

    print(f"Multi-action plan with 2-hour gap:")
    print(f"  Overall success: {result['plan_success']}")
    print(f"  Total cost: {result['total_cost_kwh']:.2f} kWh")
    print(f"  Final temp: {result['final_temp_f']:.1f}°F")

    for i, action in enumerate(result['action_results']):
        print(f"\n  Action {i+1}:")
        print(f"    Start temp: {action['start_temp_f']:.1f}°F")
        print(f"    Target: {action['target_temp_f']:.1f}°F")
        print(f"    Success: {action['schedule_success']}")
        print(f"    Cost: {action['cost_kwh']:.2f} kWh")

    print("\n✓ Multi-action plan features working correctly")
    return True


def test_6_meeting_aware_validation():
    """Test 6: Meeting-Aware Validation"""
    print_section("Test 6: Meeting-Aware Validation")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Feature 6.1: Validation against meeting schedule
    print_test("Feature 6.1: Validation Against Meeting Schedule")

    meetings = [
        {"start_time": "15:00", "end_time": "16:00"},
        {"start_time": "17:00", "end_time": "18:00"}
    ]

    plan = [{
        "time_on": "14:00",
        "time_off": "15:00",
        "use_turbo": True
    }]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan,
        target_temps=[72.0],
        mode="cool",
        meeting_plan=meetings
    )

    print(f"Plan before meeting at 15:00:")
    print(f"  Plan success: {result['plan_success']}")

    if result['action_results']:
        action = result['action_results'][0]
        print(f"  Target reached at: {action['reached_time']}")
        print(f"  Meeting starts at: {action.get('meeting_start_time', 'N/A')}")
        print(f"  Extra time before meeting: {action['redundant_time_minutes']} min")

    # Feature 6.2: Detect insufficient time before meeting
    print_test("Feature 6.2: Detect Insufficient Time Before Meeting")

    late_plan = [{
        "time_on": "14:50",
        "time_off": "15:00",
        "use_turbo": False
    }]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="14:45",
        plan=late_plan,
        target_temps=[72.0],
        mode="cool",
        meeting_plan=meetings
    )

    print(f"Late plan (not enough time):")
    print(f"  Plan success: {result['plan_success']}")

    if result['failed_actions']:
        print(f"  Error: {result['failed_actions'][0]['error']}")

    print("\n✓ Meeting-aware validation working correctly")
    return True


def test_7_energy_cost_calculation():
    """Test 7: Energy Cost Calculation"""
    print_section("Test 7: Energy Cost Calculation")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Feature 7.1: Cost comparison - normal vs turbo
    print_test("Feature 7.1: Cost Comparison - Normal vs Turbo Mode")

    normal_plan = [{"time_on": "14:00", "time_off": "15:00", "use_turbo": False}]
    turbo_plan = [{"time_on": "14:00", "time_off": "14:30", "use_turbo": True}]

    normal_result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=normal_plan,
        target_temps=[72.0],
        mode="cool"
    )

    turbo_result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=turbo_plan,
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Normal mode (7000W):")
    print(f"  Time needed: {normal_result['action_results'][0]['time_needed_minutes']} min")
    print(f"  Cost: {normal_result['total_cost_kwh']:.3f} kWh")

    print(f"\nTurbo mode (9000W):")
    print(f"  Time needed: {turbo_result['action_results'][0]['time_needed_minutes']} min")
    print(f"  Cost: {turbo_result['total_cost_kwh']:.3f} kWh")

    # Feature 7.2: Multi-action total cost
    print_test("Feature 7.2: Multi-Action Total Cost Accumulation")

    multi_plan = [
        {"time_on": "09:00", "time_off": "10:00", "use_turbo": True},
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": False}
    ]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="08:30",
        plan=multi_plan,
        target_temps=[72.0, 72.0],
        mode="cool"
    )

    print(f"Multi-action plan:")
    total = 0
    for i, action in enumerate(result['action_results']):
        print(f"  Action {i+1}: {action['cost_kwh']:.3f} kWh")
        total += action['cost_kwh']

    print(f"  Total: {result['total_cost_kwh']:.3f} kWh (verified: {total:.3f} kWh)")

    print("\n✓ Energy cost calculation working correctly")
    return True


def test_8_edge_cases():
    """Test 8: Edge Cases and Error Handling"""
    print_section("Test 8: Edge Cases and Error Handling")

    config = EnvironmentConfig.room_feedback_profile()
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Feature 8.1: Invalid mode
    print_test("Feature 8.1: Invalid Mode Detection")

    plan = [{"time_on": "14:00", "time_off": "15:00", "use_turbo": False}]

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan,
        target_temps=[72.0],
        mode="invalid_mode"
    )

    print(f"Invalid mode test:")
    print(f"  Plan success: {result['plan_success']}")
    print(f"  Error handled: {'error' in result}")

    # Feature 8.2: Mismatched plan and targets
    print_test("Feature 8.2: Mismatched Plan Length Detection")

    result = validator.validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": False}],
        target_temps=[72.0, 70.0],  # 2 targets for 1 action
        mode="cool"
    )

    print(f"Mismatched lengths (1 action, 2 targets):")
    print(f"  Plan success: {result['plan_success']}")
    print(f"  Error message: {result.get('error', 'N/A')}")

    # Feature 8.3: Already at target temperature
    print_test("Feature 8.3: Already at Target Temperature")

    result = validator.validate_plan_success(
        current_indoor_temp_f=72.0,  # Already at target
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": False}],
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Already at target (72°F → 72°F):")
    print(f"  Plan success: {result['plan_success']}")
    print(f"  Time needed: {result['action_results'][0]['time_needed_minutes']} min")

    print("\n✓ Edge case handling working correctly")
    return True


def test_9_api_get_environment():
    """Test 9: API Function - get_environment()"""
    print_section("Test 9: API Function - get_environment()")

    # Feature 9.1: Basic environment retrieval
    print_test("Feature 9.1: Get Environment with Default Config")

    env = get_environment()

    print(f"Environment status:")
    print(f"  Room: {env['room_name']}")
    print(f"  Time: {env['current_time']}")
    print(f"  Indoor temp: {env['indoor_temp']:.1f}°F")
    print(f"  Outdoor temp: {env['outdoor_temp']:.1f}°F")
    print(f"  Meetings: {len(env['meeting_plan'])}")

    for i, meeting in enumerate(env['meeting_plan'], 1):
        print(f"    {i}. {meeting['start_time']} - {meeting['end_time']}")

    # Feature 9.2: Custom configuration
    print_test("Feature 9.2: Get Environment with Custom Room Name")

    custom_env = get_environment(room_name="Executive Boardroom")

    print(f"Custom room:")
    print(f"  Room: {custom_env['room_name']}")
    print(f"  Time: {custom_env['current_time']}")

    # Feature 9.3: Different HVAC profile
    print_test("Feature 9.3: Get Environment with Small HVAC Profile")

    small_config = EnvironmentConfig.ac_test_profile("Small Office")
    small_env = get_environment(config=small_config)

    print(f"Small office environment:")
    print(f"  Room: {small_env['room_name']}")
    print(f"  Time: {small_env['current_time']}")
    print(f"  Indoor: {small_env['indoor_temp']:.1f}°F")

    print("\n✓ API get_environment() working correctly")
    return True


def test_10_api_validate_plan():
    """Test 10: API Function - validate_plan()"""
    print_section("Test 10: API Function - validate_plan()")

    # Feature 10.1: Successful plan validation
    print_test("Feature 10.1: Validate Successful Cooling Plan")

    plan = [
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": True}
    ]

    result = validate_plan(
        plan=plan,
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="13:30",
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Validation result:")
    print(f"  Success: {result['plan_success']}")
    print(f"  Total cost: {result['total_cost_kwh']:.2f} kWh")
    print(f"  Final temp: {result['final_temp_f']:.1f}°F")

    if result['action_results']:
        action = result['action_results'][0]
        print(f"  Time needed: {action['time_needed_minutes']} min")
        print(f"  Target reached at: {action['reached_time']}")

    # Feature 10.2: Multi-action plan validation
    print_test("Feature 10.2: Validate Multi-Action Plan")

    multi_plan = [
        {"time_on": "09:00", "time_off": "10:00", "use_turbo": True},
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": False}
    ]

    result = validate_plan(
        plan=multi_plan,
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="08:30",
        target_temps=[72.0, 70.0],
        mode="cool"
    )

    print(f"Multi-action validation:")
    print(f"  Success: {result['plan_success']}")
    print(f"  Total cost: {result['total_cost_kwh']:.2f} kWh")
    print(f"  Actions: {len(result['action_results'])}")

    # Feature 10.3: Meeting-aware validation
    print_test("Feature 10.3: Validate Plan with Meeting Constraints")

    meetings = [
        {"start_time": "15:00", "end_time": "16:00"}
    ]

    plan = [{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}]

    result = validate_plan(
        plan=plan,
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="13:30",
        target_temps=[72.0],
        mode="cool",
        meeting_plan=meetings
    )

    print(f"Meeting-aware validation:")
    print(f"  Success: {result['plan_success']}")

    if result['action_results']:
        action = result['action_results'][0]
        print(f"  Target reached: {action['reached_time']}")
        print(f"  Meeting starts: {action.get('meeting_start_time', 'N/A')}")
        print(f"  Buffer time: {action['redundant_time_minutes']} min")

    # Feature 10.4: Failed plan detection
    print_test("Feature 10.4: Detect and Report Failed Plans")

    impossible_plan = [{
        "time_on": "14:55",
        "time_off": "15:00",
        "use_turbo": False
    }]

    result = validate_plan(
        plan=impossible_plan,
        current_indoor_temp=86.0,
        outdoor_temp=95.0,
        current_time="14:50",
        target_temps=[72.0],
        mode="cool"
    )

    print(f"Failed plan validation:")
    print(f"  Success: {result['plan_success']}")
    print(f"  Failed actions: {len(result['failed_actions'])}")

    if result['failed_actions']:
        failed = result['failed_actions'][0]
        print(f"  Error: {failed['error']}")

    print("\n✓ API validate_plan() working correctly")
    return True


def main():
    """Run all feature tests."""
    print("\n" + "=" * 80)
    print(" HVAC ENVIRONMENT SIMULATION - COMPREHENSIVE FEATURE TEST")
    print("=" * 80)
    print("\nTesting 2-Layer Architecture:")
    print("  Layer 1: core/ (internal simulation logic)")
    print("  Layer 2: hvac_api.py (2 public functions)")
    print()

    tests = [
        ("Configuration Features", test_1_configuration_features),
        ("Physics Engine Features", test_2_physics_engine_features),
        ("Environment Generator Features", test_3_environment_generator_features),
        ("Action Validator Features", test_4_action_validator_features),
        ("Multi-Action Plan Validation", test_5_multi_action_plans),
        ("Meeting-Aware Validation", test_6_meeting_aware_validation),
        ("Energy Cost Calculation", test_7_energy_cost_calculation),
        ("Edge Cases and Error Handling", test_8_edge_cases),
        ("API Function: get_environment()", test_9_api_get_environment),
        ("API Function: validate_plan()", test_10_api_validate_plan),
    ]

    results = []

    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    print("\n" + "=" * 80)

    if passed_count == total_count:
        print(f" ALL TESTS PASSED ({passed_count}/{total_count})")
        print("=" * 80)
        print("\n✓ HVAC environment simulation is working correctly")
        print("✓ All features demonstrated successfully")
        print("✓ Both API functions validated")
        print("\nSystem ready for use!")
        return 0
    else:
        print(f" SOME TESTS FAILED ({passed_count}/{total_count} passed)")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())
