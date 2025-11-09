# HVAC Environment Simulation - Available Features

**Version**: 2.0 (Refactored)
**Date**: 2025-10-31

---

## 📋 Table of Contents

1. [Environment State Generation](#1-environment-state-generation)
2. [HVAC Physics Simulation](#2-hvac-physics-simulation)
3. [Action Plan Validation](#3-action-plan-validation)
4. [Configuration Profiles](#4-configuration-profiles)
5. [API Functions](#5-api-functions)
6. [Usage Examples](#6-usage-examples)

---

## 1. Environment State Generation

### 1.1 Random Environment Generator

**Module**: `environment_generator.py`

Generates realistic random environment states for conference room scenarios:

#### Features:
- ✅ **Random Time Generation**: 08:00-21:59 (extended business hours)
- ✅ **Daily Temperature Cycle**: Realistic outdoor temperature based on time of day
  - Early morning (06:00-08:00): 45-65°F (coolest)
  - Morning (09:00-11:00): 55-75°F (warming)
  - Afternoon (12:00-16:00): 70-95°F (hottest)
  - Evening (17:00-19:00): 60-85°F (cooling)
  - Night (20:00-21:00): 50-75°F (cooler)
- ✅ **Indoor Temperature**: Outdoor ± 2°F thermal offset (simulates no HVAC running)
- ✅ **Meeting Schedule Generation**: 0-5 random meetings per day

#### Meeting Schedule Constraints:
- First meeting: Minimum 2 hours from current time
- Duration: 30-120 minutes (or 15-30 for late-day meetings)
- Gaps between meetings: 30-180 minutes
- All meetings end before 22:00
- Varied start times (not always on the hour)

#### Usage:
```python
from config import EnvironmentConfig
from environment_generator import EnvironmentGenerator

config = EnvironmentConfig.room_feedback_profile()
generator = EnvironmentGenerator(config)
state = generator.generate_state()

# Returns:
# {
#     "room_name": "Conference Room A",
#     "current_time": "14:30",
#     "indoor_temp": 86.5,
#     "outdoor_temp": 90.2,
#     "meeting_plan": [
#         {"start_time": "16:45", "end_time": "18:00"},
#         {"start_time": "19:30", "end_time": "20:45"}
#     ]
# }
```

---

## 2. HVAC Physics Simulation

### 2.1 Thermal Physics Engine

**Module**: `thermal_physics.py`

High-fidelity thermal dynamics simulation based on exponential temperature evolution model.

#### Core Physics Features:

##### Temperature Evolution
- ✅ **Exponential thermal model**: T(t) = T_inf + (T_0 - T_inf) * exp(-t/τ)
- ✅ **Thermal time constant (τ)**: Based on thermal mass and heat transfer coefficient
- ✅ **Steady-state temperature**: Accounts for outdoor temp, HVAC power, internal heat
- ✅ **Both heating and cooling modes**

##### HVAC Modes
- ✅ **Cooling mode**: Removes heat from room
- ✅ **Heating mode**: Adds heat to room
- ✅ **Base power operation**: Standard HVAC capacity
- ✅ **Turbo mode**: Higher capacity for up to 30 minutes

##### Physical Constraints
- ✅ **Minimum temperature**: 60°F (15.56°C) - physically achievable limit
- ✅ **Temperature drift**: When HVAC is off, temp approaches outdoor temp
- ✅ **Constraint range**: Indoor temp stays within ±15°F of outdoor temp
- ✅ **Internal heat generation**: Simulates occupants, equipment, lighting

##### Edge Case Handling
- ✅ **Fallback calculations**: For extreme temperature differences
- ✅ **Time estimation**: More realistic for large temperature changes (5 min/degree)
- ✅ **Difficulty factor**: Exponential scaling for larger drops (>5°F)
- ✅ **Minimum/maximum bounds**: 30-300 minutes for fallback cases

#### 2.2 Time-to-Target Calculation

**Function**: `hvac_time()`

Calculate how long HVAC needs to reach target temperature.

```python
from thermal_physics import ThermalPhysics
from config import EnvironmentConfig

config = EnvironmentConfig.room_feedback_profile()
physics = ThermalPhysics(config.hvac_config, config.thermal_config)

# How long to cool from 86°F to 72°F?
time_needed = physics.hvac_time(
    current_temp_f=86.0,
    target_temp_f=72.0,
    outdoor_temp_f=95.0,
    mode="cool",
    use_turbo=True
)
# Returns: 24 (minutes)
```

#### 2.3 Temperature Estimation

**Function**: `estimate_temp_at_time()`

Predict indoor temperature when HVAC is off (natural drift toward outdoor temp).

```python
# What will temperature be in 2 hours with no HVAC?
estimated_temp = physics.estimate_temp_at_time(
    current_indoor_temp_f=75.0,
    current_outdoor_temp_f=95.0,
    duration_minutes=120  # 2 hours
)
# Returns: ~89.1°F (drifts toward outdoor temp)
```

#### 2.4 Schedule Feasibility Check

**Function**: `check_hvac_schedule()`

Check if HVAC can reach target temperature within available time.

```python
result = physics.check_hvac_schedule(
    current_temp_f=86.0,
    target_temp_f=72.0,
    time_available_minutes=60,
    outdoor_temp_f=95.0,
    mode="cool",
    use_turbo=True
)
# Returns:
# {
#     "reached_temp": "success",
#     "time_needed_minutes": 24,
#     "time_available_minutes": 60,
#     "redundant_time_minutes": 36,
#     "error": None
# }
```

---

## 3. Action Plan Validation

### 3.1 Multi-Action Plan Validation

**Module**: `action_validator.py`

Validates complete HVAC action plans with sophisticated logic.

#### Core Validation Features:

##### Plan Execution Simulation
- ✅ **Sequential action processing**: Step-by-step through entire plan
- ✅ **Gap temperature tracking**: Estimates temp changes between actions
- ✅ **Cumulative state tracking**: Current temp updates after each action
- ✅ **Partial cooling on failure**: Calculates achieved cooling if action fails

##### Meeting-Aware Validation
- ✅ **Pre-meeting temperature check**: Validates temp reached BEFORE meeting starts
- ✅ **Meeting conflict detection**: Flags if HVAC starts at meeting time
- ✅ **Closest meeting matching**: Associates actions with nearby meetings
- ✅ **Wasted energy detection**: Warns if target reached >5 min before meeting

##### Energy Cost Calculation
- ✅ **Per-action cost tracking**: kWh for each action
- ✅ **Total plan cost**: Cumulative energy consumption
- ✅ **Turbo/base power accounting**: Accurate power consumption calculation
- ✅ **Turbo time limits**: Enforces 30-minute turbo maximum

##### Detailed Feedback
- ✅ **Action-by-action results**: Success/failure for each action
- ✅ **Time needed vs available**: Shows if enough time to reach target
- ✅ **Reached time calculation**: When target would actually be reached
- ✅ **Redundant time reporting**: Extra time after reaching target
- ✅ **Error messages**: Detailed explanations of failures

#### 3.2 Validation Example

```python
from action_validator import ActionValidator

validator = ActionValidator(physics, config)

plan = [
    {"time_on": "14:00", "time_off": "15:00", "use_turbo": True},
    {"time_on": "16:30", "time_off": "17:30", "use_turbo": False}
]
target_temps = [72.0, 70.0]
meeting_plan = [
    {"start_time": "15:00", "end_time": "16:00"},
    {"start_time": "17:30", "end_time": "18:30"}
]

result = validator.validate_plan_success(
    current_indoor_temp_f=86.0,
    outdoor_temp_f=95.0,
    current_time="13:30",
    plan=plan,
    target_temps=target_temps,
    mode="cool",
    meeting_plan=meeting_plan
)

# Returns detailed results for each action:
# {
#     "plan_success": "success",
#     "total_cost_kwh": 24.5,
#     "final_temp_f": 70.0,
#     "action_results": [
#         {
#             "action_index": 0,
#             "schedule_success": "success",
#             "time_needed_minutes": 24,
#             "time_available_minutes": 60,
#             "reached_time": "14:24",
#             "cost_kwh": 13.5,
#             "meeting_start_time": "15:00",
#             "error": "Target reached at 14:24, meeting starts at 15:00..."
#         },
#         ...
#     ],
#     "failed_actions": []
# }
```

---

## 4. Configuration Profiles

### 4.1 HVAC System Profiles

**Module**: `config.py`

Two pre-configured HVAC systems matching original implementations:

#### Profile 1: Small Unit (2000W) - `ac_test.py` parameters
```python
config = EnvironmentConfig.ac_test_profile()

# Specifications:
# - Base capacity: 2000W (~6,800 BTU/hr)
# - Turbo capacity: 2600W (~8,900 BTU/hr)
# - Turbo max: 30 minutes
# - Heat transfer (UA): 150.0 W/K (standard insulation)
# - Thermal mass (C): 5e5 J/K (smaller room)
# - Internal heat: 200W
```

**Use case**: Small office, study room, compact conference room

#### Profile 2: Standard 2-Ton (7000W) - `room_feedback.py` parameters (DEFAULT)
```python
config = EnvironmentConfig.room_feedback_profile()

# Specifications:
# - Base capacity: 7000W (~24,000 BTU/hr)
# - Turbo capacity: 9000W (~30,000 BTU/hr)
# - Turbo max: 30 minutes
# - Heat transfer (UA): 85.0 W/K (better insulation)
# - Thermal mass (C): 1.2e6 J/K (larger room)
# - Internal heat: 100W
```

**Use case**: Standard conference room, medium office, typical residential room

#### Performance Comparison:
| Scenario | Small Unit (2000W) | Standard (7000W) | Difference |
|----------|-------------------|------------------|------------|
| Cool 86→77°F with turbo | 40 minutes | 12 minutes | **3.3x faster** |
| Cool 86→77°F no turbo | 56 minutes | 16 minutes | **3.5x faster** |

### 4.2 Custom Configurations

Create custom HVAC profiles:

```python
from config import HVACConfig, ThermalConfig, EnvironmentConfig

# Custom HVAC unit
custom_hvac = HVACConfig(
    name="Large 3-Ton Unit",
    base_capacity_w=10500.0,  # 3-ton = 36,000 BTU/hr
    turbo_capacity_w=13500.0,
    turbo_max_minutes=30.0
)

# Custom thermal properties
custom_thermal = ThermalConfig(
    heat_transfer_coeff_w_k=100.0,
    thermal_mass_j_k=2.0e6,  # Large thermal mass
    internal_heat_w=150.0,
    fan_boost_multiplier=1.0
)

# Combine into custom config
custom_config = EnvironmentConfig(
    room_name="Large Conference Room",
    hvac_config=custom_hvac,
    thermal_config=custom_thermal
)
```

---

## 5. API Functions

### 5.1 Simple API for AI Agents

**Module**: `hvac_api.py`

Three main functions designed for LLM/AI agent consumption:

#### Function 1: `get_env_status()`

Get current environment state.

```python
from hvac_api import get_env_status

# Get random environment state
status = get_env_status()

# Or with custom configuration
status = get_env_status(
    room_name="Meeting Room B",
    config=EnvironmentConfig.ac_test_profile()
)

# Returns:
# {
#     "room_name": "Conference Room A",
#     "current_time": "14:30",
#     "indoor_temp": 86.5,
#     "outdoor_temp": 90.2,
#     "meeting_plan": [...]
# }
```

**Features**:
- Fresh random state each call (not persistent)
- Realistic temperature and time
- Meeting schedule with constraints
- Optional custom configuration

#### Function 2: `get_feedback()`

Validate HVAC action plan and get detailed feedback.

```python
from hvac_api import get_feedback

feedback = get_feedback(
    current_indoor_temp=86.0,
    outdoor_temp=95.0,
    current_time="13:30",
    plan=[
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": True}
    ],
    target_temps=[72.0],
    mode="cool",
    meeting_plan=[
        {"start_time": "15:00", "end_time": "16:00"}
    ]
)

# Returns:
# {
#     "plan_success": "success",
#     "total_cost_kwh": 13.5,
#     "final_temp_f": 72.0,
#     "action_results": [...],
#     "failed_actions": []
# }
```

**Features**:
- Multi-action plan validation
- Meeting-aware validation
- Energy cost calculation
- Detailed per-action results
- Gap temperature tracking
- Wasted energy detection

#### Function 3: `check_single_action()`

Simplified check for single HVAC action.

```python
from hvac_api import check_single_action

result = check_single_action(
    current_temp=86.0,
    target_temp=72.0,
    current_time="14:00",
    target_time="15:00",
    outdoor_temp=95.0,
    use_turbo=True,
    mode="cool"
)

# Returns:
# {
#     "reached_temp": "success",
#     "time_needed_minutes": 24,
#     "time_available_minutes": 60,
#     "redundant_time_minutes": 36,
#     "error": None
# }
```

**Features**:
- Quick feasibility check
- No complex plan needed
- Time calculations
- Success/failure indication

---

## 6. Usage Examples

### Example 1: Basic Environment Simulation

```python
# Get random environment and check current conditions
from hvac_api import get_env_status

status = get_env_status()
print(f"Current time: {status['current_time']}")
print(f"Indoor: {status['indoor_temp']}°F")
print(f"Outdoor: {status['outdoor_temp']}°F")
print(f"Meetings: {len(status['meeting_plan'])}")
```

### Example 2: Simple Plan Validation

```python
# Create and validate a simple cooling plan
from hvac_api import get_env_status, get_feedback

status = get_env_status()

plan = [{
    "time_on": status["current_time"],
    "time_off": "18:00",
    "use_turbo": True
}]

feedback = get_feedback(
    current_indoor_temp=status["indoor_temp"],
    outdoor_temp=status["outdoor_temp"],
    current_time=status["current_time"],
    plan=plan,
    target_temps=[72.0],
    mode="cool"
)

if feedback["plan_success"] == "success":
    print(f"✓ Plan works! Cost: {feedback['total_cost_kwh']:.2f} kWh")
else:
    print("✗ Plan failed")
    for failed in feedback["failed_actions"]:
        print(f"  Action {failed['action_index']}: {failed['error']}")
```

### Example 3: Meeting-Aware Planning

```python
# Ensure room is comfortable before meetings
from hvac_api import get_env_status, get_feedback

status = get_env_status()

if status["meeting_plan"]:
    first_meeting = status["meeting_plan"][0]

    # Plan to cool 30 minutes before meeting
    plan = [{
        "time_on": status["current_time"],
        "time_off": first_meeting["start_time"],
        "use_turbo": True
    }]

    feedback = get_feedback(
        current_indoor_temp=status["indoor_temp"],
        outdoor_temp=status["outdoor_temp"],
        current_time=status["current_time"],
        plan=plan,
        target_temps=[72.0],
        mode="cool",
        meeting_plan=status["meeting_plan"]  # Enable meeting validation
    )

    # Check for wasted energy warnings
    if feedback["plan_success"] == "success":
        action = feedback["action_results"][0]
        if "wasted energy" in action.get("error", "").lower():
            print("⚠ Warning: Reaching target too early, wasting energy!")
            print(f"  {action['error']}")
```

### Example 4: Using Different HVAC Profiles

```python
# Compare performance of different HVAC systems
from config import EnvironmentConfig
from thermal_physics import ThermalPhysics

# Small 2000W unit
config_small = EnvironmentConfig.ac_test_profile()
physics_small = ThermalPhysics(config_small.hvac_config, config_small.thermal_config)
time_small = physics_small.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)

# Standard 7000W unit
config_standard = EnvironmentConfig.room_feedback_profile()
physics_standard = ThermalPhysics(config_standard.hvac_config, config_standard.thermal_config)
time_standard = physics_standard.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)

print(f"Small unit (2000W): {time_small} minutes")
print(f"Standard unit (7000W): {time_standard} minutes")
print(f"Standard is {time_small/time_standard:.1f}x faster")
```

### Example 5: Multi-Action Complex Plan

```python
# Create complex multi-action plan with gaps
from hvac_api import get_feedback

plan = [
    # Cool for morning meeting
    {"time_on": "08:00", "time_off": "09:00", "use_turbo": True},
    # Turn off during meeting (gap: 09:00-11:00)
    # Cool for afternoon meeting
    {"time_on": "11:00", "time_off": "13:00", "use_turbo": False},
    # Turn off during meeting (gap: 13:00-15:00)
    # Cool for evening meeting
    {"time_on": "15:00", "time_off": "17:00", "use_turbo": True},
]

target_temps = [70.0, 68.0, 72.0]

feedback = get_feedback(
    current_indoor_temp=80.0,
    outdoor_temp=90.0,
    current_time="07:30",
    plan=plan,
    target_temps=target_temps,
    mode="cool"
)

print(f"Total energy: {feedback['total_cost_kwh']:.2f} kWh")
print(f"Final temp: {feedback['final_temp_f']:.1f}°F")

for i, action in enumerate(feedback["action_results"]):
    status = "✓" if action["schedule_success"] == "success" else "✗"
    print(f"{status} Action {i}: {action['time_on']} → {action['time_off']}")
    print(f"   Cost: {action['cost_kwh']:.2f} kWh")
```

---

## 7. Feature Summary

### ✅ Environment Simulation
- Random realistic environment generation
- Time-based outdoor temperature cycles
- Meeting schedule generation with constraints
- Indoor/outdoor temperature relationships

### ✅ Physics Simulation
- Exponential thermal model
- Heating and cooling modes
- Turbo mode support (30 min max)
- Temperature drift estimation
- Edge case handling

### ✅ Plan Validation
- Multi-action plan validation
- Gap temperature tracking
- Meeting-aware validation
- Wasted energy detection
- Partial cooling calculation
- Energy cost calculation (kWh)

### ✅ Configuration
- 2 pre-configured HVAC profiles
- Custom configuration support
- Room-specific thermal properties
- Easy profile switching

### ✅ API
- 3 simple functions for AI agents
- Backward compatible
- Detailed feedback
- Error handling

### ✅ Quality
- 100% functionality preserved
- All tests passing
- Type hints throughout
- Comprehensive documentation

---

## 8. Technical Specifications

### Supported Parameters

| Parameter | Range | Unit | Description |
|-----------|-------|------|-------------|
| Temperature | 60-100 | °F | Indoor/outdoor temperature |
| HVAC Base Power | 2000-10000+ | W | Base cooling/heating capacity |
| HVAC Turbo Power | 2600-15000+ | W | Turbo mode capacity |
| Turbo Duration | 0-30 | min | Maximum turbo time |
| Heat Transfer (UA) | 50-200 | W/K | Building heat transfer |
| Thermal Mass (C) | 1e5-5e6 | J/K | Building thermal mass |
| Internal Heat | 50-500 | W | Occupants, equipment |
| Time Range | 08:00-21:59 | HH:MM | Operating hours |
| Meeting Duration | 15-120 | min | Meeting length |

### Constraints

- Minimum achievable temperature: **60°F**
- Temperature drift constraint: **±15°F from outdoor**
- Turbo maximum duration: **30 minutes**
- Minimum meeting gap from current time: **2 hours**
- Business hours: **08:00-22:00**

---

## 9. Next Steps

### For AI Agents
Use the 3 simple API functions in `hvac_api.py` to:
1. Get environment status
2. Create HVAC plans
3. Validate plans with feedback

### For Developers
Extend the system by:
1. Creating custom HVAC profiles in `config.py`
2. Adding new validation logic in `action_validator.py`
3. Enhancing physics model in `thermal_physics.py`

### For Researchers
Experiment with:
1. Different HVAC capacities and thermal properties
2. Multi-room scenarios
3. Weather integration
4. Energy optimization algorithms

---

**For complete examples, see**: `agent_example.py`
**For verification tests, see**: `verify_refactoring.py`
**For design details, see**: `REFACTORING_DESIGN.md`
