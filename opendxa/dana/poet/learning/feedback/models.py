"""
Base simulation model classes for POET feedback providers.

This module provides the foundation for domain-specific simulation models
that generate realistic feedback for the enhanced Training stage.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from opendxa.common.mixins.loggable import Loggable


@dataclass
class SimulationResult:
    """Result from a simulation model execution"""

    # Core performance metrics
    performance_metrics: dict[str, float] = field(default_factory=dict)
    domain_metrics: dict[str, float] = field(default_factory=dict)

    # Simulation metadata
    model_name: str = ""
    execution_time_ms: float = 0.0
    confidence_score: float = 1.0

    # Additional context
    scenario_context: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if simulation result is valid"""
        return len(self.errors) == 0 and self.confidence_score > 0.5


class SimulationModel(ABC, Loggable):
    """Base class for all simulation models"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__()
        self.config = config or {}
        self.model_name = self.__class__.__name__
        self.accuracy_estimate = config.get("accuracy_estimate", 0.8) if config else 0.8

    @abstractmethod
    def simulate(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> SimulationResult:
        """Run simulation and return results"""
        pass

    @abstractmethod
    def get_supported_metrics(self) -> list[str]:
        """Get list of metrics this model can simulate"""
        pass

    def validate_inputs(self, input_data: dict[str, Any]) -> list[str]:
        """Validate simulation inputs and return any errors"""
        errors = []
        required_inputs = self.get_required_inputs()

        for required_input in required_inputs:
            if required_input not in input_data:
                errors.append(f"Missing required input: {required_input}")

        return errors

    def get_required_inputs(self) -> list[str]:
        """Get list of required inputs for this model"""
        return []

    def get_model_info(self) -> dict[str, Any]:
        """Get model information and capabilities"""
        return {
            "name": self.model_name,
            "supported_metrics": self.get_supported_metrics(),
            "required_inputs": self.get_required_inputs(),
            "accuracy_estimate": self.accuracy_estimate,
            "description": self.__doc__ or f"Simulation model: {self.model_name}",
        }


class DomainSimulationModel(SimulationModel):
    """Extended base class for domain-specific simulation models"""

    def __init__(self, domain: str, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.domain = domain
        self.domain_knowledge = config.get("domain_knowledge", {}) if config else {}
        self.simulation_parameters = config.get("simulation_parameters", {}) if config else {}

    @abstractmethod
    def get_domain_name(self) -> str:
        """Get the domain this model simulates"""
        pass

    def get_domain_metrics(self) -> list[str]:
        """Get domain-specific metrics"""
        return []

    def simulate_with_domain_context(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> SimulationResult:
        """Simulate with domain-specific enhancements"""

        start_time = time.time()

        # Validate domain-specific inputs
        validation_errors = self.validate_domain_inputs(input_data, output_data, context)
        if validation_errors:
            return SimulationResult(
                model_name=self.model_name,
                execution_time_ms=(time.time() - start_time) * 1000,
                confidence_score=0.0,
                errors=validation_errors,
            )

        # Run the actual simulation
        try:
            result = self.simulate(input_data, output_data, context)
            result.execution_time_ms = (time.time() - start_time) * 1000
            result.model_name = self.model_name

            # Add domain context
            result.scenario_context["domain"] = self.domain
            result.scenario_context["domain_parameters"] = self.simulation_parameters

            return result

        except Exception as e:
            self.error(f"Domain simulation failed: {e}")
            return SimulationResult(
                model_name=self.model_name, execution_time_ms=(time.time() - start_time) * 1000, confidence_score=0.0, errors=[str(e)]
            )

    def validate_domain_inputs(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> list[str]:
        """Validate domain-specific inputs"""
        errors = self.validate_inputs(input_data)

        # Add domain-specific validation
        domain_requirements = self.domain_knowledge.get("required_parameters", [])
        for param in domain_requirements:
            if param not in input_data and param not in context:
                errors.append(f"Missing domain parameter: {param}")

        return errors

    def get_model_info(self) -> dict[str, Any]:
        """Get enhanced model information including domain details"""
        base_info = super().get_model_info()
        base_info.update(
            {
                "domain": self.domain,
                "domain_metrics": self.get_domain_metrics(),
                "domain_parameters": list(self.simulation_parameters.keys()),
                "domain_knowledge_areas": list(self.domain_knowledge.keys()),
            }
        )
        return base_info


class CompositeSimulationModel(SimulationModel):
    """Simulation model that combines multiple sub-models"""

    def __init__(self, sub_models: list[SimulationModel], config: dict[str, Any] | None = None):
        super().__init__(config)
        self.sub_models = sub_models
        self.aggregation_strategy = config.get("aggregation_strategy", "weighted_average") if config else "weighted_average"
        self.model_weights = config.get("model_weights", {}) if config else {}

    def simulate(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> SimulationResult:
        """Run all sub-models and aggregate results"""

        sub_results = []
        all_errors = []
        all_warnings = []

        # Run each sub-model
        for model in self.sub_models:
            try:
                result = model.simulate(input_data, output_data, context)
                if result.is_valid():
                    sub_results.append(result)
                else:
                    all_errors.extend(result.errors)
                    all_warnings.extend(result.warnings)
            except Exception as e:
                all_errors.append(f"Sub-model {model.model_name} failed: {e}")

        if not sub_results:
            return SimulationResult(model_name=self.model_name, confidence_score=0.0, errors=all_errors, warnings=all_warnings)

        # Aggregate results
        aggregated_result = self._aggregate_results(sub_results)
        aggregated_result.model_name = self.model_name
        aggregated_result.warnings.extend(all_warnings)

        return aggregated_result

    def _aggregate_results(self, results: list[SimulationResult]) -> SimulationResult:
        """Aggregate multiple simulation results"""

        if not results:
            return SimulationResult(confidence_score=0.0)

        if len(results) == 1:
            return results[0]

        # Aggregate performance metrics
        aggregated_performance = {}
        aggregated_domain = {}

        for result in results:
            # Weight by confidence score if no specific weights provided
            weight = self.model_weights.get(result.model_name, result.confidence_score)

            for metric, value in result.performance_metrics.items():
                if metric not in aggregated_performance:
                    aggregated_performance[metric] = []
                aggregated_performance[metric].append((value, weight))

            for metric, value in result.domain_metrics.items():
                if metric not in aggregated_domain:
                    aggregated_domain[metric] = []
                aggregated_domain[metric].append((value, weight))

        # Calculate weighted averages
        final_performance = {}
        for metric, values_weights in aggregated_performance.items():
            total_weight = sum(weight for _, weight in values_weights)
            if total_weight > 0:
                weighted_sum = sum(value * weight for value, weight in values_weights)
                final_performance[metric] = weighted_sum / total_weight

        final_domain = {}
        for metric, values_weights in aggregated_domain.items():
            total_weight = sum(weight for _, weight in values_weights)
            if total_weight > 0:
                weighted_sum = sum(value * weight for value, weight in values_weights)
                final_domain[metric] = weighted_sum / total_weight

        # Overall confidence as average of sub-model confidences
        overall_confidence = sum(result.confidence_score for result in results) / len(results)

        return SimulationResult(
            performance_metrics=final_performance,
            domain_metrics=final_domain,
            confidence_score=overall_confidence,
            scenario_context={"aggregated_from": [r.model_name for r in results]},
        )

    def get_supported_metrics(self) -> list[str]:
        """Get union of all sub-model metrics"""
        all_metrics = set()
        for model in self.sub_models:
            all_metrics.update(model.get_supported_metrics())
        return list(all_metrics)

    def get_required_inputs(self) -> list[str]:
        """Get union of all required inputs"""
        all_inputs = set()
        for model in self.sub_models:
            all_inputs.update(model.get_required_inputs())
        return list(all_inputs)


# Utility functions for creating common simulation patterns


def create_physics_based_model(
    physics_equations: dict[str, callable], parameter_bounds: dict[str, tuple], config: dict[str, Any] | None = None
) -> SimulationModel:
    """Create a physics-based simulation model"""

    class PhysicsBasedModel(SimulationModel):
        def __init__(self):
            super().__init__(config)
            self.equations = physics_equations
            self.bounds = parameter_bounds

        def simulate(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> SimulationResult:
            results = {}

            # Apply physics equations
            for metric_name, equation in self.equations.items():
                try:
                    value = equation(input_data, output_data, context)

                    # Check bounds
                    if metric_name in self.bounds:
                        min_val, max_val = self.bounds[metric_name]
                        value = max(min_val, min(max_val, value))

                    results[metric_name] = value
                except Exception as e:
                    self.warning(f"Physics equation for {metric_name} failed: {e}")
                    results[metric_name] = 0.5  # Default fallback

            return SimulationResult(
                performance_metrics=results,
                confidence_score=0.9,  # High confidence in physics
                scenario_context={"model_type": "physics_based"},
            )

        def get_supported_metrics(self) -> list[str]:
            return list(self.equations.keys())

    return PhysicsBasedModel()


def create_statistical_model(
    historical_data: dict[str, list[float]], regression_params: dict[str, Any], config: dict[str, Any] | None = None
) -> SimulationModel:
    """Create a statistical simulation model"""

    class StatisticalModel(SimulationModel):
        def __init__(self):
            super().__init__(config)
            self.historical_data = historical_data
            self.regression_params = regression_params

        def simulate(self, input_data: dict[str, Any], output_data: Any, context: dict[str, Any]) -> SimulationResult:
            results = {}

            # Apply statistical models
            for metric_name, historical_values in self.historical_data.items():
                try:
                    # Simple statistical prediction (could be more sophisticated)
                    mean_value = sum(historical_values) / len(historical_values)

                    # Apply context-based adjustments
                    adjustment_factor = self._calculate_context_adjustment(input_data, context)
                    predicted_value = mean_value * adjustment_factor

                    results[metric_name] = max(0.0, min(1.0, predicted_value))
                except Exception as e:
                    self.warning(f"Statistical model for {metric_name} failed: {e}")
                    results[metric_name] = 0.5

            return SimulationResult(
                performance_metrics=results,
                confidence_score=0.7,  # Medium confidence in statistical models
                scenario_context={"model_type": "statistical", "data_points": len(historical_values)},
            )

        def _calculate_context_adjustment(self, input_data: dict[str, Any], context: dict[str, Any]) -> float:
            """Calculate adjustment factor based on context"""
            # Simple context-based adjustment
            return 1.0 + (hash(str(input_data)) % 100 - 50) / 1000  # Small random adjustment

        def get_supported_metrics(self) -> list[str]:
            return list(self.historical_data.keys())

    return StatisticalModel()
