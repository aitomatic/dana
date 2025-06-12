"""
Semiconductor Plugin for POET

Provides domain-specific intelligence for semiconductor manufacturing processes,
including process parameter validation, equipment protection, and root cause analysis.

Author: OpenDXA Team
Version: 1.0.0
"""

from typing import Any

from opendxa.dana.poet.plugins.base import POETPlugin


class SemiconductorPlugin(POETPlugin):
    """Domain plugin for semiconductor manufacturing processes."""

    __version__ = "1.0.0"
    __author__ = "OpenDXA Team"

    def __init__(self):
        self.process_limits = {
            "pressure": {"min": 0.1, "max": 10.0, "unit": "Torr"},
            "power": {"min": 100, "max": 3000, "unit": "W"},
            "gas_flow_rate": {"min": 1, "max": 200, "unit": "sccm"},
            "temperature": {"min": -20, "max": 400, "unit": "C"},
            "etch_rate": {"min": 0, "max": 1000, "unit": "nm/min"},
        }

        self.known_issues = {
            "high_pressure_low_rate": "Possible pump issue or gas leak",
            "low_pressure_high_power": "Risk of plasma instability",
            "high_temp_variation": "Thermal control system issue",
            "low_gas_flow": "MFC issue or gas supply problem",
            "power_instability": "RF generator or matching network issue",
        }

        self.safety_interlocks = {
            "max_temp_rate_change": 50,  # °C/min
            "pressure_stability_threshold": 0.1,  # Torr variation
            "power_stability_threshold": 50,  # W variation
        }

    def get_plugin_name(self) -> str:
        """Get unique plugin identifier."""
        return "semiconductor"

    def process_inputs(self, args: tuple, kwargs: dict) -> dict[str, Any]:
        """Process semiconductor process parameters with validation."""

        # Map to standard process parameters
        if len(args) >= 5:
            pressure, power, gas_flow_rate, temperature, etch_rate = args[:5]
        else:
            pressure = kwargs.get("pressure", args[0] if len(args) > 0 else None)
            power = kwargs.get("power", args[1] if len(args) > 1 else None)
            gas_flow_rate = kwargs.get("gas_flow_rate", args[2] if len(args) > 2 else None)
            temperature = kwargs.get("temperature", args[3] if len(args) > 3 else None)
            etch_rate = kwargs.get("etch_rate", args[4] if len(args) > 4 else None)

        # Validate and normalize process parameters
        normalized = {
            "pressure": self._validate_process_param("pressure", pressure),
            "power": self._validate_process_param("power", power),
            "gas_flow_rate": self._validate_process_param("gas_flow_rate", gas_flow_rate),
            "temperature": self._validate_process_param("temperature", temperature),
            "etch_rate": self._validate_process_param("etch_rate", etch_rate),
        }

        # Perform safety checks
        self._safety_interlock_check(normalized)

        return {
            "args": (
                normalized["pressure"],
                normalized["power"],
                normalized["gas_flow_rate"],
                normalized["temperature"],
                normalized["etch_rate"],
            ),
            "kwargs": {},
        }

    def validate_output(self, result: Any, context: dict[str, Any]) -> Any:
        """Validate process analysis output for completeness and accuracy."""

        # Ensure output contains required analysis fields
        if isinstance(result, dict):
            required_fields = ["root_cause", "confidence", "recommendations"]
            for field in required_fields:
                if field not in result or not result[field]:
                    result[field] = f"Analysis incomplete: {field} not determined"

            # Validate confidence is reasonable
            if "confidence" in result:
                try:
                    confidence = float(result["confidence"])
                    if not (0.0 <= confidence <= 1.0):
                        result["confidence"] = max(0.0, min(1.0, confidence))
                except:
                    result["confidence"] = 0.5  # Default medium confidence

            # Ensure recommendations are provided
            if "recommendations" in result and (
                not result["recommendations"] or result["recommendations"] == "Analysis incomplete: recommendations not determined"
            ):
                input_args = context.get("processed_inputs", {}).get("args", [])
                result["recommendations"] = self._generate_default_recommendations(input_args)

        return result

    def get_performance_optimizations(self) -> dict[str, Any]:
        """Get semiconductor-specific performance optimizations."""
        return {
            "timeout_multiplier": 2.0,  # Manufacturing processes may need more time
            "retry_strategy": "exponential",
            "cache_enabled": True,  # Process data can be cached briefly for analysis
            "batch_size": 5,  # Process smaller batches for semiconductor precision
        }

    def get_learning_hints(self, execution_context: dict[str, Any]) -> dict[str, Any]:
        """Provide semiconductor-specific learning guidance."""
        return {
            "parameter_bounds": {
                "timeout": (30.0, 300.0),  # Manufacturing processes: 30-300 seconds
                "precision_threshold": (0.98, 0.999),  # Very high precision requirements
            },
            "learning_rate": 0.005,  # Very conservative learning for manufacturing safety
            "convergence_threshold": 0.005,  # Tight convergence for precision
            "performance_weight": 0.95,  # Prioritize precision and safety over speed
        }

    def get_plugin_info(self) -> dict[str, Any]:
        """Get enhanced plugin information."""
        base_info = super().get_plugin_info()
        base_info.update(
            {
                "domain": "semiconductor",
                "capabilities": ["process_inputs", "validate_output", "parameter_validation", "safety_interlocks", "root_cause_analysis"],
                "supported_processes": ["etching", "deposition", "lithography", "thermal_processing"],
                "safety_features": ["parameter_limits", "safety_interlocks", "equipment_protection"],
            }
        )
        return base_info

    def _validate_process_param(self, param_name: str, value) -> float:
        """Validate process parameters against equipment limits."""
        if value is None:
            return 0.0

        try:
            numeric_value = float(value)

            if param_name in self.process_limits:
                limits = self.process_limits[param_name]

                if not (limits["min"] <= numeric_value <= limits["max"]):
                    # Log warning instead of print
                    from opendxa.common.utils.logging import DXA_LOGGER

                    DXA_LOGGER.warning(
                        f"{param_name} {numeric_value} {limits['unit']} "
                        f"outside normal range ({limits['min']}-{limits['max']} {limits['unit']})"
                    )

                    # Clamp to safe operating range
                    numeric_value = max(limits["min"], min(limits["max"], numeric_value))

            return numeric_value

        except (ValueError, TypeError):
            from opendxa.common.utils.logging import DXA_LOGGER

            DXA_LOGGER.warning(f"Invalid {param_name} value: {value}, using default 0.0")
            return 0.0

    def _safety_interlock_check(self, params: dict):
        """Perform safety interlock checks on process parameters."""

        # Check for dangerous parameter combinations
        pressure = params.get("pressure", 0)
        power = params.get("power", 0)
        temperature = params.get("temperature", 0)
        gas_flow_rate = params.get("gas_flow_rate", 0)

        # High power with low pressure can cause plasma instability
        if power > 1500 and pressure < 1.0:
            raise ValueError(f"Safety interlock: High power ({power}W) with low pressure ({pressure} Torr) " "may cause plasma instability")

        # Very high temperature requires special handling
        if temperature > 300:
            from opendxa.common.utils.logging import DXA_LOGGER

            DXA_LOGGER.warning(f"High temperature warning: {temperature}°C requires enhanced monitoring")

        # Low gas flow with high power can damage chamber
        if gas_flow_rate < 10 and power > 1000:
            raise ValueError(f"Safety interlock: Low gas flow ({gas_flow_rate} sccm) with high power " f"({power}W) may damage chamber")

    def _generate_default_recommendations(self, process_params: list) -> list[str]:
        """Generate default recommendations based on process parameters."""
        recommendations = []

        if len(process_params) >= 5:
            pressure, power, gas_flow_rate, temperature, etch_rate = process_params[:5]

            # Low etch rate recommendations
            if etch_rate < 50:
                if pressure > 5.0:
                    recommendations.append("Reduce chamber pressure to increase etch rate")
                if power < 500:
                    recommendations.append("Increase RF power gradually to improve etching")
                if gas_flow_rate < 20:
                    recommendations.append("Check gas flow rates and MFC calibration")

            # High temperature recommendations
            if temperature > 150:
                recommendations.append("Monitor substrate temperature to prevent resist damage")

            # Equipment maintenance recommendations
            if pressure > 8.0:
                recommendations.append("Check vacuum pump performance and leak rate")

            if not recommendations:
                recommendations.append("Process parameters within normal range - consider optimization")

        return recommendations

    def get_process_expertise(self, issue_type: str) -> str:
        """Get domain expertise for specific process issues."""
        return self.known_issues.get(issue_type, "Unknown issue - consult process engineer")
