#!/usr/bin/env python3
"""
Verification script to ensure refactored code produces identical results.

Compares outputs from:
- Old: room_feedback.py physics
- New: thermal_physics.py + config.py

Tests both HVAC profiles (2000W and 7000W).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import old implementation from deprecated folder
sys.path.insert(0, str(Path(__file__).parent.parent / "_deprecated"))
from room_feedback import hvac_time as old_hvac_time
from room_feedback import estimate_temp_at_time as old_estimate_temp
from room_feedback import check_hvac_schedule as old_check_schedule

# Import new implementation
from core import EnvironmentConfig, ThermalPhysics


def test_hvac_time():
    """Test hvac_time function produces identical results."""
    print("=" * 80)
    print("TEST 1: hvac_time() - Time to reach target temperature")
    print("=" * 80)

    # Create new physics engine with room_feedback.py profile (7000W)
    config = EnvironmentConfig.room_feedback_profile()
    new_physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    test_cases = [
        # (current_temp, target_temp, outdoor_temp, mode, use_turbo, description)
        (86.0, 77.0, 95.0, "cool", True, "Cool with turbo (86→77°F, out=95°F)"),
        (86.0, 77.0, 95.0, "cool", False, "Cool without turbo (86→77°F, out=95°F)"),
        (64.0, 75.0, 50.0, "heat", True, "Heat with turbo (64→75°F, out=50°F)"),
        (64.0, 75.0, 50.0, "heat", False, "Heat without turbo (64→75°F, out=50°F)"),
        (90.0, 72.0, 95.0, "cool", True, "Large cooling (90→72°F, out=95°F)"),
        (75.0, 75.0, 80.0, "cool", False, "No change (75→75°F)"),
    ]

    all_passed = True
    for current, target, outdoor, mode, turbo, desc in test_cases:
        old_result = old_hvac_time(
            current, target, mode=mode,
            T_out_F=outdoor, use_turbo=turbo
        )
        new_result = new_physics.hvac_time(
            current, target, outdoor, mode=mode, use_turbo=turbo
        )

        passed = old_result == new_result
        all_passed = all_passed and passed
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"\n{status}: {desc}")
        print(f"  Old result: {old_result} min")
        print(f"  New result: {new_result} min")

    return all_passed


def test_estimate_temp():
    """Test estimate_temp_at_time function."""
    print("\n" + "=" * 80)
    print("TEST 2: estimate_temp_at_time() - Temperature evolution")
    print("=" * 80)

    config = EnvironmentConfig.room_feedback_profile()
    new_physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    test_cases = [
        # (current_indoor, outdoor, current_time, target_time, description)
        (75.0, 95.0, "14:00", "15:00", "1 hour, warming up"),
        (75.0, 95.0, "14:00", "18:00", "4 hours, warming up"),
        (80.0, 70.0, "14:00", "16:00", "2 hours, cooling down"),
        (85.0, 85.0, "10:00", "12:00", "2 hours, stable temp"),
    ]

    all_passed = True
    for current_indoor, outdoor, current_time, target_time, desc in test_cases:
        old_result = old_estimate_temp(
            current_indoor, outdoor, current_time, target_time
        )

        # Calculate duration for new API
        def parse_time(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        duration = parse_time(target_time) - parse_time(current_time)

        new_result = new_physics.estimate_temp_at_time(
            current_indoor, outdoor, duration
        )

        # Allow small floating point differences (< 0.1°F)
        diff = abs(old_result - new_result)
        passed = diff < 0.1
        all_passed = all_passed and passed
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"\n{status}: {desc}")
        print(f"  Old result: {old_result:.2f}°F")
        print(f"  New result: {new_result:.2f}°F")
        if diff >= 0.1:
            print(f"  Difference: {diff:.2f}°F")

    return all_passed


def test_check_schedule():
    """Test check_hvac_schedule function."""
    print("\n" + "=" * 80)
    print("TEST 3: check_hvac_schedule() - Can reach target in time?")
    print("=" * 80)

    config = EnvironmentConfig.room_feedback_profile()
    new_physics = ThermalPhysics(config.hvac_config, config.thermal_config)

    test_cases = [
        # (current, target, current_time, target_time, outdoor, turbo, mode, description)
        (86.0, 77.0, "14:00", "15:30", 95.0, True, "cool", "Success: enough time with turbo"),
        (86.0, 77.0, "14:00", "14:30", 95.0, False, "cool", "Fail: not enough time"),
        (64.0, 75.0, "08:00", "09:00", 50.0, True, "heat", "Success: heating with turbo"),
    ]

    all_passed = True
    for current, target, current_time, target_time, outdoor, turbo, mode, desc in test_cases:
        old_result = old_check_schedule(
            current, target, turbo, current_time, target_time,
            mode=mode, t_out_f=outdoor
        )

        # Calculate duration for new API
        def parse_time(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        time_available = parse_time(target_time) - parse_time(current_time)

        new_result = new_physics.check_hvac_schedule(
            current, target, time_available, outdoor,
            mode=mode, use_turbo=turbo
        )

        # Compare key fields
        passed = (
            old_result["reached_temp"] == new_result["reached_temp"] and
            old_result["time_needed_minutes"] == new_result["time_needed_minutes"] and
            old_result["time_available_minutes"] == new_result["time_available_minutes"]
        )
        all_passed = all_passed and passed
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"\n{status}: {desc}")
        print(f"  Old: {old_result['reached_temp']}, "
              f"need {old_result['time_needed_minutes']} min, "
              f"have {old_result['time_available_minutes']} min")
        print(f"  New: {new_result['reached_temp']}, "
              f"need {new_result['time_needed_minutes']} min, "
              f"have {new_result['time_available_minutes']} min")

    return all_passed


def test_both_profiles():
    """Test that both HVAC profiles (2000W and 7000W) work correctly."""
    print("\n" + "=" * 80)
    print("TEST 4: Both HVAC Profiles (2000W and 7000W)")
    print("=" * 80)

    # Test 2000W profile
    config_2000w = EnvironmentConfig.ac_test_profile()
    physics_2000w = ThermalPhysics(config_2000w.hvac_config, config_2000w.thermal_config)

    result_2000w = physics_2000w.hvac_time(86.0, 77.0, 95.0, mode="cool", use_turbo=True)

    print(f"\n2000W Profile (ac_test.py parameters):")
    print(f"  Base capacity: {config_2000w.hvac_config.base_capacity_w}W")
    print(f"  Turbo capacity: {config_2000w.hvac_config.turbo_capacity_w}W")
    print(f"  Time to cool 86→77°F with turbo: {result_2000w} min")

    # Test 7000W profile
    config_7000w = EnvironmentConfig.room_feedback_profile()
    physics_7000w = ThermalPhysics(config_7000w.hvac_config, config_7000w.thermal_config)

    result_7000w = physics_7000w.hvac_time(86.0, 77.0, 95.0, mode="cool", use_turbo=True)

    print(f"\n7000W Profile (room_feedback.py parameters):")
    print(f"  Base capacity: {config_7000w.hvac_config.base_capacity_w}W")
    print(f"  Turbo capacity: {config_7000w.hvac_config.turbo_capacity_w}W")
    print(f"  Time to cool 86→77°F with turbo: {result_7000w} min")

    # 7000W should be faster than 2000W
    passed = result_7000w < result_2000w
    status = "✓ PASS" if passed else "✗ FAIL"

    print(f"\n{status}: 7000W faster than 2000W? {result_7000w} < {result_2000w}")

    return passed


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("REFACTORING VERIFICATION TEST SUITE")
    print("Comparing old vs new implementation")
    print("=" * 80 + "\n")

    results = {
        "hvac_time": test_hvac_time(),
        "estimate_temp": test_estimate_temp(),
        "check_schedule": test_check_schedule(),
        "both_profiles": test_both_profiles(),
    }

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("Refactoring successfully preserves all functionality!")
        return 0
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("Please review the differences above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
