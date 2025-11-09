import math
from typing import Literal

Mode = Literal["cool", "heat"]

# Fixed HVAC thermal capacities (adjusted for 2-ton residential AC realism)
BASE_CAPACITY_W  = 7000.0   # W (~24,000 BTU/hr, typical 2-ton AC)
TURBO_CAPACITY_W = 9000.0   # W (~30,000 BTU/hr, turbo boost)
TURBO_MAX_MIN    = 30.0     # max Turbo time (minutes)

def _tau_minutes(C: float, UA_eff: float) -> float:
    return (C / UA_eff) / 60.0

def _T_inf(T_out: float, UA_eff: float, Q_int: float, Q_HVAC: float) -> float:
    return T_out + (Q_int + Q_HVAC) / UA_eff

def _time_to_target_minutes(T0: float, T_target: float, Tinf: float, tau_min: float) -> float:
    """Calculate time to target temperature. Temperatures in Celsius internally, displayed in Fahrenheit."""
    num = (T_target - Tinf)
    den = (T0 - Tinf)
    if num == 0:
        return 0.0
    ratio = num / den

    # Helper to convert C to F for display
    def C_to_F(c: float) -> float:
        return c * 9.0/5.0 + 32.0

    # Only block targets below 60°F (15.56°C)
    min_achievable = 15.56  # 60°F in Celsius
    if T_target < min_achievable:
        raise ValueError("Target below 60°F minimum.")

    # For targets above 60°F, allow them even if ratio <= 0
    # This means the HVAC can reach any temperature above 60°F
    if ratio <= 0:
        # Calculate time based on temperature difference and difficulty
        temp_diff = abs(T_target - T0)

        # More realistic calculation:
        # - Base time: 5 minutes per degree (more realistic)
        # - Difficulty factor: exponential for larger drops
        # - Minimum: 30 min, Maximum: 300 min
        base_time = temp_diff * 5.0  # 5 minutes per degree is more realistic

        # Add difficulty factor for larger temperature changes
        if temp_diff > 5:  # Start difficulty factor earlier
            difficulty_factor = 1.0 + (temp_diff - 5) * 0.2  # 20% extra per degree above 5
            base_time *= difficulty_factor

        time_estimate = max(30.0, min(300.0, base_time))  # Higher minimum for realism
        # Convert to Fahrenheit for display
        temp_diff_f = temp_diff * 9.0/5.0
        print(f"      Fallback calculation: {C_to_F(T0):.1f}°F → {C_to_F(T_target):.1f}°F, diff={temp_diff_f:.1f}°F, time={time_estimate:.0f}min")
        return time_estimate

    result = -tau_min * math.log(ratio)
    # Convert to Fahrenheit for display
    print(f"      Normal calculation: {C_to_F(T0):.1f}°F → {C_to_F(T_target):.1f}°F, ratio={ratio:.3f}, time={result:.0f}min")
    print(f"        Current: {C_to_F(T0):.1f}°F, Target: {C_to_F(T_target):.1f}°F, Tinf: {C_to_F(Tinf):.1f}°F")
    return result

def _advance_temperature(T0: float, minutes: float, Tinf: float, tau_min: float) -> float:
    return Tinf + (T0 - Tinf) * math.exp(-minutes / tau_min)

def hvac_time(
    T0_F: float,
    T_target_F: float,
    mode: Mode = "cool",
    *,
    T_out_F: float = 95.0,   # °F, outdoor temperature
    UA: float = 85.0,        # W/K, heat transfer coefficient (better insulation)
    C: float = 1.2e6,        # J/K, thermal mass (typical residential)
    Q_int: float = 100.0,    # W, internal heat (reduced to prevent above-outdoor temps)
    fan_boost_UA: float = 1.0,
    use_turbo: bool = False
) -> int:
    """
    Returns time (minutes) to reach T_target_F from T0_F.
    Turbo = 9000 W up to 30 minutes, then 7000 W base (2-ton AC).
    All temps in °F (internally converted to K-deltas).
    """
    # Convert °F to K scale differences
    def F_to_K(F: float) -> float: return (F - 32.0) * 5.0/9.0
    def K_to_F(K: float) -> float: return K * 9.0/5.0 + 32.0

    # Work in Kelvin-equivalent °C
    T0     = F_to_K(T0_F)
    T_out  = F_to_K(T_out_F)
    T_goal = F_to_K(T_target_F)

    UA_eff = UA * fan_boost_UA
    tau_min = _tau_minutes(C, UA_eff)

    sign   = -1.0 if mode == "cool" else  1.0
    Q_base = sign * BASE_CAPACITY_W
    Q_tbo  = sign * TURBO_CAPACITY_W

    def _check(T_start, T_goal, Q_hvac):
        Tinf = _T_inf(T_out, UA_eff, Q_int, Q_hvac)
        if (T_goal - T_start) == 0:
            return Tinf, 0.0
        
        # Only block targets below 60°F (15.56°C)
        min_achievable = 15.56  # 60°F in Celsius
        if T_goal < min_achievable:
            raise ValueError(f"Target {T_target_F}°F unreachable (below 60°F minimum).")
        
        # For targets above 60°F, allow them even if they seem "unreachable"
        # The HVAC system should be able to reach any temperature above 60°F
        return Tinf, _time_to_target_minutes(T_start, T_goal, Tinf, tau_min)

    total_min = 0.0
    T_curr = T0

    # Phase A: Turbo (up to 30 min)
    if use_turbo:
        Tinf_t, t_need_t = _check(T_curr, T_goal, Q_tbo)
        if t_need_t <= TURBO_MAX_MIN:
            return int(round(t_need_t))
        T_curr = _advance_temperature(T_curr, TURBO_MAX_MIN, Tinf_t, tau_min)
        total_min += TURBO_MAX_MIN

    # Phase B: Base
    _, t_need_b = _check(T_curr, T_goal, Q_base)
    total_min += t_need_b
    return int(round(total_min))


def estimate_temp_at_time(
    current_indoor_temp_f: float,
    current_outdoor_temp_f: float,
    current_time: str,  # Format: "HH:MM"
    target_time: str,   # Format: "HH:MM"
    *,
    ua: float = 85.0,        # W/K, heat transfer coefficient (better insulation)
    c: float = 1.2e6,        # J/K, thermal mass (typical residential)
    q_int: float = 100.0,    # W, internal heat (reduced to prevent above-outdoor temps)
    max_temp_diff: float = 15.0  # Max difference from outdoor temp (°F)
) -> float:
    """
    Estimate indoor temperature at a given time without HVAC running.

    Args:
        current_indoor_temp_f: Current indoor temperature in °F
        current_outdoor_temp_f: Current outdoor temperature in °F
        current_time: Current time in "HH:MM" format
        target_time: Target time in "HH:MM" format
        ua: Heat transfer coefficient (W/K)
        c: Thermal mass (J/K)
        q_int: Internal heat generation (W)
        max_temp_diff: Maximum difference from outdoor temp (°F)

    Returns:
        Estimated indoor temperature in °F at target time
    """
    def parse_time(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    def f_to_k(f: float) -> float:
        return (f - 32.0) * 5.0/9.0

    def k_to_f(k: float) -> float:
        return k * 9.0/5.0 + 32.0

    # Parse times
    current_minutes = parse_time(current_time)
    target_minutes = parse_time(target_time)

    # Calculate time difference in minutes
    time_diff_minutes = target_minutes - current_minutes

    # If target time is before current time, assume next day
    if time_diff_minutes < 0:
        time_diff_minutes += 24 * 60

    # Convert temperatures to Kelvin scale
    t_indoor = f_to_k(current_indoor_temp_f)
    t_outdoor = f_to_k(current_outdoor_temp_f)

    # Calculate thermal time constant
    tau_min = _tau_minutes(c, ua)

    # Calculate steady-state temperature without HVAC (Q_HVAC = 0)
    t_inf = _T_inf(t_outdoor, ua, q_int, 0.0)

    # Use the temperature advance function to estimate temperature
    t_estimated = _advance_temperature(
        t_indoor, time_diff_minutes, t_inf, tau_min
    )

    # Convert back to Fahrenheit
    estimated_temp_f = k_to_f(t_estimated)
    
    # Constrain the estimated temperature to be within reasonable bounds
    # of the outdoor temperature
    min_estimated = current_outdoor_temp_f - max_temp_diff
    max_estimated = current_outdoor_temp_f + max_temp_diff
    
    # Apply constraints
    constrained_temp = max(min_estimated, min(estimated_temp_f, max_estimated))
    
    return constrained_temp


def check_hvac_schedule(
    current_temp_f: float,
    target_temp_f: float,
    use_turbo: bool,
    current_time: str,  # Format: "HH:MM"
    target_time: str,   # Format: "HH:MM"
    *,
    mode: Mode = "cool",
    t_out_f: float = 95.0,   # °F, outdoor temperature
    ua: float = 85.0,        # W/K, heat transfer coefficient (better insulation)
    c: float = 1.2e6,        # J/K, thermal mass (typical residential)
    q_int: float = 100.0,    # W, internal heat (reduced to prevent above-outdoor temps)
    fan_boost_ua: float = 1.0
) -> dict:
    """
    Check if HVAC can reach target temperature within the specified time window.
    
    Args:
        current_temp_f: Current indoor temperature in °F
        target_temp_f: Target temperature in °F
        use_turbo: Whether to use turbo mode
        current_time: Current time in "HH:MM" format
        target_time: Target time in "HH:MM" format
        mode: HVAC mode ("cool" or "heat")
        t_out_f: Outdoor temperature in °F
        ua: Heat transfer coefficient (W/K)
        c: Thermal mass (J/K)
        q_int: Internal heat generation (W)
        fan_boost_ua: Fan boost multiplier for UA
        
    Returns:
        Dictionary with keys:
        - reached_temp: "success" or "failed"
        - time_needed_minutes: Time needed to reach target (minutes)
        - time_available_minutes: Time available until target time (minutes)
        - redundant_time_minutes: Extra time if target reached early (None if failed)
        - reached_time: Time when target would be reached (HH:MM format, None if failed)
    """
    def parse_time(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def minutes_to_time(minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    # Parse times
    current_minutes = parse_time(current_time)
    target_minutes = parse_time(target_time)
    
    # Calculate time available
    time_available_minutes = target_minutes - current_minutes
    if time_available_minutes < 0:
        time_available_minutes += 24 * 60  # Next day
    
    # Calculate time needed using hvac_time function
    try:
        time_needed_minutes = hvac_time(
            current_temp_f, target_temp_f, mode=mode,
            T_out_F=t_out_f, UA=ua, C=c, Q_int=q_int,
            fan_boost_UA=fan_boost_ua, use_turbo=use_turbo
        )
    except ValueError as e:
        # Target temperature is unreachable (physically impossible)
        return {
            "reached_temp": "failed",
            "time_needed_minutes": None,
            "time_available_minutes": time_available_minutes,
            "redundant_time_minutes": None,
            "reached_time": None,
            "error": str(e)
        }
    
    # Check if we can reach target in time
    if time_needed_minutes <= time_available_minutes:
        # Success case
        reached_minutes = current_minutes + time_needed_minutes
        if reached_minutes >= 24 * 60:
            reached_minutes -= 24 * 60  # Next day
        
        redundant_time = time_available_minutes - time_needed_minutes
        
        return {
            "reached_temp": "success",
            "time_needed_minutes": time_needed_minutes,
            "time_available_minutes": time_available_minutes,
            "redundant_time_minutes": redundant_time,
            "reached_time": minutes_to_time(reached_minutes),
            "error": None
        }
    else:
        # Failed case - not enough time
        # Calculate when the target would actually be reached
        reached_minutes = current_minutes + time_needed_minutes
        if reached_minutes >= 24 * 60:
            reached_minutes -= 24 * 60  # Next day
        
        actual_reached_time = minutes_to_time(reached_minutes)
        
        # Create a more descriptive error message
        error_msg = (f"Need {time_needed_minutes} min to cool down, "
                     f"only {time_available_minutes} min available. "
                     f"Target would be reached at {actual_reached_time} "
                     f"(after action ends at {target_time})")
        
        return {
            "reached_temp": "failed",
            "time_needed_minutes": time_needed_minutes,
            "time_available_minutes": time_available_minutes,
            "redundant_time_minutes": None,
            "reached_time": actual_reached_time,  # Show when it would actually be reached
            "error": error_msg
        }


def calculate_plan_cost(
    current_indoor_temp_f: float,
    outdoor_temp_f: float,
    current_time: str,  # Format: "HH:MM"
    plan: list,  # List of action dictionaries
    *,
    mode: Mode = "cool",
    ua: float = 85.0,        # W/K, heat transfer coefficient (better insulation)
    c: float = 1.2e6,        # J/K, thermal mass (typical residential)
    q_int: float = 100.0,    # W, internal heat (reduced to prevent above-outdoor temps)
    fan_boost_ua: float = 1.0,
    base_power_w: float = 7000.0,    # W, base HVAC power (2-ton AC)
    turbo_power_w: float = 9000.0,   # W, turbo HVAC power
    turbo_max_min: float = 30.0      # max turbo time (minutes)
) -> dict:
    """
    Calculate total electricity cost for a HVAC action plan.
    
    Args:
        current_indoor_temp_f: Current indoor temperature in °F
        outdoor_temp_f: Outdoor temperature in °F
        current_time: Current time in "HH:MM" format
        plan: List of action dictionaries with keys:
            - time_on: Start time in "HH:MM" format
            - time_off: End time in "HH:MM" format  
            - use_turbo: Boolean for turbo mode
        mode: HVAC mode ("cool" or "heat")
        ua: Heat transfer coefficient (W/K)
        c: Thermal mass (J/K)
        q_int: Internal heat generation (W)
        fan_boost_ua: Fan boost multiplier for UA
        base_power_w: Base HVAC power consumption (W)
        turbo_power_w: Turbo HVAC power consumption (W)
        turbo_max_min: Maximum turbo time (minutes)
        
    Returns:
        Dictionary with:
        - total_cost_kwh: Total electricity consumption in kWh
        - action_details: List of detailed cost breakdown per action
        - final_temp_f: Final temperature after all actions
    """
    def parse_time(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def minutes_to_time(minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def time_diff_minutes(start_time: str, end_time: str) -> int:
        """Calculate time difference in minutes"""
        start_min = parse_time(start_time)
        end_min = parse_time(end_time)
        diff = end_min - start_min
        if diff < 0:
            diff += 24 * 60  # Next day
        return diff
    
    # Initialize tracking variables
    current_temp = current_indoor_temp_f
    current_time_min = parse_time(current_time)
    total_cost_kwh = 0.0
    action_details = []
    
    for i, action in enumerate(plan):
        time_on = action["time_on"]
        time_off = action["time_off"]
        use_turbo = action["use_turbo"]
        
        # Check for gap between previous action and current action
        if i > 0:
            prev_action = plan[i-1]
            prev_time_off = prev_action["time_off"]
            
            # If there's a gap, estimate temperature change during off period
            if prev_time_off != time_on:
                print(f"    Gap detected: {prev_time_off} to {time_on}")
                print(f"    Estimating temp change from {current_temp:.1f}°F...")
                gap_temp = estimate_temp_at_time(
                    current_temp, outdoor_temp_f, prev_time_off, time_on,
                    ua=ua, c=c, q_int=q_int
                )
                print(f"    Estimated temp after gap: {gap_temp:.1f}°F")
                current_temp = gap_temp
            else:
                print(f"    No gap: {prev_time_off} = {time_on}")
        
        # Calculate action duration
        duration_minutes = time_diff_minutes(time_on, time_off)
        
        # Calculate power consumption for this action
        if use_turbo:
            # Turbo phase (up to turbo_max_min) + base phase
            turbo_duration = min(duration_minutes, turbo_max_min)
            base_duration = max(0, duration_minutes - turbo_max_min)
            
            turbo_cost_kwh = (turbo_power_w * turbo_duration) / (1000 * 60)  # Convert to kWh
            base_cost_kwh = (base_power_w * base_duration) / (1000 * 60)
            total_action_cost_kwh = turbo_cost_kwh + base_cost_kwh
        else:
            # Base power only
            total_action_cost_kwh = (base_power_w * duration_minutes) / (1000 * 60)
        
        # Update total cost
        total_cost_kwh += total_action_cost_kwh
        
        # Store action details
        action_details.append({
            "action_index": i,
            "time_on": time_on,
            "time_off": time_off,
            "use_turbo": use_turbo,
            "duration_minutes": duration_minutes,
            "cost_kwh": total_action_cost_kwh,
            "start_temp_f": current_temp
        })
        
        # Update current time and temperature for next iteration
        current_time_min = parse_time(time_off)
        
        # Estimate final temperature after this action
        # This is a simplified approach - in reality you'd need to track the target temp
        # For now, we'll just use the estimate_temp_at_time function
        if i < len(plan) - 1:  # Not the last action
            next_action = plan[i + 1]
            next_time_on = next_action["time_on"]
            current_temp = estimate_temp_at_time(
                current_temp, outdoor_temp_f, time_off, next_time_on,
                ua=ua, c=c, q_int=q_int
            )
    
    return {
        "total_cost_kwh": total_cost_kwh,
        "action_details": action_details,
        "final_temp_f": current_temp
    }


def validate_plan_success(
    current_indoor_temp_f: float,
    outdoor_temp_f: float,
    current_time: str,  # Format: "HH:MM"
    plan: list,  # List of action dictionaries
    target_temps: list,  # List of target temperatures for each action
    *,
    mode: Mode = "cool",
    ua: float = 85.0,        # W/K, heat transfer coefficient (better insulation)
    c: float = 1.2e6,        # J/K, thermal mass (typical residential)
    q_int: float = 100.0,    # W, internal heat (reduced to prevent above-outdoor temps)
    fan_boost_ua: float = 1.0,
    base_power_w: float = 7000.0,    # W, base HVAC power (2-ton AC)
    turbo_power_w: float = 9000.0,   # W, turbo HVAC power
    turbo_max_min: float = 30.0,    # max turbo time (minutes)
    meeting_plan: list = None  # List of meetings with start_time and end_time
) -> dict:
    """
    Validate if a HVAC plan can successfully reach all target temperatures.
    
    Args:
        current_indoor_temp_f: Current indoor temperature in °F
        outdoor_temp_f: Outdoor temperature in °F
        current_time: Current time in "HH:MM" format
        plan: List of action dictionaries with keys:
            - time_on: Start time in "HH:MM" format
            - time_off: End time in "HH:MM" format  
            - use_turbo: Boolean for turbo mode
        target_temps: List of target temperatures for each action
        mode: HVAC mode ("cool" or "heat")
        ua: Heat transfer coefficient (W/K)
        c: Thermal mass (J/K)
        q_int: Internal heat generation (W)
        fan_boost_ua: Fan boost multiplier for UA
        base_power_w: Base HVAC power consumption (W)
        turbo_power_w: Turbo HVAC power consumption (W)
        turbo_max_min: Maximum turbo time (minutes)
        
    Returns:
        Dictionary with:
        - plan_success: "success" or "failed"
        - total_cost_kwh: Total electricity consumption in kWh
        - action_results: List of results for each action
        - failed_actions: List of actions that failed
        - final_temp_f: Final temperature after all actions
    """
    def parse_time(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def time_diff_minutes(start_time: str, end_time: str) -> int:
        """Calculate time difference in minutes"""
        start_min = parse_time(start_time)
        end_min = parse_time(end_time)
        diff = end_min - start_min
        if diff < 0:
            diff += 24 * 60  # Next day
        return diff
    
    # Validate input lengths match
    if len(plan) != len(target_temps):
        return {
            "plan_success": "failed",
            "total_cost_kwh": 0.0,
            "action_results": [],
            "failed_actions": [],
            "final_temp_f": current_indoor_temp_f,
            "error": f"Plan has {len(plan)} actions but {len(target_temps)} target temperatures"
        }
    
    # Initialize tracking variables
    current_temp = current_indoor_temp_f
    current_time_min = parse_time(current_time)
    total_cost_kwh = 0.0
    action_results = []
    failed_actions = []

    # Build a mapping of meeting start times for quick lookup
    meeting_start_times = set()
    if meeting_plan:
        for meeting in meeting_plan:
            meeting_start_times.add(meeting["start_time"])

    for i, (action, target_temp) in enumerate(zip(plan, target_temps)):
        time_on = action["time_on"]
        time_off = action["time_off"]
        use_turbo = action["use_turbo"]
        
        # Check for gap between previous action and current action
        if i > 0:
            prev_action = plan[i-1]
            prev_time_off = prev_action["time_off"]

            # If there's a gap, estimate temperature change during off period
            if prev_time_off != time_on:
                print(f"    Gap detected: {prev_time_off} to {time_on}")
                print(f"    Temp before gap: {current_temp:.1f}°F")
                gap_temp = estimate_temp_at_time(
                    current_temp, outdoor_temp_f, prev_time_off, time_on,
                    ua=ua, c=c, q_int=q_int
                )
                print(f"    Temp after gap: {gap_temp:.1f}°F")
                current_temp = gap_temp

        # CRITICAL VALIDATION: If this action starts at a meeting time,
        # the target temperature must already be reached BEFORE the meeting starts
        if time_on in meeting_start_times:
            # Check if current temperature already meets target
            if mode == "cool" and current_temp > target_temp:
                # Need to cool but haven't reached target yet
                error_msg = f"Meeting starts at {time_on} but room is {current_temp:.1f}°F (target: {target_temp}°F). HVAC should have turned on earlier!"
                failed_action = {
                    "action_index": i,
                    "time_on": time_on,
                    "time_off": time_off,
                    "target_temp_f": target_temp,
                    "error": error_msg
                }
                failed_actions.append(failed_action)

                # Still calculate cost and partial result for this action
                cost_result = calculate_plan_cost(
                    current_indoor_temp_f=current_temp,
                    outdoor_temp_f=outdoor_temp_f,
                    current_time=time_on,
                    plan=[action],
                    mode=mode,
                    ua=ua, c=c, q_int=q_int,
                    fan_boost_ua=fan_boost_ua,
                    base_power_w=base_power_w,
                    turbo_power_w=turbo_power_w,
                    turbo_max_min=turbo_max_min
                )

                action_results.append({
                    "action_index": i,
                    "time_on": time_on,
                    "time_off": time_off,
                    "use_turbo": use_turbo,
                    "target_temp_f": target_temp,
                    "start_temp_f": current_temp,
                    "schedule_success": "failed",
                    "cost_kwh": cost_result["total_cost_kwh"],
                    "time_needed_minutes": None,
                    "time_available_minutes": None,
                    "reached_time": None,
                    "redundant_time_minutes": None,
                    "error": error_msg
                })

                total_cost_kwh += cost_result["total_cost_kwh"]
                # Continue to next action
                continue

            elif mode == "heat" and current_temp < target_temp:
                # Need to heat but haven't reached target yet
                error_msg = f"Meeting starts at {time_on} but room is {current_temp:.1f}°F (target: {target_temp}°F). HVAC should have turned on earlier!"
                failed_action = {
                    "action_index": i,
                    "time_on": time_on,
                    "time_off": time_off,
                    "target_temp_f": target_temp,
                    "error": error_msg
                }
                failed_actions.append(failed_action)

                # Still calculate cost and partial result for this action
                cost_result = calculate_plan_cost(
                    current_indoor_temp_f=current_temp,
                    outdoor_temp_f=outdoor_temp_f,
                    current_time=time_on,
                    plan=[action],
                    mode=mode,
                    ua=ua, c=c, q_int=q_int,
                    fan_boost_ua=fan_boost_ua,
                    base_power_w=base_power_w,
                    turbo_power_w=turbo_power_w,
                    turbo_max_min=turbo_max_min
                )

                action_results.append({
                    "action_index": i,
                    "time_on": time_on,
                    "time_off": time_off,
                    "use_turbo": use_turbo,
                    "target_temp_f": target_temp,
                    "start_temp_f": current_temp,
                    "schedule_success": "failed",
                    "cost_kwh": cost_result["total_cost_kwh"],
                    "time_needed_minutes": None,
                    "time_available_minutes": None,
                    "reached_time": None,
                    "redundant_time_minutes": None,
                    "error": error_msg
                })

                total_cost_kwh += cost_result["total_cost_kwh"]
                # Continue to next action
                continue

        # Check if this action can reach target temperature
        schedule_result = check_hvac_schedule(
            current_temp_f=current_temp,
            target_temp_f=target_temp,
            use_turbo=use_turbo,
            current_time=time_on,
            target_time=time_off,
            mode=mode,
            t_out_f=outdoor_temp_f,
            ua=ua,
            c=c,
            q_int=q_int,
            fan_boost_ua=fan_boost_ua
        )
        
        # Calculate cost for this action
        cost_result = calculate_plan_cost(
            current_indoor_temp_f=current_temp,
            outdoor_temp_f=outdoor_temp_f,
            current_time=time_on,
            plan=[action],  # Single action
            mode=mode,
            ua=ua,
            c=c,
            q_int=q_int,
            fan_boost_ua=fan_boost_ua,
            base_power_w=base_power_w,
            turbo_power_w=turbo_power_w,
            turbo_max_min=turbo_max_min
        )
        
        # Find the closest meeting start time for this action
        meeting_start_time = None
        if meeting_plan:
            # Find the meeting that starts closest to this action's time_on (start time)
            # This makes more sense as we want to match the action with the meeting it's preparing for
            time_on_min = parse_time(time_on)
            closest_meeting = None
            min_diff = float('inf')
            
            for meeting in meeting_plan:
                meeting_start_min = parse_time(meeting["start_time"])
                # Calculate time difference (considering day wrap-around)
                diff = abs(meeting_start_min - time_on_min)
                if diff > 12 * 60:  # More than 12 hours, consider next day
                    diff = 24 * 60 - diff
                
                if diff < min_diff:
                    min_diff = diff
                    closest_meeting = meeting
            
            if closest_meeting:
                meeting_start_time = closest_meeting["start_time"]
        
        # Check if the action reaches target before meeting starts
        final_schedule_success = schedule_result["reached_temp"]
        final_error = schedule_result["error"]
        
        if (schedule_result["reached_temp"] == "success" and
                meeting_start_time and
                schedule_result["reached_time"]):
            
            # Parse times to compare reached time with meeting start time
            reached_minutes = parse_time(schedule_result["reached_time"])
            meeting_start_minutes = parse_time(meeting_start_time)
            
            # If reached time is after meeting start time, mark as failed
            if reached_minutes > meeting_start_minutes:
                final_schedule_success = "failed"
                final_error = (f"Target reached at {schedule_result['reached_time']} "
                               f"but meeting starts at {meeting_start_time}. "
                               f"HVAC should have started earlier to reach target "
                               f"before meeting begins.")
            else:
                # Success case - check if there's wasted energy time
                meeting_time_diff_minutes = meeting_start_minutes - reached_minutes
                if meeting_time_diff_minutes > 5:  # More than 5 minutes early
                    final_error = (f"Target reached at {schedule_result['reached_time']}, "
                                   f"meeting starts at {meeting_start_time}. "
                                   f"Wasted energy time: {meeting_time_diff_minutes} min "
                                   f"(target reached {meeting_time_diff_minutes} min before meeting)")
        
        # Store action result
        action_result = {
            "action_index": i,
            "time_on": time_on,
            "time_off": time_off,
            "use_turbo": use_turbo,
            "target_temp_f": target_temp,
            "start_temp_f": current_temp,
            "schedule_success": final_schedule_success,
            "cost_kwh": cost_result["total_cost_kwh"],
            "time_needed_minutes": schedule_result["time_needed_minutes"],
            "time_available_minutes": schedule_result["time_available_minutes"],
            "reached_time": schedule_result["reached_time"],
            "redundant_time_minutes": schedule_result["redundant_time_minutes"],
            "error": final_error
        }
        
        # Add meeting start time if found
        if meeting_start_time:
            action_result["meeting_start_time"] = meeting_start_time
        
        action_results.append(action_result)
        
        # Check if this action failed
        if final_schedule_success == "failed":
            failed_actions.append({
                "action_index": i,
                "time_on": time_on,
                "time_off": time_off,
                "target_temp_f": target_temp,
                "error": final_error
            })
        
        # Update total cost
        total_cost_kwh += cost_result["total_cost_kwh"]
        
        # Update current temperature for next iteration
        if final_schedule_success == "success":
            # If successful, assume we reach the target temperature
            current_temp = target_temp
        else:
            # If failed, calculate partial cooling achieved
            # Use the HVAC system to partially cool the room
            duration_minutes = time_diff_minutes(time_on, time_off)
            
            # Calculate what temperature would be achieved with partial cooling
            # This is a simplified approach - in reality you'd need to track the actual cooling
            # For now, estimate based on the time available vs time needed
            time_needed = schedule_result["time_needed_minutes"]
            if time_needed and time_needed > 0:
                # Calculate partial cooling based on time ratio
                cooling_ratio = min(1.0, duration_minutes / time_needed)
                temp_drop_achieved = (current_temp - target_temp) * cooling_ratio
                current_temp = current_temp - temp_drop_achieved
            else:
                # If we can't calculate, use a conservative estimate
                current_temp = current_temp - 2.0  # Assume 2°F cooling achieved
            
            print(f"    Action {i} failed, temp after action: {current_temp:.1f}°F")
    
    # Determine overall plan success
    plan_success = "success" if len(failed_actions) == 0 else "failed"
    
    return {
        "plan_success": plan_success,
        "total_cost_kwh": total_cost_kwh,
        "action_results": action_results,
        "failed_actions": failed_actions,
        "final_temp_f": current_temp
    }


# -------------------------
# Examples: °F inputs
# -------------------------
if __name__ == "__main__":
    # COOLING: 86 → 77 °F (outdoor 95 °F)
    print("Cool + Turbo (86→77, out=95):",
          hvac_time(86, 77, mode="cool", T_out_F=95, use_turbo=True))

    print("Cool + NoTurbo (86→77, out=95):",
          hvac_time(86, 77, mode="cool", T_out_F=95, use_turbo=False))

    # HEATING: 64 → 75 °F (outdoor 50 °F)
    print("Heat + Turbo (64→75, out=50):",
          hvac_time(64, 75, mode="heat", T_out_F=50, use_turbo=True))

    print("Heat + NoTurbo (64→75, out=50):",
          hvac_time(64, 75, mode="heat", T_out_F=50, use_turbo=False))
    
    print("\n" + "="*50)
    print("Temperature Estimation Examples:")
    print("="*50)

    # Example 1: Estimate temperature in 2 hours
    current_temp = 75.0
    outdoor_temp = 95.0
    current_time = "14:00"
    target_time = "15:00"

    estimated_temp = estimate_temp_at_time(
        current_temp, outdoor_temp, current_time, target_time
    )
    print(f"Current: {current_temp}°F at {current_time}, "
          f"Outdoor: {outdoor_temp}°F")
    print(f"Estimated temp at {target_time}: {estimated_temp:.1f}°F")

    # Example 2: Estimate temperature in 4 hours
    target_time = "18:00"
    estimated_temp = estimate_temp_at_time(
        current_temp, outdoor_temp, current_time, target_time
    )
    print(f"Estimated temp at {target_time}: {estimated_temp:.1f}°F")

    # Example 3: Different scenario - cooler outdoor temp
    outdoor_temp = 70.0
    estimated_temp = estimate_temp_at_time(
        current_temp, outdoor_temp, current_time, target_time
    )
    print(f"With cooler outdoor temp ({outdoor_temp}°F): "
          f"{estimated_temp:.1f}°F")
    
    # Example 4: Test constraint with extreme case
    print("\nTesting constraint with extreme case:")
    extreme_outdoor = 50.0  # Very cold outdoor
    extreme_current = 80.0  # Very warm indoor
    estimated_temp = estimate_temp_at_time(
        extreme_current, extreme_outdoor, current_time, target_time,
        max_temp_diff=10.0  # Tighter constraint
    )
    print(f"Extreme case (indoor={extreme_current}°F, outdoor={extreme_outdoor}°F): "
          f"{estimated_temp:.1f}°F")
    
    print("\n" + "="*50)
    print("HVAC Schedule Check Examples:")
    print("="*50)
    
    # Example 1: Success case with turbo
    result = check_hvac_schedule(
        current_temp_f=86.0,
        target_temp_f=77.0,
        use_turbo=True,
        current_time="14:00",
        target_time="15:30",
        mode="cool",
        t_out_f=95.0
    )
    print(f"Success case (86→77°F, turbo, 14:00→15:30):")
    print(f"  Result: {result['reached_temp']}")
    print(f"  Time needed: {result['time_needed_minutes']} min")
    print(f"  Time available: {result['time_available_minutes']} min")
    if result['reached_temp'] == 'success':
        print(f"  Reached at: {result['reached_time']}")
        print(f"  Redundant time: {result['redundant_time_minutes']} min")
    
    # Example 2: Failed case - not enough time
    result = check_hvac_schedule(
        current_temp_f=86.0,
        target_temp_f=77.0,
        use_turbo=False,
        current_time="14:00",
        target_time="14:30",
        mode="cool",
        t_out_f=95.0
    )
    print(f"\nFailed case (86→77°F, no turbo, 14:00→14:30):")
    print(f"  Result: {result['reached_temp']}")
    print(f"  Time needed: {result['time_needed_minutes']} min")
    print(f"  Time available: {result['time_available_minutes']} min")
    if result['error']:
        print(f"  Error: {result['error']}")
    
    # Example 3: Heating case
    result = check_hvac_schedule(
        current_temp_f=64.0,
        target_temp_f=75.0,
        use_turbo=True,
        current_time="08:00",
        target_time="09:00",
        mode="heat",
        t_out_f=50.0
    )
    print(f"\nHeating case (64→75°F, turbo, 08:00→09:00):")
    print(f"  Result: {result['reached_temp']}")
    print(f"  Time needed: {result['time_needed_minutes']} min")
    print(f"  Time available: {result['time_available_minutes']} min")
    if result['reached_temp'] == 'success':
        print(f"  Reached at: {result['reached_time']}")
        print(f"  Redundant time: {result['redundant_time_minutes']} min")
    
    print("\n" + "="*50)
    print("HVAC Plan Cost Calculation Examples:")
    print("="*50)
    
    # Example 1: Simple plan with gaps
    plan1 = [
        {"time_on": "14:00", "time_off": "14:30", "use_turbo": True},
        {"time_on": "15:00", "time_off": "15:45", "use_turbo": False},
        {"time_on": "16:30", "time_off": "17:00", "use_turbo": True}
    ]
    
    result1 = calculate_plan_cost(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan1
    )
    
    print("Plan 1: Multiple actions with gaps")
    print(f"  Total cost: {result1['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result1['final_temp_f']:.1f}°F")
    print("  Action breakdown:")
    for action in result1['action_details']:
        print(f"    Action {action['action_index']}: {action['time_on']}-{action['time_off']} "
              f"({action['duration_minutes']}min, turbo={action['use_turbo']}) "
              f"= {action['cost_kwh']:.3f} kWh")
    
    # Example 2: Continuous plan (no gaps)
    plan2 = [
        {"time_on": "14:00", "time_off": "14:30", "use_turbo": True},
        {"time_on": "14:30", "time_off": "15:15", "use_turbo": False}
    ]
    
    result2 = calculate_plan_cost(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan2
    )
    
    print(f"\nPlan 2: Continuous actions (no gaps)")
    print(f"  Total cost: {result2['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result2['final_temp_f']:.1f}°F")
    
    # Example 3: Test turbo for 60 minutes (exceeds turbo limit)
    plan3 = [
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": True}  # 60 minutes with turbo
    ]
    
    result3 = calculate_plan_cost(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan3
    )
    
    print(f"\nPlan 3: Turbo for 60 minutes (exceeds 30min turbo limit)")
    print(f"  Total cost: {result3['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result3['final_temp_f']:.1f}°F")
    print("  Action breakdown:")
    for action in result3['action_details']:
        print(f"    Action {action['action_index']}: {action['time_on']}-{action['time_off']} "
              f"({action['duration_minutes']}min, turbo={action['use_turbo']}) "
              f"= {action['cost_kwh']:.3f} kWh")
        print(f"      Breakdown: 30min turbo (2600W) + 30min base (2000W)")
        print(f"      Turbo cost: {(2600 * 30) / (1000 * 60):.3f} kWh")
        print(f"      Base cost: {(2000 * 30) / (1000 * 60):.3f} kWh")
    
    print("\n" + "="*50)
    print("HVAC Plan Validation Examples:")
    print("="*50)
    
    # Example 1: Successful plan
    plan_success = [
        {"time_on": "14:00", "time_off": "14:30", "use_turbo": True},
        {"time_on": "15:00", "time_off": "15:45", "use_turbo": False}
    ]
    target_temps_success = [77.0, 75.0]  # Target temperatures for each action
    
    result_success = validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan_success,
        target_temps=target_temps_success
    )
    
    print("Plan Success: Multiple actions with targets")
    print(f"  Overall result: {result_success['plan_success']}")
    print(f"  Total cost: {result_success['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result_success['final_temp_f']:.1f}°F")
    print("  Action details:")
    for action in result_success['action_results']:
        print(f"    Action {action['action_index']}: {action['time_on']}-{action['time_off']} "
              f"target={action['target_temp_f']}°F, result={action['schedule_success']}")
        if action['schedule_success'] == 'success':
            print(f"      Reached at: {action['reached_time']}, "
                  f"redundant: {action['redundant_time_minutes']} min")
        else:
            print(f"      Error: {action['error']}")
    
    # Example 2: Failed plan (unrealistic targets)
    plan_fail = [
        {"time_on": "14:00", "time_off": "14:15", "use_turbo": False},  # Only 15 min, no turbo
        {"time_on": "14:30", "time_off": "14:45", "use_turbo": False}   # Only 15 min, no turbo
    ]
    target_temps_fail = [70.0, 65.0]  # Very aggressive targets
    
    result_fail = validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan_fail,
        target_temps=target_temps_fail
    )
    
    print(f"\nPlan Fail: Unrealistic targets")
    print(f"  Overall result: {result_fail['plan_success']}")
    print(f"  Total cost: {result_fail['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result_fail['final_temp_f']:.1f}°F")
    print(f"  Failed actions: {len(result_fail['failed_actions'])}")
    for failed in result_fail['failed_actions']:
        print(f"    Action {failed['action_index']}: {failed['time_on']}-{failed['time_off']} "
              f"target={failed['target_temp_f']}°F - {failed['error']}")
    
    # Example 3: Successful plan with realistic targets and enough time
    plan_success_real = [
        {"time_on": "14:00", "time_off": "15:00", "use_turbo": True},  # 60 min with turbo
        {"time_on": "15:30", "time_off": "16:45", "use_turbo": False}  # 75 min base (more time)
    ]
    target_temps_success_real = [80.0, 78.0]  # More realistic targets
    
    result_success_real = validate_plan_success(
        current_indoor_temp_f=86.0,
        outdoor_temp_f=95.0,
        current_time="13:30",
        plan=plan_success_real,
        target_temps=target_temps_success_real
    )
    
    print(f"\nPlan Success Real: Realistic targets with enough time")
    print(f"  Overall result: {result_success_real['plan_success']}")
    print(f"  Total cost: {result_success_real['total_cost_kwh']:.3f} kWh")
    print(f"  Final temp: {result_success_real['final_temp_f']:.1f}°F")
    print("  Action details:")
    for action in result_success_real['action_results']:
        print(f"    Action {action['action_index']}: {action['time_on']}-{action['time_off']} "
              f"target={action['target_temp_f']}°F, result={action['schedule_success']}")
        if action['schedule_success'] == 'success':
            print(f"      Reached at: {action['reached_time']}, "
                  f"redundant: {action['redundant_time_minutes']} min")
        else:
            print(f"      Error: {action['error']}")
