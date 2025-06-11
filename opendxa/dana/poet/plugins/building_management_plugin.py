"""
Building Management Plugin for POET

Provides domain-specific intelligence for HVAC and building management systems,
including thermal optimization, equipment protection, and energy efficiency.

Author: OpenDXA Team
Version: 1.0.0
"""

from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
from datetime import datetime

from opendxa.dana.poet.plugins.base import POETPlugin
from opendxa.dana.poet.learning.objective import ObjectiveEvaluator, EvaluationContext


@dataclass
class HVACCommand:
    """HVAC control command output."""

    heating_output: float  # 0-100%
    cooling_output: float  # 0-100%
    fan_speed: float  # 0-100%
    status: str  # Status message


class BuildingManagementPlugin(POETPlugin):
    """Domain plugin for HVAC and building management systems."""

    __version__ = "1.0.0"
    __author__ = "OpenDXA Team"

    def __init__(self):
        self.thermal_models = {}
        self.equipment_constraints = {
            "min_temp": 60,
            "max_temp": 85,
            "min_humidity": 30,
            "max_humidity": 70,
            "max_temp_change_rate": 2.0,  # degrees per hour
        }
        self.energy_optimization_enabled = True

        # Learning-specific attributes
        self.learning_enabled = True
        self.feedback_history = deque(maxlen=100)  # Store recent feedback
        self.performance_metrics = deque(maxlen=50)  # Store performance scores

        # Learnable parameters (with defaults)
        self.learnable_params = {
            "energy_setback_degrees": 3.0,  # Energy-saving setback when unoccupied
            "deadband_multiplier": 1.0,  # Thermal deadband adjustment
            "heating_aggressiveness": 1.0,  # How aggressively to heat
            "cooling_aggressiveness": 1.0,  # How aggressively to cool
            "comfort_tolerance": 1.0,  # Temperature tolerance
            "energy_priority_weight": 0.8,  # Balance between comfort and energy
        }

        # Learning statistics
        self.learning_stats = {
            "feedback_count": 0,
            "parameter_updates": 0,
            "performance_trend": "stable",
            "last_update": None,
        }

        # Objective evaluation
        self.objective_evaluator = ObjectiveEvaluator()

    def get_plugin_name(self) -> str:
        """Get unique plugin identifier."""
        return "building_management"

    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """Process HVAC control inputs with building intelligence."""

        # Extract common HVAC parameters
        if len(args) >= 4:
            # Standard HVAC function signature: (current_temp, setpoint, occupancy, outdoor_temp)
            current_temp, setpoint, occupancy, outdoor_temp = args[:4]
        else:
            # Extract from kwargs or use defaults
            current_temp = kwargs.get("current_temp", args[0] if len(args) > 0 else 72.0)
            setpoint = kwargs.get("setpoint", args[1] if len(args) > 1 else 72.0)
            occupancy = kwargs.get("occupancy", args[2] if len(args) > 2 else True)
            outdoor_temp = kwargs.get("outdoor_temp", args[3] if len(args) > 3 else 70.0)

        # Apply building management intelligence
        enhanced_inputs = {
            "current_temp": self._validate_temperature(current_temp),
            "setpoint": self._optimize_setpoint(setpoint, occupancy),
            "occupancy": occupancy,
            "outdoor_temp": self._validate_temperature(outdoor_temp),
            "thermal_context": self._get_thermal_context(
                {"current_temp": current_temp, "setpoint": setpoint, "occupancy": occupancy, "outdoor_temp": outdoor_temp}
            ),
        }

        return {
            "args": (
                enhanced_inputs["current_temp"],
                enhanced_inputs["setpoint"],
                enhanced_inputs["occupancy"],
                enhanced_inputs["outdoor_temp"],
            ),
            "kwargs": {},
        }

    def validate_output(self, result: Any, context: Dict[str, Any]) -> Any:
        """Validate HVAC control output for safety and efficiency."""

        # Validate output is reasonable control command
        if hasattr(result, "heating_output"):
            if not (0 <= result.heating_output <= 100):
                raise ValueError(f"Invalid heating output: {result.heating_output}%")

        if hasattr(result, "cooling_output"):
            if not (0 <= result.cooling_output <= 100):
                raise ValueError(f"Invalid cooling output: {result.cooling_output}%")

        if hasattr(result, "fan_speed"):
            if not (0 <= result.fan_speed <= 100):
                raise ValueError(f"Invalid fan speed: {result.fan_speed}%")

        # Equipment protection: prevent simultaneous heating and cooling
        if (
            hasattr(result, "heating_output")
            and hasattr(result, "cooling_output")
            and result.heating_output > 10
            and result.cooling_output > 10
        ):
            raise ValueError("Equipment protection: Cannot heat and cool simultaneously")

        # Energy efficiency check
        if self.energy_optimization_enabled:
            result = self._apply_energy_optimization(result, context)

        return result

    def get_performance_optimizations(self) -> Dict[str, Any]:
        """Get HVAC-specific performance optimizations."""
        return {
            "timeout_multiplier": 1.2,  # HVAC operations may take slightly longer
            "retry_strategy": "exponential",
            "cache_enabled": False,  # Real-time data, don't cache
            "batch_size": 1,  # Process each HVAC command individually
        }

    def get_learning_hints(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide HVAC-specific learning guidance."""
        return {
            "parameter_bounds": {
                "timeout": (5.0, 60.0),  # HVAC operations: 5-60 seconds
                "setpoint_tolerance": (0.5, 3.0),  # Temperature tolerance in degrees
            },
            "learning_rate": 0.03,  # Conservative learning for safety
            "convergence_threshold": 0.05,  # Higher threshold for stability
            "performance_weight": 0.8,  # Prioritize performance over speed
        }

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get enhanced plugin information."""
        base_info = super().get_plugin_info()
        base_info.update(
            {
                "domain": "building_management",
                "capabilities": ["process_inputs", "validate_output", "thermal_optimization", "equipment_protection", "energy_efficiency"],
                "supported_systems": ["HVAC", "thermal_control", "energy_management"],
                "safety_features": ["equipment_protection", "temperature_limits", "energy_optimization"],
            }
        )
        return base_info

    def _validate_temperature(self, temp) -> float:
        """Validate and normalize temperature readings."""
        if temp is None:
            return 70.0  # Reasonable default

        # Handle various temperature formats
        if isinstance(temp, str):
            try:
                # Handle common formats like "72°F", "72F", "72.5"
                temp = float(temp.replace("°F", "").replace("F", "").strip())
            except:
                return 70.0

        # Validate reasonable range (0-120°F)
        if not (0 <= temp <= 120):
            return 70.0

        return float(temp)

    def _optimize_setpoint(self, setpoint: float, occupancy: bool) -> float:
        """Apply energy-saving setpoint optimization."""
        if setpoint is None:
            return 72.0 if occupancy else 68.0

        setpoint = self._validate_temperature(setpoint)

        # Energy saving when unoccupied
        if not occupancy and self.energy_optimization_enabled:
            # Use learned setback parameter
            setback = self.learnable_params["energy_setback_degrees"]
            return max(setpoint - setback, 65)

        return setpoint

    def _get_thermal_context(self, inputs: Dict) -> Dict[str, Any]:
        """Generate thermal context for enhanced control decisions."""
        current_temp = inputs.get("current_temp", 72)
        setpoint = inputs.get("setpoint", 72)
        outdoor_temp = inputs.get("outdoor_temp", 70)
        occupancy = inputs.get("occupancy", True)

        temp_error = current_temp - setpoint
        outdoor_delta = outdoor_temp - current_temp

        return {
            "temp_error": temp_error,
            "outdoor_delta": outdoor_delta,
            "heating_load": max(0, -temp_error) if outdoor_temp < current_temp else 0,
            "cooling_load": max(0, temp_error) if outdoor_temp > current_temp else 0,
            "occupancy_factor": 1.0 if occupancy else 0.7,
            "recommended_deadband": (2.0 if not occupancy else 1.0) * self.learnable_params["deadband_multiplier"],
        }

    def _apply_energy_optimization(self, result: Any, context: Dict[str, Any]) -> Any:
        """Apply energy optimization to HVAC commands."""

        if not hasattr(result, "heating_output") and not hasattr(result, "cooling_output"):
            return result

        # Extract thermal context from the enhanced inputs
        thermal_context = None
        if "args" in context:
            # Look for thermal context in processed inputs
            for arg in context["args"]:
                if isinstance(arg, dict) and "thermal_context" in arg:
                    thermal_context = arg["thermal_context"]
                    break

        occupancy_factor = thermal_context.get("occupancy_factor", 1.0) if thermal_context else 1.0

        # Apply occupancy-based energy reduction
        if hasattr(result, "heating_output"):
            result.heating_output *= occupancy_factor

        if hasattr(result, "cooling_output"):
            result.cooling_output *= occupancy_factor

        # Fan speed optimization
        if hasattr(result, "fan_speed"):
            # Reduce fan speed during low-load conditions
            if result.heating_output < 20 and result.cooling_output < 20:
                result.fan_speed = max(result.fan_speed * 0.8, 20)  # Minimum 20% for air circulation

        # Update status to reflect optimization
        if hasattr(result, "status"):
            if occupancy_factor < 1.0:
                result.status += " (Energy optimized)"

        return result

    # Learning Methods Implementation

    def receive_feedback(self, feedback: Dict[str, Any]) -> None:
        """Receive feedback about HVAC performance for domain learning."""
        if not self.learning_enabled:
            return

        # Store feedback for learning analysis
        self.feedback_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "feedback": feedback.copy(),
            }
        )

        # Extract performance metrics
        performance_score = feedback.get("performance_score", 0.5)
        energy_efficiency = feedback.get("energy_efficiency", 0.5)
        comfort_score = feedback.get("comfort_score", 0.5)

        # Calculate domain-specific metric
        domain_performance = (
            performance_score * 0.4
            + energy_efficiency * self.learnable_params["energy_priority_weight"] * 0.4
            + comfort_score * (1 - self.learnable_params["energy_priority_weight"]) * 0.2
        )

        self.performance_metrics.append(domain_performance)
        self.learning_stats["feedback_count"] += 1

        # Update performance trend
        if len(self.performance_metrics) >= 5:
            recent_avg = sum(list(self.performance_metrics)[-5:]) / 5
            older_avg = sum(list(self.performance_metrics)[-10:-5]) / 5 if len(self.performance_metrics) >= 10 else recent_avg

            if recent_avg > older_avg + 0.05:
                self.learning_stats["performance_trend"] = "improving"
            elif recent_avg < older_avg - 0.05:
                self.learning_stats["performance_trend"] = "declining"
            else:
                self.learning_stats["performance_trend"] = "stable"

    def update_from_learning(self, learning_insights: Dict[str, Any]) -> None:
        """Update plugin behavior based on learning insights."""
        if not self.learning_enabled:
            return

        # Process cross-plugin learning insights
        if "domain_best_practices" in learning_insights:
            best_practices = learning_insights["domain_best_practices"]

            # Apply building management best practices
            if "energy_priority" in best_practices:
                self.learnable_params["energy_priority_weight"] = min(0.95, max(0.5, best_practices["energy_priority"]))

        # Process general performance insights
        if "parameter_suggestions" in learning_insights:
            suggestions = learning_insights["parameter_suggestions"]
            for param_name, suggested_value in suggestions.items():
                if param_name in self.learnable_params:
                    # Apply suggested value with bounds checking
                    self._apply_parameter_bounds(param_name, suggested_value)

        self.learning_stats["last_update"] = datetime.now().isoformat()

    def get_domain_metrics(self, execution_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract HVAC-specific metrics for learning from execution results."""
        metrics = {}

        # Extract result data
        result = execution_result.get("result")
        context = execution_result.get("context", {})
        execution_time = execution_result.get("execution_time", 0.0)

        # Performance metrics
        metrics["execution_time"] = float(execution_time)

        # HVAC-specific metrics
        if result and hasattr(result, "heating_output"):
            metrics["heating_output"] = float(result.heating_output)
            metrics["energy_usage_heating"] = float(result.heating_output) / 100.0

        if result and hasattr(result, "cooling_output"):
            metrics["cooling_output"] = float(result.cooling_output)
            metrics["energy_usage_cooling"] = float(result.cooling_output) / 100.0

        if result and hasattr(result, "fan_speed"):
            metrics["fan_speed"] = float(result.fan_speed)

        # Calculate total energy usage
        total_energy = metrics.get("energy_usage_heating", 0) + metrics.get("energy_usage_cooling", 0)
        metrics["total_energy_usage"] = total_energy

        # Efficiency metrics
        if total_energy > 0:
            metrics["energy_efficiency"] = 1.0 / (1.0 + total_energy)  # Higher is better
        else:
            metrics["energy_efficiency"] = 1.0

        # Comfort metrics (based on how close we got to setpoint)
        if "thermal_context" in context:
            temp_error = abs(context["thermal_context"].get("temp_error", 0))
            metrics["comfort_score"] = 1.0 / (1.0 + temp_error)  # Higher is better

        return metrics

    def adapt_parameters(self, current_params: Dict[str, Any], performance_history: List[float]) -> Dict[str, Any]:
        """Adapt HVAC parameters based on performance history."""
        if not self.learning_enabled or len(performance_history) < 3:
            return current_params

        # Calculate performance trend
        recent_performance = sum(performance_history[-3:]) / 3
        baseline_performance = sum(performance_history[:3]) / 3 if len(performance_history) >= 6 else recent_performance

        # Adaptive parameter adjustment
        adapted_params = current_params.copy()

        # If performance is declining, be more conservative
        if recent_performance < baseline_performance - 0.1:
            # More conservative energy management
            adapted_params["energy_setback_degrees"] = max(1.0, self.learnable_params["energy_setback_degrees"] * 0.9)
            adapted_params["deadband_multiplier"] = max(0.8, self.learnable_params["deadband_multiplier"] * 0.95)

        # If performance is improving, can be more aggressive with energy savings
        elif recent_performance > baseline_performance + 0.1:
            adapted_params["energy_setback_degrees"] = min(5.0, self.learnable_params["energy_setback_degrees"] * 1.05)
            adapted_params["energy_priority_weight"] = min(0.95, self.learnable_params["energy_priority_weight"] * 1.02)

        return adapted_params

    def get_learnable_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get HVAC plugin parameters that can be learned/optimized."""
        return {
            "energy_setback_degrees": {
                "current_value": self.learnable_params["energy_setback_degrees"],
                "range": (1.0, 8.0),
                "type": "continuous",
                "impact": "Temperature setback when building is unoccupied (higher = more energy savings)",
            },
            "deadband_multiplier": {
                "current_value": self.learnable_params["deadband_multiplier"],
                "range": (0.5, 2.0),
                "type": "continuous",
                "impact": "Thermal deadband adjustment (higher = wider deadband, less switching)",
            },
            "heating_aggressiveness": {
                "current_value": self.learnable_params["heating_aggressiveness"],
                "range": (0.5, 2.0),
                "type": "continuous",
                "impact": "How aggressively to respond to heating needs (higher = faster response)",
            },
            "cooling_aggressiveness": {
                "current_value": self.learnable_params["cooling_aggressiveness"],
                "range": (0.5, 2.0),
                "type": "continuous",
                "impact": "How aggressively to respond to cooling needs (higher = faster response)",
            },
            "comfort_tolerance": {
                "current_value": self.learnable_params["comfort_tolerance"],
                "range": (0.5, 2.0),
                "type": "continuous",
                "impact": "Temperature tolerance before taking action (higher = more tolerant)",
            },
            "energy_priority_weight": {
                "current_value": self.learnable_params["energy_priority_weight"],
                "range": (0.3, 0.95),
                "type": "continuous",
                "impact": "Balance between energy savings and comfort (higher = prioritize energy)",
            },
        }

    def apply_learned_parameters(self, learned_params: Dict[str, Any]) -> None:
        """Apply learned parameters to HVAC plugin behavior."""
        if not self.learning_enabled:
            return

        for param_name, value in learned_params.items():
            if param_name in self.learnable_params:
                # Apply parameter with bounds checking
                self._apply_parameter_bounds(param_name, value)

        self.learning_stats["parameter_updates"] += 1
        self.learning_stats["last_update"] = datetime.now().isoformat()

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status and statistics for HVAC plugin."""
        base_status = super().get_learning_status()

        # Calculate recent performance trend
        recent_performance = 0.0
        if len(self.performance_metrics) >= 3:
            recent_performance = sum(list(self.performance_metrics)[-3:]) / 3

        base_status.update(
            {
                "learning_enabled": self.learning_enabled,
                "parameters_learned": len(self.learnable_params),
                "learning_progress": self.learning_stats["performance_trend"],
                "performance_trend": self.learning_stats["performance_trend"],
                "feedback_received": self.learning_stats["feedback_count"],
                "parameter_updates": self.learning_stats["parameter_updates"],
                "recent_performance": recent_performance,
                "last_update": self.learning_stats["last_update"],
                "domain_focus": "energy_efficiency_and_comfort_optimization",
            }
        )

        return base_status

    def _apply_parameter_bounds(self, param_name: str, value: float) -> None:
        """Apply parameter value with bounds checking."""
        param_info = self.get_learnable_parameters().get(param_name)
        if not param_info:
            return

        min_val, max_val = param_info["range"]
        bounded_value = max(min_val, min(max_val, float(value)))
        self.learnable_params[param_name] = bounded_value

    def evaluate_objectives(self, execution_result: Dict[str, Any], execution_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate HVAC objectives using formal multi-objective optimization.

        Args:
            execution_result: Complete execution result with metrics
            execution_context: Optional execution context

        Returns:
            Dict: Objective evaluation result with scores and recommendations
        """
        # Extract domain metrics
        domain_metrics = self.get_domain_metrics(execution_result)

        # Add common metrics if available
        if "execution_time" in execution_result:
            domain_metrics["execution_time"] = execution_result["execution_time"]
        if "success_rate" in execution_result:
            domain_metrics["success_rate"] = execution_result.get("success_rate", 1.0)
        else:
            domain_metrics["success_rate"] = 1.0 if execution_result.get("success", True) else 0.0
        domain_metrics["retry_count"] = execution_result.get("retry_count", 0)

        # Create evaluation context
        context = EvaluationContext(
            domain="building_management",
            function_name=execution_context.get("function_name", "hvac_control") if execution_context else "hvac_control",
            execution_id=execution_context.get("execution_id", "unknown") if execution_context else "unknown",
        )

        # Evaluate using domain objectives with energy priority from learned parameters
        objective_config = {
            "energy_priority": self.learnable_params["energy_priority_weight"],
            "optimization_method": "constraint_satisfaction",
        }

        evaluation_result = self.objective_evaluator.evaluate_execution(
            domain="building_management", metrics=domain_metrics, context=context, **objective_config
        )

        # Get learning recommendations
        recommendations = self.objective_evaluator.should_adjust_parameters(
            domain="building_management", current_metrics=domain_metrics, **objective_config
        )

        return {
            "evaluation_result": evaluation_result,
            "recommendations": recommendations,
            "domain_metrics": domain_metrics,
            "objective_config": objective_config,
        }
