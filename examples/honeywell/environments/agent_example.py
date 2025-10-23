#!/usr/bin/env python3
"""
Example AI Agent using the HVAC API - Testing Version

This demonstrates how an AI agent would use get_env_status() and get_feedback()
with mocked inputs for easy testing and demonstration.
"""

from hvac_api import get_feedback


def mock_env_status(scenario="success"):
    """
    Mock environment status for testing.

    Args:
        scenario: "success" for achievable plan, "tight" for tight but achievable, "failed" for impossible
    """
    if scenario == "success":
        # Plenty of time - 60 minutes
        return {
            "room_name": "Conference Room A",
            "current_time": "14:00",
            "indoor_temp": 86.0,
            "outdoor_temp": 95.0,
            "meeting_plan": [
                {"start_time": "15:00", "end_time": "16:30"},
                {"start_time": "17:00", "end_time": "18:00"}
            ]
        }
    elif scenario == "tight":
        # Tight schedule - 30 minutes
        return {
            "room_name": "Conference Room A",
            "current_time": "14:30",
            "indoor_temp": 86.0,
            "outdoor_temp": 95.0,
            "meeting_plan": [
                {"start_time": "15:00", "end_time": "16:30"}
            ]
        }
    else:  # "failed"
        # Not enough time - 10 minutes, impossible to cool 14°F
        return {
            "room_name": "Conference Room A",
            "current_time": "14:50",
            "indoor_temp": 86.0,
            "outdoor_temp": 95.0,
            "meeting_plan": [
                {"start_time": "15:00", "end_time": "16:30"}
            ]
        }


def print_header(title):
    """Print a section header."""
    print()
    print("=" * 80)
    print(f"{title}")
    print("=" * 80)


def print_section(title):
    """Print a subsection header."""
    print()
    print(title)
    print("-" * 80)


def ai_agent_decision(scenario="success"):
    """
    AI agent that makes intelligent HVAC decisions.

    Args:
        scenario: "success", "tight", or "failed" to test different time constraints
    """
    print_header("AI AGENT: HVAC Control Decision System")

    # ========================================================================
    # STEP 1: Get Environment Status (Mocked)
    # ========================================================================
    print_section("STEP 1: Getting environment status...")

    status = mock_env_status(scenario)

    print(f"Room: {status['room_name']}")
    print(f"Current Time: {status['current_time']}")
    print(f"Indoor Temperature: {status['indoor_temp']}°F")
    print(f"Outdoor Temperature: {status['outdoor_temp']}°F")
    print(f"Scheduled Meetings: {len(status['meeting_plan'])}")

    if status['meeting_plan']:
        print("\nMeeting Schedule:")
        for i, meeting in enumerate(status['meeting_plan'], 1):
            print(f"  {i}. {meeting['start_time']} - {meeting['end_time']}")

    # ========================================================================
    # STEP 2: Analyze Situation
    # ========================================================================
    print_section("STEP 2: Analyzing situation...")

    COMFORT_TEMP = 72.0
    COOLING_THRESHOLD = 75.0

    needs_cooling = status['indoor_temp'] > COOLING_THRESHOLD
    has_meetings = len(status['meeting_plan']) > 0

    print(f"Current: {status['indoor_temp']}°F")
    print(f"Threshold: {COOLING_THRESHOLD}°F")
    print(f"Needs cooling? {needs_cooling}")
    print(f"Has meetings? {has_meetings}")

    if not needs_cooling:
        print("\n✓ Temperature is comfortable. No action needed.")
        return

    if not has_meetings:
        print("\n→ No meetings scheduled. Energy-saving mode: No cooling.")
        return

    print(f"\n→ Decision: Cool to {COMFORT_TEMP}°F before meetings")

    # ========================================================================
    # STEP 3: Create Optimal Plan
    # ========================================================================
    print_section("STEP 3: Creating optimal cooling plan...")

    first_meeting = status['meeting_plan'][0]

    # Calculate time until meeting
    def parse_time(time_str):
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    current_minutes = parse_time(status['current_time'])
    meeting_minutes = parse_time(first_meeting['start_time'])
    time_until_meeting = meeting_minutes - current_minutes

    print(f"First meeting: {first_meeting['start_time']}")
    print(f"Time until meeting: {time_until_meeting} minutes")

    # Use turbo if less than 30 minutes available
    use_turbo = time_until_meeting < 30
    print(f"Strategy: {'TURBO mode (faster)' if use_turbo else 'BASE mode (economical)'}")

    # Create the plan
    plan = [{
        "time_on": status['current_time'],
        "time_off": first_meeting['start_time'],
        "use_turbo": use_turbo
    }]
    target_temps = [COMFORT_TEMP]

    print(f"\nPlan Details:")
    print(f"  Time: {plan[0]['time_on']} → {plan[0]['time_off']}")
    print(f"  Mode: {'Turbo (9000W)' if use_turbo else 'Base (7000W)'}")
    print(f"  Target: {COMFORT_TEMP}°F")

    # ========================================================================
    # STEP 4: Validate Plan
    # ========================================================================
    print_section("STEP 4: Validating plan with HVAC simulation...")

    feedback = get_feedback(
        current_indoor_temp=status['indoor_temp'],
        outdoor_temp=status['outdoor_temp'],
        current_time=status['current_time'],
        plan=plan,
        target_temps=target_temps,
        mode="cool"
    )

    print(f"Result: {feedback['plan_success'].upper()}")

    # ========================================================================
    # STEP 5: Execute or Adjust
    # ========================================================================
    print_section("STEP 5: Final decision...")

    if feedback['plan_success'] == 'success':
        action = feedback['action_results'][0]

        print("✓ PLAN IS FEASIBLE - READY TO EXECUTE!")
        print()
        print("Execution Details:")
        print(f"  • Turn on AC: {action['time_on']}")
        print(f"  • Mode: {'Turbo (9000W)' if use_turbo else 'Base (7000W)'}")
        print(f"  • Target reached: {action['reached_time']}")
        print(f"  • Turn off AC: {action['time_off']}")
        print()
        print("Performance Metrics:")
        print(f"  • Time needed: {action['time_needed_minutes']} min")
        print(f"  • Time available: {action['time_available_minutes']} min")
        print(f"  • Safety margin: {action['redundant_time_minutes']} min")
        print()
        print("Energy Cost:")
        print(f"  • This action: {action['cost_kwh']:.3f} kWh")
        print(f"  • Total cost: {feedback['total_cost_kwh']:.3f} kWh")
        print()
        print("Expected Outcome:")
        print(f"  • Final temp: {feedback['final_temp_f']:.1f}°F")
        print(f"  • Meeting comfort: ✓ Achieved")

    else:
        failed = feedback['failed_actions'][0]
        action = feedback['action_results'][0]

        print("✗ PLAN FAILED - ADJUSTMENTS NEEDED!")
        print()
        print(f"Problem:")
        print(f"  {failed['error']}")
        print()
        print("Analysis:")
        print(f"  • Time needed: {action['time_needed_minutes']} min")
        print(f"  • Time available: {action['time_available_minutes']} min")
        print(f"  • Shortfall: {action['time_needed_minutes'] - action['time_available_minutes']} min")
        print()
        print("Energy Cost (Partial Cooling):")
        print(f"  • This action: {action['cost_kwh']:.3f} kWh (HVAC ran for {action['time_available_minutes']} min)")
        print(f"  • Total cost: {feedback['total_cost_kwh']:.3f} kWh")
        print(f"  • Final temp: {feedback['final_temp_f']:.1f}°F (partial cooling achieved)")
        print()

        # Suggest alternatives
        print("💡 Suggestions:")
        if not use_turbo:
            print("  1. Switch to TURBO mode for faster cooling")
        else:
            print("  1. Set higher target temp (e.g., 74°F instead of 72°F)")
            print("  2. Start cooling earlier if possible")
        print("  3. Accept partial cooling within available time")

    print()
    print("=" * 80)


def test_multiple_scenarios():
    """
    Test different scenarios with different mocked inputs.
    """
    print_header("TESTING MULTIPLE SCENARIOS")

    scenarios = [
        {
            "name": "Scenario 1: Plenty of time (60 min)",
            "status": {
                "room_name": "Conference Room A",
                "current_time": "14:00",
                "indoor_temp": 86.0,
                "outdoor_temp": 95.0,
                "meeting_plan": [{"start_time": "15:00", "end_time": "16:00"}]
            }
        },
        {
            "name": "Scenario 2: Tight schedule (30 min)",
            "status": {
                "room_name": "Conference Room A",
                "current_time": "14:30",
                "indoor_temp": 86.0,
                "outdoor_temp": 95.0,
                "meeting_plan": [{"start_time": "15:00", "end_time": "16:00"}]
            }
        },
        {
            "name": "Scenario 3: Very tight schedule (15 min)",
            "status": {
                "room_name": "Conference Room A",
                "current_time": "14:45",
                "indoor_temp": 86.0,
                "outdoor_temp": 95.0,
                "meeting_plan": [{"start_time": "15:00", "end_time": "16:00"}]
            }
        }
    ]

    for scenario in scenarios:
        print_section(scenario["name"])

        status = scenario["status"]
        first_meeting = status["meeting_plan"][0]

        # Create plan
        plan = [{
            "time_on": status["current_time"],
            "time_off": first_meeting["start_time"],
            "use_turbo": True
        }]

        # Validate
        feedback = get_feedback(
            current_indoor_temp=status["indoor_temp"],
            outdoor_temp=status["outdoor_temp"],
            current_time=status["current_time"],
            plan=plan,
            target_temps=[72.0],
            mode="cool"
        )

        # Show results
        print(f"Time: {status['current_time']} → {first_meeting['start_time']}")
        print(f"Indoor: {status['indoor_temp']}°F → Target: 72°F")
        print(f"Result: {feedback['plan_success'].upper()}")

        action = feedback['action_results'][0]
        if feedback['plan_success'] == 'success':
            print(f"  ✓ Reaches 72°F at {action['reached_time']}")
            print(f"  ✓ Cost: {action['cost_kwh']:.3f} kWh")
        else:
            print(f"  ✗ {feedback['failed_actions'][0]['error']}")
            print(f"  ✗ Partial cooling cost: {action['cost_kwh']:.3f} kWh (HVAC ran for {action['time_available_minutes']} min)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    import sys

    # Check if user wants to run a specific scenario
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
        if scenario in ["success", "tight", "failed"]:
            ai_agent_decision(scenario)
        else:
            print("Usage: python agent_example.py [success|tight|failed]")
            print("  success - Plenty of time (60 min)")
            print("  tight   - Tight schedule (30 min)")
            print("  failed  - Impossible task (10 min)")
    else:
        # Run all demonstrations

        # Demo 1: Success scenario
        ai_agent_decision("success")

        # Demo 2: Failed scenario (to show cost even when failed)
        print("\n\n")
        ai_agent_decision("failed")

        # Demo 3: Multiple test scenarios
        print("\n\n")
        test_multiple_scenarios()
