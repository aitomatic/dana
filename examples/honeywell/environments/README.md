# HVAC API - 2 Simple Functions

Simple API for AI agents to control HVAC systems.

## 🎯 The 2 Functions

```python
from hvac_api import get_env_status, get_feedback

# 1. Get environment
status = get_env_status()

# 2. Validate plan
feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": False}],
    target_temps=[72.0]
)
```

## 🧪 Quick Test

```bash
python agent_example.py
```

**Example Output** (varies each run - real API generates random data):
```
FUNCTION 1: get_env_status()
Output:
  room_name:    Conference Room A
  current_time: 20:22              ← Random time
  indoor_temp:  74.6°F             ← Random temp (close to outdoor)
  outdoor_temp: 73.7°F             ← Random temp
  meetings:     1 scheduled        ← Random meetings
    1. 21:06 - 22:00

FUNCTION 2: get_feedback()
Input:
  current_indoor_temp: 74.6°F
  plan:                20:22 → 21:06 (turbo: False)  ← Dynamic plan
  target_temps:        72.0°F

Output:
  plan_success:    success
  total_cost_kwh:  7.000 kWh
  final_temp_f:    72.0°F
  time_needed:     6 min
  time_available:  44 min

RESULT: ✓ Plan works!
```

## 📁 Files

| File | Purpose |
|------|---------|
| **hvac_api.py** | 2 main functions (get_env_status, get_feedback) |
| **agent_example.py** | Simple demo with mocked inputs |
| **room_feedback.py** | HVAC physics simulation (backend) |
| **single_room.py** | Room environment (backend) |
| **QUICK_START.md** | Quick reference guide |
| **API_README.md** | Complete API docs |

## 📖 Documentation

- **QUICK_START.md** - Quick reference for AI agents
- **API_README.md** - Complete API documentation

## 🔧 System Specs

- **Base Mode**: 7,000W (typical 2-ton AC)
- **Turbo Mode**: 9,000W (29% boost, max 30 min)
- **Cooling**: 2-3°F in 2-6 min, 10-16°F in 20-29 min

## 💡 Usage Pattern

```python
# Step 1: Get environment
status = get_env_status()

# Step 2: Create plan
plan = [{
    "time_on": status["current_time"],
    "time_off": status["meeting_plan"][0]["start_time"],
    "use_turbo": True
}]

# Step 3: Validate
feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=plan,
    target_temps=[72.0]
)

# Step 4: Check
if feedback["plan_success"] == "success":
    print(f"✓ Costs {feedback['total_cost_kwh']:.2f} kWh")
else:
    print(f"✗ Failed: {feedback['failed_actions'][0]['error']}")
```

That's it! Just 2 functions. 🎉
