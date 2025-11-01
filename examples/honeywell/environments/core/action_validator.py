#!/usr/bin/env python3
"""
Action validation and cost calculation for HVAC plans.

Extracted from room_feedback.py - exact logic preserved.
Validates HVAC action plans with meeting-aware logic and cost tracking.
"""

from typing import Optional
from .config import EnvironmentConfig, Mode
from .thermal_physics import ThermalPhysics


class ActionValidator:
    """
    Validates HVAC action plans and calculates costs.

    Features:
    - Multi-action plan validation
    - Gap temperature tracking between actions
    - Energy cost calculation (kWh)
    - Meeting-aware validation
    - Wasted energy detection
    - Partial cooling calculation on failure
    """

    def __init__(self, physics: ThermalPhysics, config: EnvironmentConfig):
        """
        Initialize validator.

        Args:
            physics: ThermalPhysics engine for calculations
            config: Environment configuration
        """
        self.physics = physics
        self.config = config

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

    @staticmethod
    def _time_diff_minutes(start_time: str, end_time: str) -> int:
        """Calculate time difference in minutes."""
        start_min = ActionValidator._parse_time(start_time)
        end_min = ActionValidator._parse_time(end_time)
        diff = end_min - start_min
        if diff < 0:
            diff += 24 * 60  # Next day
        return diff

    def calculate_plan_cost(
        self,
        current_indoor_temp_f: float,
        outdoor_temp_f: float,
        current_time: str,
        plan: list[dict],
        mode: Mode = "cool"
    ) -> dict:
        """
        Calculate electricity cost for HVAC action plan.

        Handles:
        - Gap detection between actions
        - Temperature evolution during gaps
        - Turbo/base power consumption
        - Per-action and total cost

        Args:
            current_indoor_temp_f: Current indoor temperature (°F)
            outdoor_temp_f: Outdoor temperature (°F)
            current_time: Current time in HH:MM format
            plan: List of action dicts with time_on, time_off, use_turbo
            mode: "cool" or "heat"

        Returns:
            Dictionary with:
            - total_cost_kwh: Total electricity consumption (kWh)
            - action_details: List of per-action details
            - final_temp_f: Final temperature after all actions
        """
        current_temp = current_indoor_temp_f
        total_cost_kwh = 0.0
        action_details = []

        for i, action in enumerate(plan):
            time_on = action["time_on"]
            time_off = action["time_off"]
            use_turbo = action["use_turbo"]

            # Check for gap between previous action and current action
            if i > 0:
                prev_action = plan[i - 1]
                prev_time_off = prev_action["time_off"]

                # If there's a gap, estimate temperature change during off period
                if prev_time_off != time_on:
                    print(f"    Gap detected: {prev_time_off} to {time_on}")
                    print(f"    Estimating temp change from {current_temp:.1f}°F...")
                    gap_duration = self._time_diff_minutes(prev_time_off, time_on)
                    gap_temp = self.physics.estimate_temp_at_time(
                        current_temp, outdoor_temp_f, gap_duration
                    )
                    print(f"    Estimated temp after gap: {gap_temp:.1f}°F")
                    current_temp = gap_temp
                else:
                    print(f"    No gap: {prev_time_off} = {time_on}")

            # Calculate action duration
            duration_minutes = self._time_diff_minutes(time_on, time_off)

            # Calculate power consumption for this action
            if use_turbo:
                # Turbo phase (up to turbo_max_minutes) + base phase
                turbo_duration = min(duration_minutes, self.config.hvac_config.turbo_max_minutes)
                base_duration = max(0, duration_minutes - self.config.hvac_config.turbo_max_minutes)

                turbo_cost_kwh = (self.config.hvac_config.turbo_capacity_w * turbo_duration) / (1000 * 60)
                base_cost_kwh = (self.config.hvac_config.base_capacity_w * base_duration) / (1000 * 60)
                total_action_cost_kwh = turbo_cost_kwh + base_cost_kwh
            else:
                # Base power only
                total_action_cost_kwh = (self.config.hvac_config.base_capacity_w * duration_minutes) / (1000 * 60)

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

            # Estimate temperature after this action for next iteration
            if i < len(plan) - 1:  # Not the last action
                next_action = plan[i + 1]
                next_time_on = next_action["time_on"]
                gap_duration = self._time_diff_minutes(time_off, next_time_on)
                current_temp = self.physics.estimate_temp_at_time(
                    current_temp, outdoor_temp_f, gap_duration
                )

        return {
            "total_cost_kwh": total_cost_kwh,
            "action_details": action_details,
            "final_temp_f": current_temp
        }

    def validate_plan_success(
        self,
        current_indoor_temp_f: float,
        outdoor_temp_f: float,
        current_time: str,
        plan: list[dict],
        target_temps: list[float],
        mode: Mode = "cool",
        meeting_plan: Optional[list[dict]] = None
    ) -> dict:
        """
        Validate complete HVAC action plan.

        Features:
        - Multi-action sequence validation
        - Gap temperature tracking
        - Meeting-aware validation (if meeting_plan provided)
        - Partial cooling calculation on failure
        - Wasted energy detection

        Args:
            current_indoor_temp_f: Current indoor temperature (°F)
            outdoor_temp_f: Outdoor temperature (°F)
            current_time: Current time in HH:MM format
            plan: List of action dicts with time_on, time_off, use_turbo
            target_temps: List of target temperatures for each action
            mode: "cool" or "heat"
            meeting_plan: Optional list of meetings with start_time and end_time

        Returns:
            Dictionary with:
            - plan_success: "success" or "failed"
            - total_cost_kwh: Total electricity consumption
            - action_results: List of detailed results per action
            - failed_actions: List of actions that failed
            - final_temp_f: Final temperature after all actions
        """
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
                prev_action = plan[i - 1]
                prev_time_off = prev_action["time_off"]

                # If there's a gap, estimate temperature change during off period
                if prev_time_off != time_on:
                    print(f"    Gap detected: {prev_time_off} to {time_on}")
                    print(f"    Temp before gap: {current_temp:.1f}°F")
                    gap_duration = self._time_diff_minutes(prev_time_off, time_on)
                    gap_temp = self.physics.estimate_temp_at_time(
                        current_temp, outdoor_temp_f, gap_duration
                    )
                    print(f"    Temp after gap: {gap_temp:.1f}°F")
                    current_temp = gap_temp

            # CRITICAL VALIDATION: If this action starts at a meeting time,
            # the target temperature must already be reached BEFORE the meeting starts
            if time_on in meeting_start_times:
                # Check if current temperature already meets target
                if mode == "cool" and current_temp > target_temp:
                    # Need to cool but haven't reached target yet
                    error_msg = (f"Meeting starts at {time_on} but room is {current_temp:.1f}°F "
                                f"(target: {target_temp}°F). HVAC should have turned on earlier!")
                    failed_action = {
                        "action_index": i,
                        "time_on": time_on,
                        "time_off": time_off,
                        "target_temp_f": target_temp,
                        "error": error_msg
                    }
                    failed_actions.append(failed_action)

                    # Still calculate cost for this action
                    cost_result = self.calculate_plan_cost(
                        current_indoor_temp_f=current_temp,
                        outdoor_temp_f=outdoor_temp_f,
                        current_time=time_on,
                        plan=[action],
                        mode=mode
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
                    continue

                elif mode == "heat" and current_temp < target_temp:
                    # Need to heat but haven't reached target yet
                    error_msg = (f"Meeting starts at {time_on} but room is {current_temp:.1f}°F "
                                f"(target: {target_temp}°F). HVAC should have turned on earlier!")
                    failed_action = {
                        "action_index": i,
                        "time_on": time_on,
                        "time_off": time_off,
                        "target_temp_f": target_temp,
                        "error": error_msg
                    }
                    failed_actions.append(failed_action)

                    # Still calculate cost for this action
                    cost_result = self.calculate_plan_cost(
                        current_indoor_temp_f=current_temp,
                        outdoor_temp_f=outdoor_temp_f,
                        current_time=time_on,
                        plan=[action],
                        mode=mode
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
                    continue

            # Check if this action can reach target temperature
            time_available_minutes = self._time_diff_minutes(time_on, time_off)
            schedule_result = self.physics.check_hvac_schedule(
                current_temp_f=current_temp,
                target_temp_f=target_temp,
                time_available_minutes=time_available_minutes,
                outdoor_temp_f=outdoor_temp_f,
                mode=mode,
                use_turbo=use_turbo
            )

            # Calculate cost for this action
            cost_result = self.calculate_plan_cost(
                current_indoor_temp_f=current_temp,
                outdoor_temp_f=outdoor_temp_f,
                current_time=time_on,
                plan=[action],
                mode=mode
            )

            # Find the closest meeting start time for this action
            meeting_start_time = None
            if meeting_plan:
                # Find the meeting that starts closest to this action's time_on
                time_on_min = self._parse_time(time_on)
                closest_meeting = None
                min_diff = float('inf')

                for meeting in meeting_plan:
                    meeting_start_min = self._parse_time(meeting["start_time"])
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
                    schedule_result.get("time_needed_minutes") is not None):

                # Calculate reached_time
                reached_minutes = self._parse_time(time_on) + schedule_result["time_needed_minutes"]
                if reached_minutes >= 24 * 60:
                    reached_minutes -= 24 * 60
                reached_time = self._minutes_to_time(reached_minutes)

                # Parse times to compare reached time with meeting start time
                reached_minutes = self._parse_time(reached_time)
                meeting_start_minutes = self._parse_time(meeting_start_time)

                # If reached time is after meeting start time, mark as failed
                if reached_minutes > meeting_start_minutes:
                    final_schedule_success = "failed"
                    final_error = (f"Target reached at {reached_time} "
                                  f"but meeting starts at {meeting_start_time}. "
                                  f"HVAC should have started earlier to reach target "
                                  f"before meeting begins.")
                else:
                    # Success case - check if there's wasted energy time
                    meeting_time_diff_minutes = meeting_start_minutes - reached_minutes
                    if meeting_time_diff_minutes > 5:  # More than 5 minutes early
                        final_error = (f"Target reached at {reached_time}, "
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
                "reached_time": self._minutes_to_time(
                    self._parse_time(time_on) + schedule_result["time_needed_minutes"]
                ) if schedule_result["time_needed_minutes"] is not None else None,
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
                time_needed = schedule_result["time_needed_minutes"]
                duration_minutes = self._time_diff_minutes(time_on, time_off)

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
