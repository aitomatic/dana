# HVAC Control Agent

AI agent that creates HVAC control plans based ONLY on environment status.

## Flow

```
Input: Environment Status Only
    ↓
Agent: Figures out plan on its own
    ↓
Feedback: Validates the plan
```

## Key Feature

**Agent receives ONLY environment data - no rules, no instructions, no user request.**

The agent must figure out:
- Should it cool or heat?
- When to start/stop?
- Use turbo or base mode?
- What target temperature?

## Usage

```bash
python hvac_agent.py
```

## Example Output

```
STEP 1: Get Environment Status
--------------------------------------------------------------------------------
Input: get_env_status()

Output:
  room_name:    Conference Room A
  current_time: 14:00
  indoor_temp:  86.0°F
  outdoor_temp: 95.0°F
  meetings:     2 scheduled
    1. 15:00 - 16:30
    2. 17:00 - 18:00

STEP 2: Agent Creates HVAC Plan
--------------------------------------------------------------------------------
Agent Input:
  Current time: 14:00
  Indoor temp:  86.0°F
  Outdoor temp: 95.0°F
  Meetings:     2 scheduled

Agent Output:
{
  "plan": [{"time_on": "14:00", "time_off": "15:00", "use_turbo": false}],
  "target_temps": [72.0],
  "mode": "cool",
  "reasoning": "Room is hot (86°F), cool to 72°F before meeting at 15:00"
}

STEP 3: Validate Plan with Feedback
--------------------------------------------------------------------------------
Feedback Input:
  current_indoor_temp: 86.0°F
  outdoor_temp:        95.0°F
  current_time:        14:00
  plan:                [{'time_on': '14:00', 'time_off': '15:00', 'use_turbo': False}]
  target_temps:        [72.0]
  mode:                cool

Feedback Output:
  plan_success:    success
  total_cost_kwh:  7.000 kWh
  final_temp_f:    72.0°F
  time_needed:     25 min
  time_available:  60 min

FINAL RESULT
================================================================================
✓ Plan is valid!
  • Cools from 86.0°F to 72.0°F
  • Takes 25 min (have 60 min)
  • Costs 7.000 kWh
  • Reasoning: Room is hot (86°F), cool to 72°F before meeting at 15:00
```

## What Makes This Different

**Traditional approach:**
- Agent has built-in rules
- Knows when to use turbo
- Told what target temp should be
- Given explicit instructions

**This approach:**
- Agent receives ONLY: time, temps, meetings
- Figures out everything itself
- No built-in knowledge
- Pure reasoning from environment

## Files

| File | Purpose |
|------|---------|
| `hvac_agent.py` | Main flow (3 steps) |
| `prompts/HVACAgent.xml` | Minimal identity (no knowledge) |
| `environments/hvac_api.py` | API functions |

## Agent Prompt

**Identity:** Minimal (no decision rules)
```xml
<IDENTITY>
I create HVAC control plans based on current environment conditions.
I analyze the environment and output a plan in JSON format.
</IDENTITY>
```

**Input:** Environment status only
```
- Current time: 14:00
- Indoor temperature: 86.0°F
- Outdoor temperature: 95.0°F
- Meetings: 2 scheduled
```

**Output:** Agent decides everything
```json
{
  "plan": [...],
  "target_temps": [72.0],
  "mode": "cool",
  "reasoning": "..."
}
```

---

**Pure environment-driven decision making** 🧠
