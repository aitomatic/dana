# Changelog

## [1.1.0] - 2025-01-23

### Added
- Cost calculation now properly displayed for **failed plans**
- Even when a plan fails to reach the target temperature, the HVAC still runs and consumes energy
- Three test scenarios in `agent_example.py`:
  - **Success** (60 min): Plan succeeds, reaches target
  - **Failed** (10 min): Plan fails, but shows partial cooling cost
  - **Test scenarios**: Multiple edge cases (60, 30, 15 min)

### Changed
- **`agent_example.py`** now shows cost for both successful and failed plans
- Failed plans now display:
  - Partial cooling cost (energy consumed during available time)
  - Final temperature achieved (partial cooling)
  - Clear indication that HVAC ran even though target wasn't reached

### Example Output

#### Success Scenario (60 minutes available)
```
✓ PLAN IS FEASIBLE - READY TO EXECUTE!

Energy Cost:
  • This action: 7.000 kWh
  • Total cost: 7.000 kWh

Expected Outcome:
  • Final temp: 72.0°F
  • Meeting comfort: ✓ Achieved
```

#### Failed Scenario (10 minutes available, needs 19 minutes)
```
✗ PLAN FAILED - ADJUSTMENTS NEEDED!

Problem:
  Need 19 min, only 10 min available

Energy Cost (Partial Cooling):
  • This action: 1.500 kWh (HVAC ran for 10 min)
  • Total cost: 1.500 kWh
  • Final temp: 78.6°F (partial cooling achieved)
```

### Why This Matters

When a plan fails:
1. **HVAC still runs** for the available time
2. **Energy is consumed** even though target isn't reached
3. **Partial cooling is achieved** (86°F → 78.6°F in example above)
4. **Cost must be accounted for** in decision-making

This is realistic behavior - in real systems, you can't get a refund if the AC doesn't cool fast enough!

### Usage

Run specific scenarios:
```bash
# Test success scenario
python agent_example.py success

# Test tight schedule
python agent_example.py tight

# Test failed scenario
python agent_example.py failed

# Run all demos
python agent_example.py
```

---

## [1.0.0] - 2025-01-23

### Initial Release
- Simple 2-function API for AI agents
- `get_env_status()` - Get environment state
- `get_feedback()` - Validate HVAC plans
- Realistic physics simulation (7000W 2-ton AC)
- Comprehensive documentation
- Example AI agent implementation
