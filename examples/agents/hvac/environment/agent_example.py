#!/usr/bin/env python3
"""
Simple demonstration of the 2 HVAC API functions.

Shows:
1. get_env_status() - Get current environment
2. get_feedback() - Validate HVAC plan
"""

from hvac_api import get_env_status, get_feedback


# ============================================================================
# DEMONSTRATION
# ============================================================================


def main():
    print("=" * 80)
    print("HVAC API DEMONSTRATION - 2 Simple Functions")
    print("=" * 80)
    print()

    # ------------------------------------------------------------------------
    # FUNCTION 1: get_env_status()
    # ------------------------------------------------------------------------
    print("FUNCTION 1: get_env_status()")
    print("-" * 80)
    print("Get current environment state (temperature, time, meetings)")
    print()

    # Call the real API
    status = get_env_status()

    print("Input:  None (just call the function)")
    print()
    print("Output:")
    print(f"  room_name:    {status['room_name']}")
    print(f"  current_time: {status['current_time']}")
    print(f"  indoor_temp:  {status['indoor_temp']}°F")
    print(f"  outdoor_temp: {status['outdoor_temp']}°F")
    print(f"  meetings:     {len(status['meeting_plan'])} scheduled")
    for i, meeting in enumerate(status["meeting_plan"], 1):
        print(f"    {i}. {meeting['start_time']} - {meeting['end_time']}")
    print()

    # ------------------------------------------------------------------------
    # FUNCTION 2: get_feedback()
    # ------------------------------------------------------------------------
    print("FUNCTION 2: get_feedback()")
    print("-" * 80)
    print("Validate an HVAC plan and get detailed feedback")
    print()

    # Create a simple cooling plan
    # If there are meetings, cool before the first one
    # If no meetings, cool for 1 hour
    if status["meeting_plan"]:
        time_off = status["meeting_plan"][0]["start_time"]
    else:
        # Calculate 1 hour from current time
        h, m = map(int, status["current_time"].split(":"))
        time_off = f"{(h + 1) % 24:02d}:{m:02d}"

    plan = [{"time_on": status["current_time"], "time_off": time_off, "use_turbo": False}]
    target_temps = [72.0]

    # Automatically detect if we need heating or cooling
    if status["indoor_temp"] > target_temps[0]:
        mode = "cool"
    else:
        mode = "heat"

    print("Input:")
    print(f"  current_indoor_temp: {status['indoor_temp']}°F")
    print(f"  outdoor_temp:        {status['outdoor_temp']}°F")
    print(f"  current_time:        {status['current_time']}")
    print(f"  plan:                {plan[0]['time_on']} → {plan[0]['time_off']} (turbo: {plan[0]['use_turbo']})")
    print(f"  target_temps:        {target_temps[0]}°F")
    print(f"  mode:                {mode}")
    print()

    # Call the API
    feedback = get_feedback(
        current_indoor_temp=status["indoor_temp"],
        outdoor_temp=status["outdoor_temp"],
        current_time=status["current_time"],
        plan=plan,
        target_temps=target_temps,
        mode=mode,
    )

    print("Output:")
    print(f"  plan_success:    {feedback['plan_success']}")
    print(f"  total_cost_kwh:  {feedback['total_cost_kwh']:.3f} kWh")
    print(f"  final_temp_f:    {feedback['final_temp_f']:.1f}°F")
    print()

    action = feedback["action_results"][0]
    print("  action_results[0]:")
    print(f"    time_needed_minutes:     {action['time_needed_minutes']} min")
    print(f"    time_available_minutes:  {action['time_available_minutes']} min")
    print(f"    reached_time:            {action['reached_time']}")
    print(f"    redundant_time_minutes:  {action['redundant_time_minutes']} min")
    print(f"    cost_kwh:                {action['cost_kwh']:.3f} kWh")
    print()

    # ------------------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------------------
    print("=" * 80)
    print("RESULT")
    print("=" * 80)

    if feedback["plan_success"] == "success":
        action_verb = "Cools" if mode == "cool" else "Heats"
        print("✓ Plan works!")
        print(f"  • {action_verb} from {status['indoor_temp']}°F to {target_temps[0]}°F")
        print(f"  • Takes {action['time_needed_minutes']} min (have {action['time_available_minutes']} min)")
        print(f"  • Reaches target at {action['reached_time']}")
        print(f"  • Costs {action['cost_kwh']:.3f} kWh")
    else:
        action_type = "cooling" if mode == "cool" else "heating"
        print("✗ Plan failed!")
        print(f"  • {feedback['failed_actions'][0]['error']}")
        print(f"  • Partial {action_type} cost: {action['cost_kwh']:.3f} kWh")
        print(f"  • Final temp: {feedback['final_temp_f']:.1f}°F")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
