#!/usr/bin/env python3
"""
HVAC Environment Simulation API

2-Layer Architecture:
- Layer 1 (core/): Internal simulation logic (physics, validation, config)
- Layer 2 (this file): Public API - 2 essential functions

Public Functions:
1. get_environment() - Get current environment status
2. validate_plan() - Validate HVAC action plan and get feedback
"""

from typing import Optional
from core import (
    EnvironmentConfig,
    EnvironmentGenerator,
    ThermalPhysics,
    ActionValidator
)


def get_environment(
    room_name: str = "Conference Room A",
    config: Optional[EnvironmentConfig] = None
) -> dict:
    """
    Get current environment status.

    Args:
        room_name: Name of the room (default: "Conference Room A")
        config: Optional custom configuration (default: standard 7000W HVAC)

    Returns:
        dict with:
            - room_name: str
            - current_time: str (HH:MM format)
            - indoor_temp: float (°F)
            - outdoor_temp: float (°F)
            - meeting_plan: list[dict] with start_time and end_time

    Example:
        >>> env = get_environment()
        >>> print(f"Indoor: {env['indoor_temp']}°F at {env['current_time']}")
        >>> print(f"Meetings today: {len(env['meeting_plan'])}")
    """
    if config is None:
        config = EnvironmentConfig.room_feedback_profile(room_name)

    generator = EnvironmentGenerator(config)
    return generator.generate_state()


def validate_plan(
    plan: list[dict],
    current_indoor_temp: float,
    outdoor_temp: float,
    current_time: str,
    target_temps: list[float],
    mode: str = "cool",
    meeting_plan: Optional[list[dict]] = None,
    config: Optional[EnvironmentConfig] = None
) -> dict:
    """
    Validate HVAC action plan and get detailed feedback.

    Args:
        plan: List of actions, each dict with:
            - time_on: str (HH:MM)
            - time_off: str (HH:MM)
            - use_turbo: bool
        current_indoor_temp: Current indoor temperature (°F)
        outdoor_temp: Outdoor temperature (°F)
        current_time: Current time (HH:MM format)
        target_temps: Target temperature for each action (°F)
        mode: "cool" or "heat" (default: "cool")
        meeting_plan: Optional list of meetings with start_time and end_time
        config: Optional custom configuration (default: standard 7000W HVAC)

    Returns:
        dict with:
            - plan_success: "success" or "failed"
            - total_cost_kwh: float
            - final_temp_f: float
            - action_results: list[dict] with detailed results per action
            - failed_actions: list[dict] with failed action details

    Example:
        >>> plan = [{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}]
        >>> result = validate_plan(
        ...     plan=plan,
        ...     current_indoor_temp=86.0,
        ...     outdoor_temp=95.0,
        ...     current_time="13:30",
        ...     target_temps=[72.0],
        ...     mode="cool"
        ... )
        >>> print(f"Success: {result['plan_success']}")
        >>> print(f"Cost: {result['total_cost_kwh']:.2f} kWh")
    """
    if config is None:
        config = EnvironmentConfig.room_feedback_profile()

    # Validate inputs
    if len(plan) != len(target_temps):
        return {
            "plan_success": "failed",
            "total_cost_kwh": 0.0,
            "final_temp_f": current_indoor_temp,
            "action_results": [],
            "failed_actions": [],
            "error": f"Plan has {len(plan)} actions but {len(target_temps)} target temperatures"
        }

    if mode not in ["cool", "heat"]:
        return {
            "plan_success": "failed",
            "total_cost_kwh": 0.0,
            "final_temp_f": current_indoor_temp,
            "action_results": [],
            "failed_actions": [],
            "error": f"Invalid mode '{mode}'. Must be 'cool' or 'heat'"
        }

    # Create physics engine and validator
    physics = ThermalPhysics(config.hvac_config, config.thermal_config)
    validator = ActionValidator(physics, config)

    # Validate the plan
    return validator.validate_plan_success(
        current_indoor_temp_f=current_indoor_temp,
        outdoor_temp_f=outdoor_temp,
        current_time=current_time,
        plan=plan,
        target_temps=target_temps,
        mode=mode,
        meeting_plan=meeting_plan
    )


if __name__ == "__main__":
    """Demo the 2 API functions."""
    print("=" * 80)
    print("HVAC API Demo - 2 Essential Functions")
    print("=" * 80)
    print()

    # Function 1: Get environment
    print("Function 1: get_environment()")
    print("-" * 80)
    env = get_environment()
    print(f"Room: {env['room_name']}")
    print(f"Time: {env['current_time']}")
    print(f"Indoor: {env['indoor_temp']:.1f}°F")
    print(f"Outdoor: {env['outdoor_temp']:.1f}°F")
    print(f"Meetings: {len(env['meeting_plan'])}")
    for i, meeting in enumerate(env['meeting_plan'], 1):
        print(f"  {i}. {meeting['start_time']} - {meeting['end_time']}")
    print()

    # Function 2: Validate plan
    print("Function 2: validate_plan()")
    print("-" * 80)

    if env['meeting_plan']:
        first_meeting = env['meeting_plan'][0]
        plan = [{
            "time_on": env['current_time'],
            "time_off": first_meeting['start_time'],
            "use_turbo": True
        }]

        print(f"Plan: Cool to 72°F before meeting at {first_meeting['start_time']}")

        result = validate_plan(
            plan=plan,
            current_indoor_temp=env['indoor_temp'],
            outdoor_temp=env['outdoor_temp'],
            current_time=env['current_time'],
            target_temps=[72.0],
            mode="cool",
            meeting_plan=env['meeting_plan']
        )

        print(f"Result: {result['plan_success']}")
        print(f"Cost: {result['total_cost_kwh']:.2f} kWh")
        print(f"Final temp: {result['final_temp_f']:.1f}°F")

        if result['action_results']:
            action = result['action_results'][0]
            print(f"Time needed: {action['time_needed_minutes']} min")
            if action['schedule_success'] == 'success':
                print(f"Target reached at: {action['reached_time']}")
    else:
        print("No meetings scheduled - skipping plan validation demo")

    print()
    print("=" * 80)
