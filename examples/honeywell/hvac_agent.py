#!/usr/bin/env python3
"""HVAC Control Agent - Simple flow without tools."""

import sys
import os
import json

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "dana_agent")
)

# Add environments directory to path for API access
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "environments")
)

from dana.core.agent.star_agent import STARAgent  # noqa: E402
from hvac_api import get_env_status, get_feedback  # noqa: E402


class HVACAgent(STARAgent):
    """HVAC Control Agent - Creates HVAC plans based on environment."""

    def __init__(self, **kwargs):
        # Set prompt path
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            "HVACAgent.xml"
        )

        super().__init__(
            agent_id="hvac-agent",
            llm_provider="openai",
            model="gpt-4o-mini",
            prompt_path=prompt_path,
            **kwargs
        )


def run_hvac_flow():
    """
    Run the complete HVAC control flow.

    Flow:
    1. Get environment status
    2. Agent creates HVAC plan (based on environment only)
    3. Validate plan with feedback
    """
    print("=" * 80)
    print("HVAC AGENT FLOW")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: Get Environment Status
    # ========================================================================
    print("STEP 1: Get Environment Status")
    print("-" * 80)

    env_status = get_env_status()

    print("Input: get_env_status()")
    print()
    print("Output:")
    print(f"  room_name:    {env_status['room_name']}")
    print(f"  current_time: {env_status['current_time']}")
    print(f"  indoor_temp:  {env_status['indoor_temp']}°F")
    print(f"  outdoor_temp: {env_status['outdoor_temp']}°F")
    print(f"  meetings:     {len(env_status['meeting_plan'])} scheduled")
    for i, meeting in enumerate(env_status['meeting_plan'], 1):
        print(f"    {i}. {meeting['start_time']} - {meeting['end_time']}")
    print()

    # ========================================================================
    # STEP 2: Agent Creates HVAC Plan
    # ========================================================================
    print("STEP 2: Agent Creates HVAC Plan")
    print("-" * 80)

    # Create prompt with ONLY environment data
    agent_prompt = f"""
CURRENT ENVIRONMENT:
- Current time: {env_status['current_time']}
- Indoor temperature: {env_status['indoor_temp']}°F
- Outdoor temperature: {env_status['outdoor_temp']}°F
- Meetings: {len(env_status['meeting_plan'])} scheduled
"""

    if env_status['meeting_plan']:
        agent_prompt += "\nUpcoming meetings:\n"
        for meeting in env_status['meeting_plan']:
            agent_prompt += f"  - {meeting['start_time']} to {meeting['end_time']}\n"

    print("Agent Input:")
    print(f"  Current time: {env_status['current_time']}")
    print(f"  Indoor temp:  {env_status['indoor_temp']}°F")
    print(f"  Outdoor temp: {env_status['outdoor_temp']}°F")
    print(f"  Meetings:     {len(env_status['meeting_plan'])} scheduled")
    print()

    # Call agent
    agent = HVACAgent()
    result = agent.query(caller_message=agent_prompt)

    if not result or "response" not in result:
        print("ERROR: Agent did not respond")
        return

    agent_response = result["response"]
    print("Agent Output:")
    print(agent_response)
    print()

    # Parse agent response
    try:
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', agent_response, re.DOTALL)
        if json_match:
            agent_plan = json.loads(json_match.group())
        else:
            agent_plan = json.loads(agent_response)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse agent response as JSON: {e}")
        return

    # ========================================================================
    # STEP 3: Validate Plan with Feedback
    # ========================================================================
    print("STEP 3: Validate Plan with Feedback")
    print("-" * 80)

    print("Feedback Input:")
    print(f"  current_indoor_temp: {env_status['indoor_temp']}°F")
    print(f"  outdoor_temp:        {env_status['outdoor_temp']}°F")
    print(f"  current_time:        {env_status['current_time']}")
    print(f"  plan:                {agent_plan['plan']}")
    print(f"  target_temps:        {agent_plan['target_temps']}")
    print(f"  mode:                {agent_plan['mode']}")
    print()

    feedback = get_feedback(
        current_indoor_temp=env_status['indoor_temp'],
        outdoor_temp=env_status['outdoor_temp'],
        current_time=env_status['current_time'],
        plan=agent_plan['plan'],
        target_temps=agent_plan['target_temps'],
        mode=agent_plan['mode']
    )

    print("Feedback Output:")
    print(f"  plan_success:    {feedback['plan_success']}")
    print(f"  total_cost_kwh:  {feedback['total_cost_kwh']:.3f} kWh")
    print(f"  final_temp_f:    {feedback['final_temp_f']:.1f}°F")
    print()

    if feedback['action_results']:
        action = feedback['action_results'][0]
        print("  action_results[0]:")
        print(f"    time_needed_minutes:     {action['time_needed_minutes']} min")
        print(f"    time_available_minutes:  {action['time_available_minutes']} min")
        print(f"    reached_time:            {action['reached_time']}")
        print(f"    cost_kwh:                {action['cost_kwh']:.3f} kWh")
    print()

    # ========================================================================
    # FINAL RESULT
    # ========================================================================
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    if feedback['plan_success'] == 'success':
        action = feedback['action_results'][0]
        action_verb = "Cools" if agent_plan['mode'] == "cool" else "Heats"
        print(f"✓ Plan is valid!")
        print(f"  • {action_verb} from {env_status['indoor_temp']}°F to {agent_plan['target_temps'][0]}°F")
        print(f"  • Takes {action['time_needed_minutes']} min (have {action['time_available_minutes']} min)")
        print(f"  • Reaches target at {action['reached_time']}")
        print(f"  • Costs {action['cost_kwh']:.3f} kWh")
        print(f"  • Reasoning: {agent_plan.get('reasoning', 'N/A')}")
    else:
        print(f"✗ Plan failed!")
        if feedback['failed_actions']:
            print(f"  • {feedback['failed_actions'][0]['error']}")
        if feedback['action_results']:
            action = feedback['action_results'][0]
            print(f"  • Cost (partial): {action['cost_kwh']:.3f} kWh")
        print(f"  • Final temp: {feedback['final_temp_f']:.1f}°F")

    print()
    print("=" * 80)


if __name__ == "__main__":
    run_hvac_flow()
