# HVAC API Quick Start Guide

## For AI Agents: 2 Simple Functions

### TL;DR

```python
from hvac_api import get_env_status, get_feedback

# 1. Get current status
status = get_env_status()
# Returns: {room_name, current_time, indoor_temp, outdoor_temp, meeting_plan}

# 2. Validate your plan
feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}],
    target_temps=[72.0]
)
# Returns: {plan_success, total_cost_kwh, final_temp_f, action_results, failed_actions}
```

---

## Function 1: `get_env_status()`

**What it does:** Returns current room conditions and meeting schedule

**Input:**
- `room_name` (optional): Room name, default "Conference Room A"

**Output:**
```python
{
    "room_name": "Conference Room A",
    "current_time": "14:30",           # Current time
    "indoor_temp": 86.5,               # Current indoor temp (°F)
    "outdoor_temp": 95.2,              # Outdoor temp (°F)
    "meeting_plan": [                  # Scheduled meetings
        {"start_time": "15:00", "end_time": "16:30"},
        {"start_time": "17:00", "end_time": "18:00"}
    ]
}
```

---

## Function 2: `get_feedback()`

**What it does:** Validates if your HVAC plan will work, returns cost and timing

**Inputs:**
- `current_indoor_temp`: Current indoor temp (°F)
- `outdoor_temp`: Outdoor temp (°F)
- `current_time`: Current time "HH:MM"
- `plan`: List of actions (see below)
- `target_temps`: List of target temps for each action
- `mode`: "cool" or "heat" (default "cool")

**Plan Format:**
```python
plan = [
    {
        "time_on": "14:00",    # When to start
        "time_off": "15:00",   # When to stop
        "use_turbo": True      # Use turbo mode? (faster, more energy)
    }
]
target_temps = [72.0]  # One target per action
```

**Output:**
```python
{
    "plan_success": "success",  # or "failed"
    "total_cost_kwh": 8.5,      # Energy cost
    "final_temp_f": 72.0,       # Final temperature
    "action_results": [         # Details for each action
        {
            "action_index": 0,
            "schedule_success": "success",
            "time_needed_minutes": 12,      # How long it takes
            "time_available_minutes": 60,   # How long you have
            "reached_time": "14:12",        # When target is reached
            "redundant_time_minutes": 48,   # Extra time
            "cost_kwh": 8.5
        }
    ],
    "failed_actions": []  # Empty if success
}
```

---

## Minimal Example

```python
from hvac_api import get_env_status, get_feedback

# Get status
status = get_env_status()

# Create plan: cool to 72°F before first meeting
if status["meeting_plan"]:
    plan = [{
        "time_on": status["current_time"],
        "time_off": status["meeting_plan"][0]["start_time"],
        "use_turbo": True
    }]

    # Validate plan
    feedback = get_feedback(
        current_indoor_temp=status["indoor_temp"],
        outdoor_temp=status["outdoor_temp"],
        current_time=status["current_time"],
        plan=plan,
        target_temps=[72.0]
    )

    # Check result
    if feedback["plan_success"] == "success":
        print("✓ Plan works!")
        print(f"  Cost: {feedback['total_cost_kwh']:.2f} kWh")
    else:
        print("✗ Plan failed")
        print(f"  {feedback['failed_actions'][0]['error']}")
```

---

## Key Concepts

### Turbo Mode
- **Turbo**: 9000W, ~30% faster, more energy
- **Base**: 7000W, slower, less energy
- **Rule**: Use turbo if time is tight (<30 min to meeting)

### Typical Cooling Times
- **2-3°F**: 2-6 minutes
- **5-8°F**: 8-14 minutes
- **10-16°F**: 20-29 minutes

### Temperature Drift
- When HVAC is OFF, indoor temp drifts toward outdoor temp
- ~4-5°F/hour drift with 15°F difference
- Account for gaps between actions!

---

## Common Patterns

### Pattern 1: Cool Before Meeting
```python
status = get_env_status()
first_meeting = status["meeting_plan"][0]

plan = [{
    "time_on": status["current_time"],
    "time_off": first_meeting["start_time"],
    "use_turbo": True
}]
target_temps = [72.0]
```

### Pattern 2: Cool for Multiple Meetings
```python
plan = []
target_temps = []

for meeting in status["meeting_plan"][:2]:  # First 2 meetings
    plan.append({
        "time_on": meeting["start_time"],
        "time_off": meeting["end_time"],
        "use_turbo": False  # During meeting, base mode is fine
    })
    target_temps.append(72.0)
```

### Pattern 3: Pre-cool + Maintain
```python
plan = [
    # Pre-cool with turbo
    {
        "time_on": "14:00",
        "time_off": "15:00",
        "use_turbo": True
    },
    # Maintain with base mode
    {
        "time_on": "15:00",
        "time_off": "18:00",
        "use_turbo": False
    }
]
target_temps = [72.0, 72.0]
```

---

## Error Handling

```python
feedback = get_feedback(...)

if feedback["plan_success"] == "failed":
    for failed in feedback["failed_actions"]:
        error = failed["error"]

        if "not enough time" in error.lower():
            # Solution: Start earlier or use turbo
            pass
        elif "below 60°f" in error.lower():
            # Solution: Raise target temp
            pass
```

---

## Testing

Run the examples:
```bash
# Test the API
python hvac_api.py

# Run AI agent example
python agent_example.py
```

---

## Full Documentation

See `API_README.md` for complete API documentation.
