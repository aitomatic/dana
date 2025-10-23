# HVAC Control System API

Simple API for AI agents to control HVAC systems with realistic physics simulation.

## 🚀 Quick Start

```python
from hvac_api import get_env_status, get_feedback

# 1. Get environment status
status = get_env_status()

# 2. Create a cooling plan
plan = [{
    "time_on": status["current_time"],
    "time_off": status["meeting_plan"][0]["start_time"],
    "use_turbo": True
}]

# 3. Validate the plan
feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=plan,
    target_temps=[72.0]
)

# 4. Check if it works
if feedback["plan_success"] == "success":
    print(f"✓ Cost: {feedback['total_cost_kwh']:.2f} kWh")
```

## 📁 Files

### Core API
- **`hvac_api.py`** - Main API with 2 functions
  - `get_env_status()` - Get current environment
  - `get_feedback()` - Validate HVAC plans

### Simulation Engine
- **`room_feedback.py`** - HVAC physics simulation (realistic thermodynamics)
- **`single_room.py`** - Room environment simulator

### Documentation
- **`QUICK_START.md`** - Quick reference guide
- **`API_README.md`** - Complete API documentation

### Examples
- **`agent_example.py`** - AI agent example with mocked inputs (easy testing)
- **`test_hvac_realism.py`** - Comprehensive test suite

## 🎯 The 2 Core Functions

### Function 1: `get_env_status()`

**Returns current environment state**

```python
status = get_env_status()
# {
#   "room_name": "Conference Room A",
#   "current_time": "14:00",
#   "indoor_temp": 86.0,
#   "outdoor_temp": 95.0,
#   "meeting_plan": [
#     {"start_time": "15:00", "end_time": "16:30"}
#   ]
# }
```

### Function 2: `get_feedback()`

**Validates HVAC plan and returns detailed feedback**

```python
feedback = get_feedback(
    current_indoor_temp=86.0,
    outdoor_temp=95.0,
    current_time="14:00",
    plan=[{"time_on": "14:00", "time_off": "15:00", "use_turbo": True}],
    target_temps=[72.0]
)
# {
#   "plan_success": "success",
#   "total_cost_kwh": 8.5,
#   "final_temp_f": 72.0,
#   "action_results": [...],
#   "failed_actions": []
# }
```

## 🧪 Testing

### Run the API demo
```bash
python hvac_api.py
```

### Run the AI agent example (with mocked inputs)
```bash
python agent_example.py
```

Output shows:
- Main agent decision (60-minute cooling scenario)
- Multiple test scenarios (60, 30, 15 minutes)

### Run comprehensive tests
```bash
python test_hvac_realism.py
```

## 🏗️ System Specifications

### HVAC Capacity
- **Base Mode**: 7,000W (~24,000 BTU/hr) - typical 2-ton residential AC
- **Turbo Mode**: 9,000W (~30,000 BTU/hr) - 29% power boost
- **Turbo Duration**: Maximum 30 minutes, then switches to base

### Realistic Performance
| Temperature Drop | Time Required |
|------------------|---------------|
| 2-3°F | 2-6 minutes |
| 5-8°F | 8-14 minutes |
| 10-16°F | 20-29 minutes |

### Physical Parameters
- **Insulation**: UA = 85 W/K (well-insulated building)
- **Thermal Mass**: C = 1.2×10⁶ J/K (typical residential)
- **Internal Heat**: Q_int = 100W (lights, equipment)

## 📊 Example Output

```
================================================================================
AI AGENT: HVAC Control Decision System
================================================================================

STEP 1: Getting environment status...
--------------------------------------------------------------------------------
Room: Conference Room A
Current Time: 14:00
Indoor Temperature: 86.0°F
Outdoor Temperature: 95.0°F
Scheduled Meetings: 2

Meeting Schedule:
  1. 15:00 - 16:30
  2. 17:00 - 18:00

STEP 2: Analyzing situation...
--------------------------------------------------------------------------------
Current: 86.0°F
Threshold: 75.0°F
Needs cooling? True
Has meetings? True

→ Decision: Cool to 72.0°F before meetings

STEP 3: Creating optimal cooling plan...
--------------------------------------------------------------------------------
First meeting: 15:00
Time until meeting: 60 minutes
Strategy: BASE mode (economical)

STEP 4: Validating plan with HVAC simulation...
--------------------------------------------------------------------------------
Result: SUCCESS

STEP 5: Final decision...
--------------------------------------------------------------------------------
✓ PLAN IS FEASIBLE - READY TO EXECUTE!

Execution Details:
  • Turn on AC: 14:00
  • Mode: Base (7000W)
  • Target reached: 14:25
  • Turn off AC: 15:00

Performance Metrics:
  • Time needed: 25 min
  • Time available: 60 min
  • Safety margin: 35 min

Energy Cost:
  • This action: 7.000 kWh
  • Total cost: 7.000 kWh

Expected Outcome:
  • Final temp: 72.0°F
  • Meeting comfort: ✓ Achieved
```

## 📚 Documentation

- **QUICK_START.md** - Quick reference for AI agents
- **API_README.md** - Complete API documentation with examples

## 🔬 Physics Model

The simulation uses first-order thermal dynamics:

```
T(t) = T_inf + (T₀ - T_inf) × e^(-t/τ)
```

Where:
- `T_inf` = Equilibrium temperature with HVAC on
- `τ` = Time constant (C/UA)
- Temperature approach is **exponential**, not linear

This provides realistic cooling behavior matching real HVAC systems.

## 💡 Key Features

✅ **Realistic Physics** - Based on actual thermal dynamics
✅ **Easy Testing** - Mocked inputs for reproducible tests
✅ **Simple API** - Just 2 functions for AI agents
✅ **Detailed Feedback** - Time, cost, and feasibility analysis
✅ **Multiple Scenarios** - Test edge cases automatically

## 🤖 For AI Agents

The API is designed to be intuitive for AI agents:

1. **Call `get_env_status()`** to understand the situation
2. **Create a plan** based on meetings and temperature
3. **Call `get_feedback()`** to validate the plan
4. **Adjust if needed** based on feedback
5. **Execute** when plan succeeds

See `agent_example.py` for a complete working example.

---

**Version**: 1.0
**Last Updated**: 2025-01-23
