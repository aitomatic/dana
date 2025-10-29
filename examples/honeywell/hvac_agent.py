#!/usr/bin/env python3
"""HVAC Control Agent - Simple flow without tools."""

import sys
import os
import json
import re

# Try to import colorama for better cross-platform color support
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

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
            model="gpt-4.1",
            prompt_path=prompt_path,
            **kwargs
        )


class LearningAgent(STARAgent):
    """Learning Agent - Learns from the HVAC Agent's experience."""

    def __init__(self, **kwargs):
        # Set prompt path
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            "LearningAgent.xml"
        )

        super().__init__(
            agent_id="learning-agent",
            llm_provider="openai",
            model="gpt-4.1",
            prompt_path=prompt_path,
            **kwargs
        )

def generate_feedback_summary(feedback, env_status, agent_plan):
    """
    Generate a comprehensive feedback summary string for agent learning.

    Args:
        feedback: The feedback dictionary from get_feedback()
        env_status: The environment status dictionary
        agent_plan: The agent's plan dictionary

    Returns:
        str: A formatted string containing all feedback information
    """
    summary_parts = []

    # Basic feedback info
    summary_parts.append("FEEDBACK SUMMARY:")
    summary_parts.append(f"  Plan Success: {feedback['plan_success']}")
    summary_parts.append(f"  Total Cost: {feedback['total_cost_kwh']:.3f} kWh")
    final_temp = feedback['final_temp_f']
    summary_parts.append(f"  Final Temperature: {final_temp:.1f}°F")
    summary_parts.append("")

    # Action breakdown
    if feedback['action_results']:
        num_actions = len(feedback['action_results'])
        summary_parts.append(f"ACTION BREAKDOWN ({num_actions} actions):")
        total_cost_check = 0.0

        for i, action in enumerate(feedback['action_results']):
            summary_parts.append(f"  Action {i}:")
            time_range = f"{action['time_on']} → {action['time_off']}"
            summary_parts.append(f"    Time: {time_range}")
            start_temp = action['start_temp_f']
            target_temp = action['target_temp_f']
            temp_range = f"{start_temp:.1f}°F → {target_temp:.1f}°F"
            summary_parts.append(f"    Temperature: {temp_range}")
            # Color code the status
            status = action['schedule_success']
            if COLORAMA_AVAILABLE:
                if status == 'success':
                    status_colored = f"{Fore.GREEN}{status}{Style.RESET_ALL}"
                else:
                    status_colored = f"{Fore.RED}{status}{Style.RESET_ALL}"
            else:
                if status == 'success':
                    status_colored = f"\033[92m{status}\033[0m"  # Green
                else:
                    status_colored = f"\033[91m{status}\033[0m"  # Red
            summary_parts.append(f"    Status: {status_colored}")

            if action['time_needed_minutes'] is not None:
                time_needed = action['time_needed_minutes']
                summary_parts.append(f"    Time Needed: {time_needed} min")
            if action['time_available_minutes'] is not None:
                time_available = action['time_available_minutes']
                summary_parts.append(f"    Time Available: "
                                     f"{time_available} min")
            if action['reached_time']:
                reached_time = action['reached_time']
                summary_parts.append(f"    Reached Time: {reached_time}")
                
                # Add meeting context and wasted energy calculation
                if 'meeting_start_time' in action:
                    meeting_start = action['meeting_start_time']
                    summary_parts.append(f"    Meeting Starts: {meeting_start}")
                    
                    # Parse times to calculate difference
                    from datetime import datetime
                    try:
                        reached_dt = datetime.strptime(reached_time, "%H:%M")
                        meeting_dt = datetime.strptime(meeting_start, "%H:%M")
                        time_diff_minutes = (meeting_dt - reached_dt).total_seconds() / 60
                        
                        if time_diff_minutes > 0:
                            # Target reached before meeting
                            if time_diff_minutes > 5:
                                summary_parts.append(
                                    f"    ⚠️  Wasted energy time: {time_diff_minutes:.1f} min "
                                    f"(reached {time_diff_minutes:.1f} min before meeting)")
                            else:
                                summary_parts.append(
                                    f"    ✓ Reached {time_diff_minutes:.1f} min before meeting "
                                    f"(good timing)")
                        else:
                            # Target reached after meeting started
                            summary_parts.append(
                                f"    ❌ Target reached {abs(time_diff_minutes):.1f} min "
                                f"AFTER meeting started!")
                    except ValueError:
                        # If time parsing fails, skip the calculation
                        pass

            summary_parts.append(f"    Cost: {action['cost_kwh']:.3f} kWh")

            if action['error']:
                summary_parts.append(f"    Error: {action['error']}")

            total_cost_check += action['cost_kwh']
            summary_parts.append("")

        # Cost verification
        summary_parts.append("COST VERIFICATION:")
        summary_parts.append(f"  Sum of Action Costs: "
                             f"{total_cost_check:.3f} kWh")
        reported_total = feedback['total_cost_kwh']
        summary_parts.append(f"  Reported Total: {reported_total:.3f} kWh")

        cost_diff = abs(total_cost_check - reported_total)
        if cost_diff > 0.001:
            summary_parts.append(f"  ⚠️  MISMATCH: Difference of "
                                 f"{cost_diff:.3f} kWh")
        else:
            summary_parts.append("  ✓ Match!")
        summary_parts.append("")

    # Final result summary
    summary_parts.append("FINAL RESULT:")
    if feedback['plan_success'] == 'success':
        action_verb = "Cools" if agent_plan['mode'] == "cool" else "Heats"
        target_temps = agent_plan['target_temps']
        if isinstance(target_temps, (int, float)):
            target_temp = target_temps
        else:
            target_temp = target_temps[0]
        if COLORAMA_AVAILABLE:
            summary_parts.append(f"  {Fore.GREEN}✓ Plan is valid!{Style.RESET_ALL}")
        else:
            summary_parts.append("  \033[92m✓ Plan is valid!\033[0m")
        indoor_temp = env_status['indoor_temp']
        summary_parts.append(f"  • {action_verb} from {indoor_temp}°F "
                             f"to {target_temp}°F")
        total_cost = feedback['total_cost_kwh']
        summary_parts.append(f"  • Total cost: {total_cost:.3f} kWh")
        final_temp = feedback['final_temp_f']
        summary_parts.append(f"  • Final temp: {final_temp:.1f}°F")
        summary_parts.append("")
        summary_parts.append("  Action Summary:")
        for i, action in enumerate(feedback['action_results']):
            if action['schedule_success'] == 'success':
                time_range = f"{action['time_on']} → {action['time_off']}"
                reached_time = action['reached_time']
                cost = action['cost_kwh']
                target_temp = action['target_temp_f']
                
                # Calculate meeting timing and wasted energy for action summary
                meeting_timing_info = ""
                if 'meeting_start_time' in action:
                    meeting_start = action['meeting_start_time']
                    from datetime import datetime
                    try:
                        reached_dt = datetime.strptime(reached_time, "%H:%M")
                        meeting_dt = datetime.strptime(meeting_start, "%H:%M")
                        time_diff_minutes = (meeting_dt - reached_dt).total_seconds() / 60
                        
                        if time_diff_minutes > 0:
                            if time_diff_minutes > 5:
                                meeting_timing_info = (f" (meeting at {meeting_start}, "
                                                      f"wasted: {time_diff_minutes:.1f} min)")
                            else:
                                meeting_timing_info = (f" (meeting at {meeting_start}, "
                                                      f"good timing: {time_diff_minutes:.1f} min early)")
                        else:
                            meeting_timing_info = (f" (meeting at {meeting_start}, LATE: "
                                                  f"{abs(time_diff_minutes):.1f} min after meeting started!)")
                    except ValueError:
                        pass
                
                if COLORAMA_AVAILABLE:
                    summary_parts.append(
                        f"    {i+1}. {time_range}: {Fore.GREEN}✓ Reaches{Style.RESET_ALL} "
                        f"{target_temp:.0f}°F at {reached_time} "
                        f"(cost: {cost:.3f} kWh){meeting_timing_info}")
                else:
                    summary_parts.append(
                        f"    {i+1}. {time_range}: \033[92m✓ Reaches\033[0m "
                        f"{target_temp:.0f}°F at {reached_time} "
                        f"(cost: {cost:.3f} kWh){meeting_timing_info}")
            else:
                time_range = f"{action['time_on']} → {action['time_off']}"
                error = action['error']
                if COLORAMA_AVAILABLE:
                    summary_parts.append(
                        f"    {i+1}. {time_range}: {Fore.RED}✗ Failed{Style.RESET_ALL}: "
                        f"{error}")
                else:
                    summary_parts.append(
                        f"    {i+1}. {time_range}: \033[91m✗ Failed\033[0m: "
                        f"{error}")
    else:
        if COLORAMA_AVAILABLE:
            summary_parts.append(f"  {Fore.RED}✗ Plan failed!{Style.RESET_ALL}")
        else:
            summary_parts.append("  \033[91m✗ Plan failed!\033[0m")
        total_cost = feedback['total_cost_kwh']
        summary_parts.append(f"  • Total cost: {total_cost:.3f} kWh")
        final_temp = feedback['final_temp_f']
        summary_parts.append(f"  • Final temp: {final_temp:.1f}°F")
        summary_parts.append("")
        failed_count = len(feedback['failed_actions'])
        summary_parts.append(f"  Failed actions ({failed_count}):")
        for failed in feedback['failed_actions']:
            action_idx = failed['action_index']
            time_range = f"{failed['time_on']} → {failed['time_off']}"
            summary_parts.append(f"    • Action {action_idx}: {time_range}")
            summary_parts.append(f"      {failed['error']}")
        summary_parts.append("")
        summary_parts.append("  Action Summary:")
        for i, action in enumerate(feedback['action_results']):
            time_range = f"{action['time_on']} → {action['time_off']}"
            if action['schedule_success'] == 'success':
                target_temp = action['target_temp_f']
                cost = action['cost_kwh']
                
                # Calculate meeting timing and wasted energy for action summary
                meeting_timing_info = ""
                if 'meeting_start_time' in action and action['reached_time']:
                    meeting_start = action['meeting_start_time']
                    from datetime import datetime
                    try:
                        reached_dt = datetime.strptime(action['reached_time'], "%H:%M")
                        meeting_dt = datetime.strptime(meeting_start, "%H:%M")
                        time_diff_minutes = (meeting_dt - reached_dt).total_seconds() / 60
                        
                        if time_diff_minutes > 0:
                            if time_diff_minutes > 5:
                                meeting_timing_info = (f" (meeting at {meeting_start}, "
                                                      f"wasted: {time_diff_minutes:.1f} min)")
                            else:
                                meeting_timing_info = (f" (meeting at {meeting_start}, "
                                                      f"good timing: {time_diff_minutes:.1f} min early)")
                        else:
                            meeting_timing_info = (f" (meeting at {meeting_start}, LATE: "
                                                  f"{abs(time_diff_minutes):.1f} min after meeting started!)")
                    except ValueError:
                        pass
                
                if COLORAMA_AVAILABLE:
                    summary_parts.append(
                        f"    {Fore.GREEN}✓{Style.RESET_ALL} {i+1}. {time_range}: "
                        f"Reaches {target_temp:.0f}°F "
                        f"(cost: {cost:.3f} kWh){meeting_timing_info}")
                else:
                    summary_parts.append(
                        f"    \033[92m✓\033[0m {i+1}. {time_range}: "
                        f"Reaches {target_temp:.0f}°F "
                        f"(cost: {cost:.3f} kWh){meeting_timing_info}")
            else:
                cost = action['cost_kwh']
                if COLORAMA_AVAILABLE:
                    summary_parts.append(
                        f"    {Fore.RED}✗{Style.RESET_ALL} {i+1}. {time_range}: "
                        f"Failed (cost: {cost:.3f} kWh)")
                else:
                    summary_parts.append(
                        f"    \033[91m✗\033[0m {i+1}. {time_range}: "
                        f"Failed (cost: {cost:.3f} kWh)")

    return "\n".join(summary_parts)


def extract_policies_from_learning_analysis(learning_insights):
    """
    Extract policies from learning agent analysis.
    
    Args:
        learning_insights: The learning agent's response text
        
    Returns:
        list: List of extracted policies
    """
    # Look for policies in the format <policy>...</policy>
    policy_pattern = r'<policy>(.*?)</policy>'
    policies = re.findall(policy_pattern, learning_insights, re.DOTALL)
    
    # Clean up the policies (remove extra whitespace and XML tags)
    cleaned_policies = []
    for policy in policies:
        # Remove any remaining XML tags and clean up whitespace
        cleaned_policy = re.sub(r'<[^>]+>', '', policy).strip()
        # Remove any stray > characters that might be left
        cleaned_policy = cleaned_policy.replace('>', '').strip()
        if cleaned_policy:
            cleaned_policies.append(cleaned_policy)
    
    return cleaned_policies


def update_hvac_agent_prompt_with_policies(policies):
    """
    Update the HVACAgent.xml file with extracted policies.
    
    Args:
        policies: List of policies to add to the prompt
    """
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "prompts",
        "HVACAgent.xml"
    )
    
    # Read the current prompt file
    with open(prompt_path, 'r') as f:
        content = f.read()
    
    # Find the IDENTITY section
    identity_start = content.find('<IDENTITY>')
    if identity_start == -1:
        print("Warning: Could not find IDENTITY section in HVACAgent.xml")
        return
    
    identity_end = content.find('</IDENTITY>')
    if identity_end == -1:
        print("Warning: Could not find end of IDENTITY section in HVACAgent.xml")
        return
    
    # Get the content before and after IDENTITY
    before_identity = content[:identity_start]
    after_identity = content[identity_end + len('</IDENTITY>'):]
    
    # Extract the original IDENTITY content (without the tags)
    identity_content = content[identity_start + len('<IDENTITY>'):identity_end].strip()
    
    # Extract existing policies if they exist
    existing_policies = []
    if "YOU MUST FOLLOW THESE RULES:" in identity_content:
        # Find the start and end of the policies section
        policies_start = identity_content.find("YOU MUST FOLLOW THESE RULES:")
        # Find the end by looking for the next empty line or end of content
        lines = identity_content[policies_start:].split('\n')
        policies_end = policies_start
        for i, line in enumerate(lines):
            if i > 0 and line.strip() == "":
                policies_end = policies_start + len('\n'.join(lines[:i+1]))
                break
        
        # Extract existing policies
        policies_section = identity_content[policies_start:policies_end]
        for line in policies_section.split('\n'):
            if line.strip().startswith('- '):
                existing_policies.append(line.strip()[2:])  # Remove the '- ' prefix
        
        # Remove the existing policies section from identity_content
        identity_content = identity_content[:policies_start] + identity_content[policies_end:]
    
    # Create the new IDENTITY content with policies
    all_policies = existing_policies + policies
    if all_policies:
        policies_section = "YOU MUST FOLLOW THESE RULES:\n"
        for policy in all_policies:
            policies_section += f"- {policy}\n"
        policies_section += "\n"
        new_identity_content = f"<IDENTITY>\n{policies_section}{identity_content}\n</IDENTITY>"
    else:
        new_identity_content = f"<IDENTITY>\n{identity_content}\n</IDENTITY>"
    
    # Reconstruct the entire file
    new_content = before_identity + new_identity_content + after_identity
    
    # Write the updated content back to the file
    with open(prompt_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated HVACAgent.xml with {len(policies)} policies")


def analyze_feedback_with_learning_agent(feedback, env_status, agent_plan):
    """
    Analyze HVAC feedback using the Learning Agent to generate optimization insights.

    Args:
        feedback: The feedback dictionary from get_feedback()
        env_status: The environment status dictionary
        agent_plan: The agent's plan dictionary

    Returns:
        dict: Learning agent insights and recommendations
    """
    # Generate feedback summary
    feedback_summary = generate_feedback_summary(
        feedback, env_status, agent_plan
    )

    # Create learning agent
    learning_agent = LearningAgent()

    # Create learning prompt with feedback summary and objectives
    learning_prompt = f"""
FEEDBACK DATA:
{feedback_summary}

ENVIRONMENTAL CONTEXT:
- Room: {env_status['room_name']}
- Current Time: {env_status['current_time']}
- Indoor Temperature: {env_status['indoor_temp']}°F
- Outdoor Temperature: {env_status['outdoor_temp']}°F
- Meeting Schedule: {len(env_status['meeting_plan'])} meetings planned

OBJECTIVES:
1. Ensure target temperature is reached before meeting starts and maintained during meeting
2. Optimize for cost by minimizing electricity consumption
"""

    # Call learning agent
    learning_result = learning_agent.query(caller_message=learning_prompt)

    if not learning_result or "response" not in learning_result:
        return {"error": "Learning Agent did not respond"}

    learning_insights = learning_result["response"]

    # Return the unstructured response directly
    return {
        "success": True,
        "insights": learning_insights,
        "raw_response": learning_insights
    }


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
#     env_status = {
#   "room_name": "Conference Room A",
#   "current_time": "18:23",
#   "indoor_temp": 59.4,
#   "outdoor_temp": 58.3,
#   "meeting_plan": [
#     {
#       "start_time": "20:31",
#       "end_time": "21:21"
#     }
#   ]
# }
    env_status = {
  "room_name": "Conference Room A",
  "current_time": "13:26",
  "indoor_temp": 93.3,
  "outdoor_temp": 92.4,
  "meeting_plan": [
    {
      "start_time": "15:37",
      "end_time": "17:27"
    },
    {
      "start_time": "18:22",
      "end_time": "18:52"
    },
    {
      "start_time": "21:45",
      "end_time": "22:00"
    }
  ]
}

    print("Input: get_env_status()")
    print()
    print("Output:")
    print(f"  room_name:    {env_status['room_name']}")
    print(f"  current_time: {env_status['current_time']}")
    print(f"  indoor_temp:  {env_status['indoor_temp']}°F")
    print(f"  outdoor_temp: {env_status['outdoor_temp']}°F")
    meeting_count = len(env_status['meeting_plan'])
    print(f"  meetings:     {meeting_count} scheduled")
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
{json.dumps(env_status, indent=2)}
"""

    if env_status['meeting_plan']:
        agent_prompt += "\nUpcoming meetings:\n"
        for meeting in env_status['meeting_plan']:
            start_time = meeting['start_time']
            end_time = meeting['end_time']
            agent_prompt += f"  - {start_time} to {end_time}\n"

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
    print(agent_prompt)
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
        mode=agent_plan['mode'],
        meeting_plan=env_status['meeting_plan']
    )

    # Generate comprehensive feedback summary for agent learning
    feedback_summary = generate_feedback_summary(
        feedback, env_status, agent_plan
    )

    # Print the feedback summary
    print("Feedback Output:")
    print(feedback_summary)
    print()
    print("=" * 80)
    
    # Force flush to ensure colors are displayed
    sys.stdout.flush()

    # ========================================================================
    # STEP 4: Learning Agent Analysis
    # ========================================================================
    print("STEP 4: Learning Agent Analysis")
    print("-" * 80)

    print("Learning Agent Input:")
    print(f"  Analyzing feedback from {env_status['room_name']}")
    print(f"  Plan success: {feedback['plan_success']}")
    print(f"  Total cost: {feedback['total_cost_kwh']:.3f} kWh")
    print(f"  Final temperature: {feedback['final_temp_f']:.1f}°F")
    print()

    # Analyze feedback with learning agent
    learning_analysis = analyze_feedback_with_learning_agent(
        feedback, env_status, agent_plan
    )

    if "error" in learning_analysis:
        print(f"ERROR: {learning_analysis['error']}")
        return

    if learning_analysis["success"]:
        print("Learning Agent Output:")
        print(learning_analysis["insights"])
        print()
        
        # Extract policies from learning analysis
        policies = extract_policies_from_learning_analysis(learning_analysis["insights"])
        
        if policies:
            print(f"Extracted {len(policies)} policies:")
            for i, policy in enumerate(policies, 1):
                print(f"  {i}. {policy}")
            print()
            
            # Update HVACAgent.xml with extracted policies
            update_hvac_agent_prompt_with_policies(policies)
        else:
            print("No policies found in learning analysis")
            print()
    else:
        print("Learning Agent Output (Raw):")
        print(learning_analysis["raw_response"])
        print()
    
    print("=" * 80)


def test_policy_extraction():
    """Test function to verify policy extraction and XML update works correctly."""
    print("Testing policy extraction and XML update...")
    
    # Sample learning insights with policies
    test_insights = """
    Based on the feedback analysis, here are the key insights:
    
    <policy>When indoor temperature exceeds ~78°F with outdoor temps near or above indoor, start pre-cooling no more than 10 minutes before the meeting starts to avoid waste of energy.</policy>
    
    <policy>When the indoor temperature is less than 50°F, start pre-cooling no less than 15 minutes before the meeting starts and use turbo mode.</policy>
    
    These policies should help optimize HVAC performance.
    """
    
    # Test policy extraction
    policies = extract_policies_from_learning_analysis(test_insights)
    print(f"Extracted {len(policies)} policies:")
    for i, policy in enumerate(policies, 1):
        print(f"  {i}. {policy}")
    
    # Test XML update
    if policies:
        print("\nUpdating HVACAgent.xml...")
        update_hvac_agent_prompt_with_policies(policies)
        
        # Read and display the updated file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            "HVACAgent.xml"
        )
        
        print("\nUpdated HVACAgent.xml content:")
        print("-" * 50)
        with open(prompt_path, 'r') as f:
            content = f.read()
            print(content)
        print("-" * 50)
    else:
        print("No policies found in test data")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_policy_extraction()
    else:
        run_hvac_flow()
