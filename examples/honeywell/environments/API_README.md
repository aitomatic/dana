# HVAC API Documentation

Simple API for AI agents to control and monitor HVAC systems.

## Overview

This API provides two main functions:
1. **`get_env_status()`** - Get current environment state (temperature, time, meetings)
2. **`get_feedback()`** - Validate HVAC action plans and get detailed feedback

## Installation

```python
from hvac_api import get_env_status, get_feedback
```

## API Functions

### 1. `get_env_status(room_name="Conference Room A")`

Get current environment status including temperature and meeting schedule.

**Parameters:**
- `room_name` (str, optional): Name of the room (default: "Conference Room A")

**Returns:**
```python
{
    "room_name": str,           # Name of the room
    "current_time": str,        # Current time "HH:MM"
    "indoor_temp": float,       # Indoor temperature (°F)
    "outdoor_temp": float,      # Outdoor temperature (°F)
    "meeting_plan": [           # List of scheduled meetings
        {
            "start_time": str,  # Meeting start "HH:MM"
            "end_time": str     # Meeting end "HH:MM"
        },
        ...
    ]
}
```

**Example:**
```python
from hvac_api import get_env_status

# Get current environment status
status = get_env_status()

print(f"Current time: {status['current_time']}")
print(f"Indoor temp: {status['indoor_temp']}°F")
print(f"Outdoor temp: {status['outdoor_temp']}°F")
print(f"Meetings today: {len(status['meeting_plan'])}")

for meeting in status['meeting_plan']:
    print(f"  Meeting: {meeting['start_time']} - {meeting['end_time']}")
```

---

### 2. `get_feedback(current_indoor_temp, outdoor_temp, current_time, plan, target_temps, mode="cool")`

Validate an HVAC action plan and get detailed feedback on feasibility and cost.

**Parameters:**
- `current_indoor_temp` (float): Current indoor temperature in °F
- `outdoor_temp` (float): Outdoor temperature in °F
- `current_time` (str): Current time in "HH:MM" format
- `plan` (list[dict]): List of HVAC actions, each dict with:
  - `time_on` (str): When to turn on HVAC "HH:MM"
  - `time_off` (str): When to turn off HVAC "HH:MM"
  - `use_turbo` (bool): Whether to use turbo mode
- `target_temps` (list[float]): Target temperatures (°F) for each action
- `mode` (str, optional): "cool" or "heat" (default: "cool")

**Returns:**
```python
{
    "plan_success": str,        # "success" or "failed"
    "total_cost_kwh": float,    # Total electricity (kWh)
    "final_temp_f": float,      # Final temperature (°F)
    "action_results": [         # Details for each action
        {
            "action_index": int,
            "time_on": str,
            "time_off": str,
            "target_temp_f": float,
            "start_temp_f": float,
            "schedule_success": str,      # "success" or "failed"
            "time_needed_minutes": int,
            "time_available_minutes": int,
            "reached_time": str,          # "HH:MM"
            "redundant_time_minutes": int,
            "cost_kwh": float,
            "error": str or None
        },
        ...
    ],
    "failed_actions": [         # List of failed actions
        {
            "action_index": int,
            "time_on": str,
            "time_off": str,
            "target_temp_f": float,
            "error": str
        },
        ...
    ]
}
```

**Example:**
```python
from hvac_api import get_env_status, get_feedback

# Step 1: Get current environment
status = get_env_status()

# Step 2: Create a cooling plan before meetings
plan = [
    # Cool to 72°F before first meeting (with turbo)
    {
        "time_on": status["current_time"],
        "time_off": status["meeting_plan"][0]["start_time"],
        "use_turbo": True
    },
    # Maintain 72°F during meeting (no turbo)
    {
        "time_on": status["meeting_plan"][0]["start_time"],
        "time_off": status["meeting_plan"][0]["end_time"],
        "use_turbo": False
    }
]

target_temps = [72.0, 72.0]  # Target 72°F for both actions

# Step 3: Get feedback on the plan
feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=plan,
    target_temps=target_temps,
    mode="cool"
)

# Step 4: Check if plan is feasible
if feedback["plan_success"] == "success":
    print(f"✓ Plan works!")
    print(f"  Total cost: {feedback['total_cost_kwh']:.2f} kWh")
    print(f"  Final temp: {feedback['final_temp_f']:.1f}°F")

    for action in feedback["action_results"]:
        print(f"\n  Action {action['action_index']}:")
        print(f"    {action['time_on']} → {action['time_off']}")
        print(f"    Target: {action['target_temp_f']}°F")
        print(f"    Reaches target at: {action['reached_time']}")
        print(f"    Cost: {action['cost_kwh']:.2f} kWh")
else:
    print(f"✗ Plan failed!")
    for failed in feedback["failed_actions"]:
        print(f"  Action {failed['action_index']}: {failed['error']}")
```

---

## Complete Usage Example

Here's a complete workflow for an AI agent:

```python
from hvac_api import get_env_status, get_feedback

# 1. Get current environment status
status = get_env_status()
print(f"Time: {status['current_time']}")
print(f"Indoor: {status['indoor_temp']}°F, Outdoor: {status['outdoor_temp']}°F")
print(f"Meetings: {len(status['meeting_plan'])}")

# 2. Check if we need to cool
if status["indoor_temp"] > 75 and status["meeting_plan"]:
    first_meeting = status["meeting_plan"][0]

    # 3. Create a simple cooling plan
    plan = [{
        "time_on": status["current_time"],
        "time_off": first_meeting["start_time"],
        "use_turbo": True
    }]
    target_temps = [72.0]

    # 4. Validate the plan
    feedback = get_feedback(
        current_indoor_temp=status["indoor_temp"],
        outdoor_temp=status["outdoor_temp"],
        current_time=status["current_time"],
        plan=plan,
        target_temps=target_temps
    )

    # 5. Make decision based on feedback
    if feedback["plan_success"] == "success":
        action = feedback["action_results"][0]
        print(f"\n✓ Execute plan:")
        print(f"  Turn on AC (turbo) at {action['time_on']}")
        print(f"  Will reach 72°F at {action['reached_time']}")
        print(f"  Cost: {action['cost_kwh']:.2f} kWh")
    else:
        print(f"\n✗ Plan won't work in time")
        print(f"  Need: {feedback['action_results'][0]['time_needed_minutes']} min")
        print(f"  Have: {feedback['action_results'][0]['time_available_minutes']} min")
else:
    print("\nNo action needed - temperature is comfortable")
```

---

## HVAC System Specifications

### Cooling/Heating Capacity
- **Base Mode**: 7,000W (~24,000 BTU/hr) - typical 2-ton residential AC
- **Turbo Mode**: 9,000W (~30,000 BTU/hr) - 29% power boost
- **Turbo Duration**: Maximum 30 minutes, then switches to base mode

### Realistic Performance
- **Small changes (2-3°F)**: 2-6 minutes
- **Medium changes (5-8°F)**: 8-14 minutes
- **Large changes (10-16°F)**: 20-29 minutes
- **Turbo speedup**: ~1.3x faster than base mode

### Physical Parameters
- **Building insulation**: UA = 85 W/K (well-insulated)
- **Thermal mass**: C = 1.2×10⁶ J/K (typical residential)
- **Internal heat**: Q_int = 100W (lights, equipment)
- **Temperature limits**: Minimum 60°F (safety limit)

### Cooling Physics
The system uses first-order thermal dynamics:
```
T(t) = T_inf + (T₀ - T_inf) × e^(-t/τ)
```

Where:
- `T_inf` = Equilibrium temperature with HVAC on
- `τ` = Time constant (depends on insulation and thermal mass)
- Time is **non-linear** - takes progressively longer as you approach equilibrium

---

## Tips for AI Agents

### 1. Plan Ahead
- Start cooling **before** meetings, not during
- Use `time_needed_minutes` from feedback to know how early to start

### 2. Use Turbo Wisely
- Turbo is ~30% faster but uses more energy
- Best for: urgent cooling before imminent meetings
- Skip for: long cooling periods with plenty of time

### 3. Handle Gaps
- Temperature **drifts** toward outdoor temp when HVAC is off
- Account for drift when planning multiple actions with gaps

### 4. Check Feasibility First
- Always call `get_feedback()` before executing
- Check `plan_success` and `failed_actions` to avoid impossible plans

### 5. Optimize for Cost
- If `redundant_time_minutes` is high, consider:
  - Starting later
  - Using base mode instead of turbo
  - Setting a slightly higher target temp

---

## Error Handling

### Common Errors

1. **"Need X min, only Y min available"**
   - Not enough time to reach target
   - Solution: Start earlier or use turbo mode

2. **"Target below 60°F minimum"**
   - Safety limit violation
   - Solution: Set target ≥ 60°F

3. **"Plan has X actions but Y target temperatures"**
   - Mismatch between plan length and targets
   - Solution: Ensure `len(plan) == len(target_temps)`

4. **"Invalid mode 'X'"**
   - Mode must be "cool" or "heat"
   - Solution: Use mode="cool" for cooling

---

## Quick Reference

```python
# Import
from hvac_api import get_env_status, get_feedback

# Get status
status = get_env_status()
# Returns: {room_name, current_time, indoor_temp, outdoor_temp, meeting_plan}

# Validate plan
feedback = get_feedback(
    current_indoor_temp=86.0,
    outdoor_temp=95.0,
    current_time="14:00",
    plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}],
    target_temps=[72.0],
    mode="cool"
)
# Returns: {plan_success, total_cost_kwh, final_temp_f, action_results, failed_actions}
```

---

## Testing

Run the demo:
```bash
python hvac_api.py
```

This will:
1. Get current environment status
2. Create a sample cooling plan
3. Validate the plan and show results
