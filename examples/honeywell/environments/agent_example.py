#!/usr/bin/env python3
"""
Example AI Agent using the HVAC API.

This demonstrates how an AI agent would use get_env_status() and get_feedback()
to make intelligent HVAC control decisions.
"""

from hvac_api import get_env_status, get_feedback


def ai_agent_decision():
    """
    AI agent that makes intelligent HVAC decisions.

    Strategy:
    1. Get current environment status
    2. Determine if cooling is needed based on:
       - Current temperature
       - Upcoming meetings
    3. Create an optimal cooling plan
    4. Validate the plan
    5. Execute or adjust based on feedback
    """
    print("=" * 80)
    print("AI AGENT: HVAC Control Decision System")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: Get Environment Status
    # ========================================================================
    print("STEP 1: Getting environment status...")
    print("-" * 80)

    status = get_env_status()

    print(f"Room: {status['room_name']}")
    print(f"Current Time: {status['current_time']}")
    print(f"Indoor Temperature: {status['indoor_temp']}°F")
    print(f"Outdoor Temperature: {status['outdoor_temp']}°F")
    print(f"Scheduled Meetings: {len(status['meeting_plan'])}")

    if status['meeting_plan']:
        print("\nMeeting Schedule:")
        for i, meeting in enumerate(status['meeting_plan']):
            print(f"  {i+1}. {meeting['start_time']} - {meeting['end_time']}")

    print()

    # ========================================================================
    # STEP 2: Analyze Situation
    # ========================================================================
    print("STEP 2: Analyzing situation...")
    print("-" * 80)

    COMFORT_TEMP = 72.0  # Desired comfort temperature
    COOLING_THRESHOLD = 75.0  # Start cooling if above this

    needs_cooling = status['indoor_temp'] > COOLING_THRESHOLD
    has_meetings = len(status['meeting_plan']) > 0

    print(f"Indoor temp ({status['indoor_temp']}°F) > Threshold ({COOLING_THRESHOLD}°F)? {needs_cooling}")
    print(f"Upcoming meetings? {has_meetings}")

    if not needs_cooling:
        print("\n✓ Temperature is comfortable. No action needed.")
        return

    if not has_meetings:
        print("\n→ No meetings scheduled. Energy-saving mode: No cooling.")
        return

    print(f"\n→ Decision: Need to cool to {COMFORT_TEMP}°F for upcoming meetings")
    print()

    # ========================================================================
    # STEP 3: Create Optimal Plan
    # ========================================================================
    print("STEP 3: Creating optimal cooling plan...")
    print("-" * 80)

    # Strategy: Cool before each meeting
    # Use turbo if time is tight, base mode if we have plenty of time

    first_meeting = status['meeting_plan'][0]

    # Parse time to calculate time available
    current_h, current_m = map(int, status['current_time'].split(':'))
    meeting_h, meeting_m = map(int, first_meeting['start_time'].split(':'))

    current_minutes = current_h * 60 + current_m
    meeting_minutes = meeting_h * 60 + meeting_m
    time_until_meeting = meeting_minutes - current_minutes

    print(f"First meeting starts at: {first_meeting['start_time']}")
    print(f"Time until meeting: {time_until_meeting} minutes")

    # Decision: Use turbo if less than 30 minutes, otherwise use base mode
    use_turbo = time_until_meeting < 30

    print(f"Strategy: Use {'TURBO' if use_turbo else 'BASE'} mode")

    # Create the plan
    plan = [{
        "time_on": status['current_time'],
        "time_off": first_meeting['start_time'],
        "use_turbo": use_turbo
    }]

    target_temps = [COMFORT_TEMP]

    print(f"\nPlan:")
    print(f"  Action 1: {plan[0]['time_on']} → {plan[0]['time_off']}")
    print(f"    Mode: {'Turbo' if plan[0]['use_turbo'] else 'Base'}")
    print(f"    Target: {COMFORT_TEMP}°F")
    print()

    # ========================================================================
    # STEP 4: Validate Plan with Feedback
    # ========================================================================
    print("STEP 4: Validating plan with HVAC simulation...")
    print("-" * 80)

    feedback = get_feedback(
        current_indoor_temp=status['indoor_temp'],
        outdoor_temp=status['outdoor_temp'],
        current_time=status['current_time'],
        plan=plan,
        target_temps=target_temps,
        mode="cool"
    )

    print(f"Validation Result: {feedback['plan_success'].upper()}")
    print()

    # ========================================================================
    # STEP 5: Make Final Decision
    # ========================================================================
    print("STEP 5: Final decision...")
    print("-" * 80)

    if feedback['plan_success'] == 'success':
        action = feedback['action_results'][0]

        print("✓ PLAN IS FEASIBLE - EXECUTE!")
        print()
        print(f"Execution Details:")
        print(f"  Turn on AC at: {action['time_on']}")
        print(f"  Mode: {'Turbo (9000W)' if use_turbo else 'Base (7000W)'}")
        print(f"  Will reach {COMFORT_TEMP}°F at: {action['reached_time']}")
        print(f"  Turn off AC at: {action['time_off']}")
        print()
        print(f"Performance:")
        print(f"  Time needed: {action['time_needed_minutes']} minutes")
        print(f"  Time available: {action['time_available_minutes']} minutes")
        print(f"  Extra safety margin: {action['redundant_time_minutes']} minutes")
        print()
        print(f"Energy Cost:")
        print(f"  This action: {action['cost_kwh']:.3f} kWh")
        print(f"  Total plan: {feedback['total_cost_kwh']:.3f} kWh")
        print()
        print(f"Final Result:")
        print(f"  Room will be at {feedback['final_temp_f']:.1f}°F when meeting starts")

    else:
        print("✗ PLAN FAILED - NEED TO ADJUST!")
        print()

        failed = feedback['failed_actions'][0]
        action = feedback['action_results'][0]

        print(f"Problem: {failed['error']}")
        print()
        print(f"Details:")
        print(f"  Time needed: {action['time_needed_minutes']} minutes")
        print(f"  Time available: {action['time_available_minutes']} minutes")
        print(f"  Shortfall: {action['time_needed_minutes'] - action['time_available_minutes']} minutes")
        print()

        # Suggest alternative
        if not use_turbo:
            print("💡 Suggestion: Try TURBO mode for faster cooling")
        else:
            print("💡 Suggestion: Target temperature may be too aggressive")
            print(f"   Consider a higher target (e.g., 74°F instead of {COMFORT_TEMP}°F)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    ai_agent_decision()
