# Deprecated Files

**⚠️ These files are deprecated and kept only for reference.**

## Files

- **`ac_test.py`** - Original physics engine with 2000W HVAC profile
  - **Replaced by**: `core/thermal_physics.py` with `EnvironmentConfig.ac_test_profile()`

- **`room_feedback.py`** - Original physics engine with 7000W HVAC profile + validation logic
  - **Replaced by**:
    - `core/thermal_physics.py` (physics)
    - `core/action_validator.py` (validation)
    - `EnvironmentConfig.room_feedback_profile()` (7000W config)

- **`single_room.py`** - Original environment state generator
  - **Replaced by**: `core/environment_generator.py`

## Why Deprecated?

These files contained **~800 lines of duplicated code**:
- `ac_test.py` and `room_feedback.py` had nearly identical physics functions
- Only differences were HVAC capacity constants and thermal parameters

## New Modular Architecture

The refactored code eliminates duplication:
- Single physics engine configurable via `HVACConfig` and `ThermalConfig`
- Both original profiles preserved as configuration presets
- 100% backward compatible API
- All functionality preserved and verified

## Migration Guide

### Old Code (using ac_test.py):
```python
from ac_test import hvac_time

time = hvac_time(86.0, 72.0, mode="cool", T_out_F=95.0, use_turbo=True)
```

### New Code:
```python
from core import EnvironmentConfig, ThermalPhysics

config = EnvironmentConfig.ac_test_profile()  # Same parameters as ac_test.py
physics = ThermalPhysics(config.hvac_config, config.thermal_config)
time = physics.hvac_time(86.0, 72.0, 95.0, mode="cool", use_turbo=True)
```

### Or use the simple API:
```python
from hvac_api import get_env_status, get_feedback

# Works exactly the same, uses room_feedback.py profile by default
status = get_env_status()
feedback = get_feedback(...)
```

## Do Not Use

**These files should not be used in new code.** They are kept only for:
1. Reference comparison in verification tests
2. Historical documentation
3. Understanding the refactoring changes

See `../tests/verify_refactoring.py` for how the old and new implementations are compared.

---

**Date Deprecated**: 2025-10-31
**Refactoring Version**: 2.0.0
