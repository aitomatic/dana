#!/usr/bin/env python3
"""
Simple HVAC API for AI agents.

Provides two main functions:
1. get_env_status() - Get current environment state
2. get_feedback() - Get HVAC plan validation and feedback
"""

import sys
import os

# Import the environment and HVAC simulation modules
from .single_room import SingleRoomEnvironment
from .room_feedback import check_hvac_schedule, validate_plan_success


def get_env_status(room_name: str = "Conference Room A") -> dict:
    """
    Get current environment status including temperature and meeting schedule.

    Args:
        room_name: Name of the room to check (default: "Conference Room A")

    Returns:
        Dictionary with:
        - room_name: str - Name of the room
        - current_time: str - Current time in "HH:MM" format
        - indoor_temp: float - Current indoor temperature in °F
        - outdoor_temp: float - Current outdoor temperature in °F
        - meeting_plan: list[dict] - List of scheduled meetings, each with:
            - start_time: str - Meeting start time in "HH:MM"
            - end_time: str - Meeting end time in "HH:MM"

    Example:
        >>> status = get_env_status()
        >>> print(status)
        {
            "room_name": "Conference Room A",
            "current_time": "14:30",
            "indoor_temp": 86.5,
            "outdoor_temp": 95.2,
            "meeting_plan": [
                {"start_time": "15:00", "end_time": "16:30"},
                {"start_time": "17:00", "end_time": "18:00"}
            ]
        }
    """
    # Create room environment
    env = SingleRoomEnvironment(room_name=room_name)

    # Get environment state
    env_state = env.get_env()

    return {
        "room_name": env_state["room_name"],
        "current_time": env_state["current_time"],
        "indoor_temp": env_state["indoor_temp"],
        "outdoor_temp": env_state["outdoor_temp"],
        "meeting_plan": env_state["meeting_plan"]
    }


def get_feedback(
    current_indoor_temp: float,
    outdoor_temp: float,
    current_time: str,
    plan: list[dict],
    target_temps: list[float],
    mode: str = "cool",
    meeting_plan: list[dict] = None
) -> dict:
    """
    Validate an HVAC action plan and get detailed feedback.

    Args:
        current_indoor_temp: Current indoor temperature in °F
        outdoor_temp: Outdoor temperature in °F
        current_time: Current time in "HH:MM" format
        plan: List of HVAC actions, each dict with:
            - time_on: str - When to turn on HVAC ("HH:MM")
            - time_off: str - When to turn off HVAC ("HH:MM")
            - use_turbo: bool - Whether to use turbo mode
        target_temps: List of target temperatures (°F) for each action
        mode: HVAC mode, either "cool" or "heat" (default: "cool")

    Returns:
        Dictionary with:
        - plan_success: str - "success" or "failed"
        - total_cost_kwh: float - Total electricity consumption in kWh
        - final_temp_f: float - Final temperature after all actions
        - action_results: list[dict] - Detailed results for each action:
            - action_index: int - Index of the action
            - time_on: str - Start time
            - time_off: str - End time
            - target_temp_f: float - Target temperature
            - start_temp_f: float - Starting temperature
            - schedule_success: str - "success" or "failed"
            - time_needed_minutes: int - Time needed to reach target
            - time_available_minutes: int - Time available
            - reached_time: str - When target would be reached ("HH:MM")
            - redundant_time_minutes: int - Extra time available
            - cost_kwh: float - Energy cost for this action
            - error: str - Error message if failed
        - failed_actions: list[dict] - List of failed actions with details

    Example:
        >>> # Plan to cool room before meetings
        >>> plan = [
        ...     {"time_on": "14:00", "time_off": "15:00", "use_turbo": True},
        ...     {"time_on": "16:30", "time_off": "17:30", "use_turbo": False}
        ... ]
        >>> target_temps = [72.0, 70.0]
        >>>
        >>> feedback = get_feedback(
        ...     current_indoor_temp=86.0,
        ...     outdoor_temp=95.0,
        ...     current_time="13:30",
        ...     plan=plan,
        ...     target_temps=target_temps,
        ...     mode="cool"
        ... )
        >>>
        >>> if feedback["plan_success"] == "success":
        ...     print(f"Plan works! Total cost: {feedback['total_cost_kwh']:.2f} kWh")
        ...     print(f"Final temp: {feedback['final_temp_f']:.1f}°F")
        ... else:
        ...     print("Plan failed:")
        ...     for failed in feedback["failed_actions"]:
        ...         print(f"  Action {failed['action_index']}: {failed['error']}")
    """
    # Convert target_temps to list if it's a single number
    if isinstance(target_temps, (int, float)):
        target_temps = [target_temps] * len(plan)

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

    # Validate the plan using the HVAC simulation
    result = validate_plan_success(
        current_indoor_temp_f=current_indoor_temp,
        outdoor_temp_f=outdoor_temp,
        current_time=current_time,
        plan=plan,
        target_temps=target_temps,
        mode=mode,
        meeting_plan=meeting_plan
    )

    return result


# Convenience function for simple single-action validation
def check_single_action(
    current_temp: float,
    target_temp: float,
    current_time: str,
    target_time: str,
    outdoor_temp: float,
    use_turbo: bool = False,
    mode: str = "cool"
) -> dict:
    """
    Check if a single HVAC action can reach the target temperature in time.

    This is a simplified version of get_feedback() for single actions.

    Args:
        current_temp: Current indoor temperature in °F
        target_temp: Target temperature in °F
        current_time: Current time in "HH:MM" format
        target_time: When target should be reached in "HH:MM" format
        outdoor_temp: Outdoor temperature in °F
        use_turbo: Whether to use turbo mode (default: False)
        mode: HVAC mode, either "cool" or "heat" (default: "cool")

    Returns:
        Dictionary with:
        - reached_temp: str - "success" or "failed"
        - time_needed_minutes: int - Time needed to reach target
        - time_available_minutes: int - Time available
        - redundant_time_minutes: int - Extra time if successful
        - reached_time: str - When target would be reached ("HH:MM")
        - error: str - Error message if failed

    Example:
        >>> result = check_single_action(
        ...     current_temp=86.0,
        ...     target_temp=72.0,
        ...     current_time="14:00",
        ...     target_time="15:00",
        ...     outdoor_temp=95.0,
        ...     use_turbo=True
        ... )
        >>> if result["reached_temp"] == "success":
        ...     print(f"Will reach {72}°F at {result['reached_time']}")
        ...     print(f"Extra time: {result['redundant_time_minutes']} minutes")
    """
    result = check_hvac_schedule(
        current_temp_f=current_temp,
        target_temp_f=target_temp,
        use_turbo=use_turbo,
        current_time=current_time,
        target_time=target_time,
        mode=mode,
        t_out_f=outdoor_temp
    )

    return result


if __name__ == "__main__":
    """Demo the API functions."""
    print("=" * 80)
    print("HVAC API DEMO")
    print("=" * 80)
    print()

    # Example 1: Get environment status
    print("1. Getting environment status...")
    print("-" * 80)
    status = get_env_status()

    import json
    print(json.dumps(status, indent=2))
    print()

    # Example 2: Create a cooling plan based on environment
    print("2. Creating and validating an HVAC plan...")
    print("-" * 80)

    # Get current conditions from status
    current_time = status["current_time"]
    indoor_temp = status["indoor_temp"]
    outdoor_temp = status["outdoor_temp"]
    meetings = status["meeting_plan"]

    print(f"Current conditions:")
    print(f"  Time: {current_time}")
    print(f"  Indoor: {indoor_temp}°F")
    print(f"  Outdoor: {outdoor_temp}°F")
    print(f"  Meetings: {len(meetings)}")
    print()

    if meetings:
        # Create a plan to cool before first meeting
        first_meeting = meetings[0]
        print(f"First meeting: {first_meeting['start_time']} - {first_meeting['end_time']}")

        # Simple plan: one action with turbo to cool before meeting
        plan = [
            {
                "time_on": current_time,
                "time_off": first_meeting["start_time"],
                "use_turbo": True
            }
        ]
        target_temps = [72.0]  # Target 72°F for the meeting

        print(f"\nPlan: Cool to 72°F before meeting starts")
        print(f"  Action: {current_time} → {first_meeting['start_time']} (turbo mode)")
        print()

        # Get feedback
        feedback = get_feedback(
            current_indoor_temp=indoor_temp,
            outdoor_temp=outdoor_temp,
            current_time=current_time,
            plan=plan,
            target_temps=target_temps,
            mode="cool"
        )

        print("Feedback:")
        print(f"  Overall result: {feedback['plan_success']}")
        print(f"  Total cost: {feedback['total_cost_kwh']:.3f} kWh")
        print(f"  Final temp: {feedback['final_temp_f']:.1f}°F")
        print()

        if feedback["action_results"]:
            action = feedback["action_results"][0]
            print(f"  Action details:")
            print(f"    Success: {action['schedule_success']}")
            print(f"    Time needed: {action['time_needed_minutes']} min")
            print(f"    Time available: {action['time_available_minutes']} min")
            if action['schedule_success'] == 'success':
                print(f"    Will reach target at: {action['reached_time']}")
                print(f"    Extra time: {action['redundant_time_minutes']} min")
            else:
                print(f"    Error: {action['error']}")
    else:
        print("No meetings scheduled. Skipping plan creation.")

    print()
    print("=" * 80)
