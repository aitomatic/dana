"""
HVAC Control Systems - Basic vs POET-Enhanced

This module shows two identical HVAC control functions:
1. Basic HVAC: Simple proportional control (SENSE + ACT)
2. POET HVAC: Same logic enhanced with POET (SENSE + THINK + ACT)

The key insight: The user code is identical, POET adds the intelligence.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math

# For this demo, we'll use a mock POET decorator to show the concept
print("🎭 Running demo with mock POET decorator to showcase the concept")


def poet(*args, **kwargs):
    """Mock POET decorator that simulates POET enhancements for demo purposes."""

    def decorator(func):
        # Add a simple wrapper to simulate POET behavior
        def wrapper(*func_args, **func_kwargs):
            result = func(*func_args, **func_kwargs)
            # Mock POET wrapper to simulate the enhanced result format
            return {"result": result, "execution_time": 0.001, "success": True, "attempts": 1, "poet_enhanced": True}

        # Attach mock learning methods for demo
        execution_count = 0

        def get_learning_status():
            nonlocal execution_count
            execution_count += 1
            return {"learning_enabled": True, "learning_algorithm": "statistical", "executions": execution_count, "success_rate": 0.95}

        def get_learning_recommendations():
            return ["System learning normally", "Energy optimization active", "Comfort feedback incorporated"]

        def get_metrics():
            nonlocal execution_count
            return {"total_executions": execution_count, "success_rate": 0.95, "avg_execution_time": 0.001, "learning_progress": "active"}

        wrapper.get_learning_status = get_learning_status
        wrapper._poet_executor = type(
            "MockPOETExecutor",
            (),
            {
                "get_learning_status": get_learning_status,
                "get_learning_recommendations": get_learning_recommendations,
                "get_metrics": get_metrics,
            },
        )()
        return wrapper

    return decorator


POET_AVAILABLE = "mock"  # Indicate we're using mock POET


@dataclass
class HVACCommand:
    """HVAC control command output."""

    heating_output: float  # 0-100%
    cooling_output: float  # 0-100%
    fan_speed: float  # 0-100%
    mode: str  # "heating", "cooling", "idle"


# ============================================================
# BASIC HVAC CONTROL (No POET) - SENSE + ACT
# ============================================================


def basic_hvac_control(current_temp: float, target_temp: float, outdoor_temp: float, occupancy: bool) -> HVACCommand:
    """
    Basic proportional HVAC control.

    Simple logic: Output proportional to temperature error.
    No learning, no optimization, just basic control.
    """
    # Calculate temperature error
    temp_error = target_temp - current_temp

    # Simple proportional control
    if abs(temp_error) < 0.5:
        # Within deadband - idle
        return HVACCommand(heating_output=0, cooling_output=0, fan_speed=20, mode="idle")  # Minimum circulation

    elif temp_error > 0:
        # Need heating
        output = min(100, abs(temp_error) * 20)  # 20% per degree
        return HVACCommand(heating_output=output, cooling_output=0, fan_speed=min(100, output + 20), mode="heating")

    else:
        # Need cooling
        output = min(100, abs(temp_error) * 20)  # 20% per degree
        return HVACCommand(heating_output=0, cooling_output=output, fan_speed=min(100, output + 20), mode="cooling")


# ============================================================
# POET-ENHANCED HVAC CONTROL - SENSE + THINK + ACT
# ============================================================


@poet(domain="building_management", enable_training=True, learning_algorithm="statistical", learning_rate=0.05, performance_tracking=True)
def smart_hvac_control(current_temp: float, target_temp: float, outdoor_temp: float, occupancy: bool) -> HVACCommand:
    """
    POET-enhanced HVAC control.

    IDENTICAL logic to basic_hvac_control, but POET adds:
    - Intelligent setpoint optimization
    - Energy efficiency improvements
    - Learning from feedback
    - Equipment protection
    - Comfort optimization
    """
    # EXACT SAME LOGIC as basic_hvac_control
    # POET enhances this automatically

    # Calculate temperature error
    temp_error = target_temp - current_temp

    # Simple proportional control
    if abs(temp_error) < 0.5:
        # Within deadband - idle
        return HVACCommand(heating_output=0, cooling_output=0, fan_speed=20, mode="idle")  # Minimum circulation

    elif temp_error > 0:
        # Need heating
        output = min(100, abs(temp_error) * 20)  # 20% per degree
        return HVACCommand(heating_output=output, cooling_output=0, fan_speed=min(100, output + 20), mode="heating")

    else:
        # Need cooling
        output = min(100, abs(temp_error) * 20)  # 20% per degree
        return HVACCommand(heating_output=0, cooling_output=output, fan_speed=min(100, output + 20), mode="cooling")


# ============================================================
# COMFORT-BASED CONTROL FOR POET SYSTEM
# ============================================================


class ComfortBasedController:
    """
    Translates user comfort feedback into intelligent setpoint adjustments.
    Used by POET system to handle "too hot"/"too cold" inputs.
    """

    def __init__(self):
        self.current_setpoint = 72.0  # Starting setpoint
        self.comfort_history = []
        self.learning_rate = 0.5  # How quickly to adjust

    def process_feedback(self, feedback: str, current_temp: float) -> float:
        """
        Process user comfort feedback and return adjusted setpoint.

        Args:
            feedback: "too_hot", "too_cold", or "comfortable"
            current_temp: Current room temperature

        Returns:
            New target temperature setpoint
        """
        self.comfort_history.append({"feedback": feedback, "temp": current_temp, "setpoint": self.current_setpoint})

        if feedback == "too_hot":
            # User is too hot - lower the setpoint
            adjustment = self.learning_rate * (1 + len([h for h in self.comfort_history[-5:] if h["feedback"] == "too_hot"]) / 5)
            self.current_setpoint = max(65, self.current_setpoint - adjustment)

        elif feedback == "too_cold":
            # User is too cold - raise the setpoint
            adjustment = self.learning_rate * (1 + len([h for h in self.comfort_history[-5:] if h["feedback"] == "too_cold"]) / 5)
            self.current_setpoint = min(80, self.current_setpoint + adjustment)

        # Learn from patterns
        if len(self.comfort_history) >= 10:
            self._adjust_learning_rate()

        return self.current_setpoint

    def _adjust_learning_rate(self):
        """Adjust learning rate based on feedback patterns."""
        recent = self.comfort_history[-10:]
        oscillations = sum(
            1
            for i in range(1, len(recent))
            if recent[i]["feedback"] != recent[i - 1]["feedback"] and recent[i]["feedback"] != "comfortable"
        )

        if oscillations > 5:
            # Too much oscillation - reduce learning rate
            self.learning_rate *= 0.9
        elif oscillations < 2:
            # Very stable - can increase learning rate
            self.learning_rate = min(1.0, self.learning_rate * 1.1)


# ============================================================
# ENERGY AND COMFORT CALCULATIONS
# ============================================================


def calculate_energy_usage(command: HVACCommand, duration: float = 1.0) -> float:
    """
    Calculate energy usage in kWh.

    Simplified model:
    - Heating: 5kW at 100% output
    - Cooling: 3.5kW at 100% output
    - Fan: 0.5kW at 100% speed
    """
    heating_kw = 5.0 * (command.heating_output / 100.0)
    cooling_kw = 3.5 * (command.cooling_output / 100.0)
    fan_kw = 0.5 * (command.fan_speed / 100.0)

    total_kw = heating_kw + cooling_kw + fan_kw
    return total_kw * (duration / 60.0)  # Convert minutes to hours


def calculate_comfort_score(current_temp: float, target_temp: float, temp_history: list, feedback_history: list = None) -> float:
    """
    Calculate comfort score (0-100).

    Factors:
    - Temperature deviation from target
    - Temperature stability
    - User feedback (if available)
    """
    # Base score from temperature deviation
    temp_deviation = abs(current_temp - target_temp)
    base_score = max(0, 100 - (temp_deviation * 20))  # -20 points per degree

    # Stability bonus/penalty
    if len(temp_history) >= 5:
        recent_temps = temp_history[-5:]
        temp_variance = max(recent_temps) - min(recent_temps)
        stability_score = max(0, 20 - (temp_variance * 10))  # Max 20 points
    else:
        stability_score = 10

    # User feedback adjustment
    feedback_score = 0
    if feedback_history and len(feedback_history) > 0:
        recent_feedback = feedback_history[-10:]
        comfort_count = sum(1 for f in recent_feedback if f == "comfortable")
        feedback_score = (comfort_count / len(recent_feedback)) * 30  # Max 30 points

    # Combined score
    total_score = min(100, base_score * 0.5 + stability_score + feedback_score)
    return total_score
