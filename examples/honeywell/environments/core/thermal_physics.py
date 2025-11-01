#!/usr/bin/env python3
"""
Thermal physics engine for HVAC simulation.

Consolidates physics calculations from ac_test.py and room_feedback.py.
Configurable via HVACConfig and ThermalConfig to support multiple HVAC profiles.
"""

import math
from .config import HVACConfig, ThermalConfig, Mode


class ThermalPhysics:
    """
    Pure thermal dynamics engine.

    Implements exponential temperature evolution model with:
    - Thermal time constant (τ)
    - Steady-state temperature calculation
    - HVAC heating/cooling with turbo mode
    - Temperature estimation during off periods
    """

    def __init__(
        self,
        hvac_config: HVACConfig,
        thermal_config: ThermalConfig,
        verbose: bool = False
    ):
        """
        Initialize physics engine with configuration.

        Args:
            hvac_config: HVAC system specifications
            thermal_config: Building thermal properties
            verbose: Enable debug prints (matches room_feedback.py behavior)
        """
        self.hvac = hvac_config
        self.thermal = thermal_config
        self.verbose = verbose

    # ===== Helper Functions =====

    @staticmethod
    def _f_to_c(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32.0) * 5.0 / 9.0

    @staticmethod
    def _c_to_f(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return celsius * 9.0 / 5.0 + 32.0

    @staticmethod
    def _parse_time(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    @staticmethod
    def _minutes_to_time(minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    # ===== Core Physics Functions =====

    def _tau_minutes(self, ua_effective: float) -> float:
        """
        Calculate thermal time constant in minutes.

        τ = C / UA_eff (in seconds), converted to minutes.
        """
        return (self.thermal.thermal_mass_j_k / ua_effective) / 60.0

    def _t_inf(
        self,
        t_outdoor_c: float,
        ua_effective: float,
        q_internal: float,
        q_hvac: float
    ) -> float:
        """
        Calculate steady-state temperature.

        T_inf = T_outdoor + (Q_internal + Q_HVAC) / UA_eff
        """
        return t_outdoor_c + (q_internal + q_hvac) / ua_effective

    def _time_to_target_minutes(
        self,
        t_start_c: float,
        t_target_c: float,
        t_inf_c: float,
        tau_minutes: float
    ) -> float:
        """
        Calculate time to reach target temperature using exponential model.

        Includes fallback calculation for edge cases where ratio <= 0.
        Enforces minimum temperature limit of 60°F (15.56°C).
        """
        num = t_target_c - t_inf_c
        den = t_start_c - t_inf_c

        if num == 0:
            return 0.0

        ratio = num / den

        # Minimum achievable temperature check (60°F = 15.56°C)
        min_achievable_c = 15.56
        if t_target_c < min_achievable_c:
            raise ValueError("Target below 60°F minimum.")

        # Fallback calculation for edge cases (ratio <= 0)
        if ratio <= 0:
            temp_diff = abs(t_target_c - t_start_c)

            # More realistic calculation:
            # - Base time: 5 minutes per degree
            # - Difficulty factor: exponential for larger drops
            # - Minimum: 30 min, Maximum: 300 min
            base_time = temp_diff * 5.0

            # Add difficulty factor for larger temperature changes
            if temp_diff > 5:
                difficulty_factor = 1.0 + (temp_diff - 5) * 0.2
                base_time *= difficulty_factor

            time_estimate = max(30.0, min(300.0, base_time))

            # Debug print if verbose (room_feedback.py style)
            if self.verbose:
                temp_diff_f = temp_diff * 9.0 / 5.0
                print(f"      Fallback calculation: {self._c_to_f(t_start_c):.1f}°F → "
                      f"{self._c_to_f(t_target_c):.1f}°F, diff={temp_diff_f:.1f}°F, "
                      f"time={time_estimate:.0f}min")

            return time_estimate

        # Normal exponential calculation
        result = -tau_minutes * math.log(ratio)

        # Debug print if verbose (room_feedback.py style)
        if self.verbose:
            print(f"      Normal calculation: {self._c_to_f(t_start_c):.1f}°F → "
                  f"{self._c_to_f(t_target_c):.1f}°F, ratio={ratio:.3f}, "
                  f"time={result:.0f}min")
            print(f"        Current: {self._c_to_f(t_start_c):.1f}°F, "
                  f"Target: {self._c_to_f(t_target_c):.1f}°F, "
                  f"Tinf: {self._c_to_f(t_inf_c):.1f}°F")

        return result

    def _advance_temperature(
        self,
        t_start_c: float,
        duration_minutes: float,
        t_inf_c: float,
        tau_minutes: float
    ) -> float:
        """
        Calculate temperature after given time duration.

        T(t) = T_inf + (T_0 - T_inf) * exp(-t / τ)
        """
        return t_inf_c + (t_start_c - t_inf_c) * math.exp(-duration_minutes / tau_minutes)

    # ===== Public API =====

    def hvac_time(
        self,
        current_temp_f: float,
        target_temp_f: float,
        outdoor_temp_f: float,
        mode: Mode = "cool",
        use_turbo: bool = False
    ) -> int:
        """
        Calculate time (minutes) to reach target temperature from current temperature.

        Handles:
        - Turbo phase (up to turbo_max_minutes) then base phase
        - Both cooling and heating modes
        - Exponential temperature approach

        Args:
            current_temp_f: Current indoor temperature (°F)
            target_temp_f: Target temperature (°F)
            outdoor_temp_f: Outdoor temperature (°F)
            mode: "cool" or "heat"
            use_turbo: Whether to use turbo mode

        Returns:
            Time in minutes (rounded to integer)

        Raises:
            ValueError: If target temperature is unreachable (< 60°F)
        """
        # Convert to Celsius for calculations
        t_current_c = self._f_to_c(current_temp_f)
        t_target_c = self._f_to_c(target_temp_f)
        t_outdoor_c = self._f_to_c(outdoor_temp_f)

        # Calculate effective UA with fan boost
        ua_eff = self.thermal.heat_transfer_coeff_w_k * self.thermal.fan_boost_multiplier
        tau_min = self._tau_minutes(ua_eff)

        # HVAC power (negative for cooling, positive for heating)
        sign = -1.0 if mode == "cool" else 1.0
        q_base = sign * self.hvac.base_capacity_w
        q_turbo = sign * self.hvac.turbo_capacity_w

        def _check(t_start, t_goal, q_hvac):
            """Helper to check if target is reachable and calculate time."""
            t_inf = self._t_inf(t_outdoor_c, ua_eff, self.thermal.internal_heat_w, q_hvac)

            if (t_goal - t_start) == 0:
                return t_inf, 0.0

            # Minimum achievable check
            min_achievable_c = 15.56  # 60°F
            if t_goal < min_achievable_c:
                raise ValueError(f"Target {target_temp_f}°F unreachable (below 60°F minimum).")

            time_needed = self._time_to_target_minutes(t_start, t_goal, t_inf, tau_min)
            return t_inf, time_needed

        total_min = 0.0
        t_curr = t_current_c

        # Phase A: Turbo (up to turbo_max_minutes)
        if use_turbo:
            t_inf_turbo, t_need_turbo = _check(t_curr, t_target_c, q_turbo)
            if t_need_turbo <= self.hvac.turbo_max_minutes:
                return int(round(t_need_turbo))

            # Run turbo for max duration, then continue with base
            t_curr = self._advance_temperature(
                t_curr, self.hvac.turbo_max_minutes, t_inf_turbo, tau_min
            )
            total_min += self.hvac.turbo_max_minutes

        # Phase B: Base power
        _, t_need_base = _check(t_curr, t_target_c, q_base)
        total_min += t_need_base

        return int(round(total_min))

    def estimate_temp_at_time(
        self,
        current_indoor_temp_f: float,
        current_outdoor_temp_f: float,
        duration_minutes: int,
        max_temp_diff_f: float = 15.0
    ) -> float:
        """
        Estimate indoor temperature after duration with no HVAC running.

        Args:
            current_indoor_temp_f: Current indoor temperature (°F)
            current_outdoor_temp_f: Current outdoor temperature (°F)
            duration_minutes: Time duration in minutes
            max_temp_diff_f: Maximum allowed difference from outdoor temp (°F)

        Returns:
            Estimated indoor temperature (°F)
        """
        # Convert to Celsius
        t_indoor_c = self._f_to_c(current_indoor_temp_f)
        t_outdoor_c = self._f_to_c(current_outdoor_temp_f)

        # Calculate thermal properties
        ua_eff = self.thermal.heat_transfer_coeff_w_k * self.thermal.fan_boost_multiplier
        tau_min = self._tau_minutes(ua_eff)

        # Calculate steady-state temperature without HVAC (Q_HVAC = 0)
        t_inf_c = self._t_inf(t_outdoor_c, ua_eff, self.thermal.internal_heat_w, 0.0)

        # Estimate temperature evolution
        t_estimated_c = self._advance_temperature(t_indoor_c, duration_minutes, t_inf_c, tau_min)

        # Convert back to Fahrenheit
        estimated_temp_f = self._c_to_f(t_estimated_c)

        # Constrain result within ±max_temp_diff of outdoor temperature
        min_estimated = current_outdoor_temp_f - max_temp_diff_f
        max_estimated = current_outdoor_temp_f + max_temp_diff_f
        constrained_temp = max(min_estimated, min(estimated_temp_f, max_estimated))

        return constrained_temp

    def check_hvac_schedule(
        self,
        current_temp_f: float,
        target_temp_f: float,
        time_available_minutes: int,
        outdoor_temp_f: float,
        mode: Mode = "cool",
        use_turbo: bool = False
    ) -> dict:
        """
        Check if HVAC can reach target temperature within available time.

        Args:
            current_temp_f: Current indoor temperature (°F)
            target_temp_f: Target temperature (°F)
            time_available_minutes: Time available (minutes)
            outdoor_temp_f: Outdoor temperature (°F)
            mode: "cool" or "heat"
            use_turbo: Whether to use turbo mode

        Returns:
            Dictionary with:
            - reached_temp: "success" or "failed"
            - time_needed_minutes: Time needed to reach target
            - time_available_minutes: Time available
            - redundant_time_minutes: Extra time if successful (None if failed)
            - error: Error message if failed (None if successful)
        """
        # Calculate time needed using hvac_time
        try:
            time_needed_minutes = self.hvac_time(
                current_temp_f, target_temp_f, outdoor_temp_f, mode, use_turbo
            )
        except ValueError as e:
            # Target temperature is unreachable (physically impossible)
            return {
                "reached_temp": "failed",
                "time_needed_minutes": None,
                "time_available_minutes": time_available_minutes,
                "redundant_time_minutes": None,
                "error": str(e)
            }

        # Check if we can reach target in time
        if time_needed_minutes <= time_available_minutes:
            # Success case
            redundant_time = time_available_minutes - time_needed_minutes
            return {
                "reached_temp": "success",
                "time_needed_minutes": time_needed_minutes,
                "time_available_minutes": time_available_minutes,
                "redundant_time_minutes": redundant_time,
                "error": None
            }
        else:
            # Failed case - not enough time
            error_msg = (f"Need {time_needed_minutes} min to cool down, "
                        f"only {time_available_minutes} min available.")
            return {
                "reached_temp": "failed",
                "time_needed_minutes": time_needed_minutes,
                "time_available_minutes": time_available_minutes,
                "redundant_time_minutes": None,
                "error": error_msg
            }
