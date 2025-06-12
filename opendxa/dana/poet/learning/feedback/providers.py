"""
Feedback provider implementations for enhanced POET Training stage.

This module provides the base FeedbackProvider interface and common
implementations for different feedback modes.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from opendxa.common.mixins.loggable import Loggable

from .feedback import FeedbackCapabilities, FeedbackMode, FeedbackRequest, SimulationFeedback


class FeedbackProvider(ABC, Loggable):
    """Base interface for all feedback providers"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__()
        self.config = config or {}

    @abstractmethod
    def generate_feedback(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> SimulationFeedback:
        """Generate feedback for function execution"""
        pass

    @abstractmethod
    def get_capabilities(self) -> FeedbackCapabilities:
        """Get provider capabilities and characteristics"""
        pass

    def validate_request(self, request: FeedbackRequest) -> bool:
        """Validate if provider can handle feedback request"""
        capabilities = self.get_capabilities()
        return request.requested_mode in capabilities.supported_modes and (
            not request.domain or request.domain in capabilities.supported_domains
        )

    def generate_feedback_from_request(self, request: FeedbackRequest) -> SimulationFeedback:
        """Generate feedback from structured request"""
        if not self.validate_request(request):
            raise ValueError(f"Provider cannot handle request for mode {request.requested_mode}")

        start_time = time.time()

        try:
            feedback = self.generate_feedback(
                function_input=request.function_input, function_output=request.function_output, execution_context=request.execution_context
            )

            # Validate feedback meets minimum requirements
            if feedback.simulation_confidence < request.min_confidence:
                feedback.warnings.append(f"Confidence {feedback.simulation_confidence:.2f} below minimum {request.min_confidence}")

            generation_time = time.time() - start_time
            if generation_time > request.timeout_seconds:
                feedback.warnings.append(f"Feedback generation took {generation_time:.2f}s, exceeded timeout {request.timeout_seconds}s")

            return feedback

        except Exception as e:
            self.error(f"Feedback generation failed: {e}")
            # Return minimal feedback with error
            return SimulationFeedback(
                performance_score=0.0,
                user_satisfaction=0.0,
                system_efficiency=0.0,
                safety_score=0.0,
                feedback_mode=request.requested_mode,
                simulation_confidence=0.0,
                real_data_available=False,
                errors=[str(e)],
            )


class RealWorldFeedbackProvider(FeedbackProvider):
    """Feedback provider using real-world data sources"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.data_sources = config.get("data_sources", {}) if config else {}
        self.sensor_config = config.get("sensors", {}) if config else {}
        self.api_endpoints = config.get("api_endpoints", {}) if config else {}

    def generate_feedback(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> SimulationFeedback:
        """Generate feedback from real-world data sources"""

        # Collect real-world metrics
        metrics = self._collect_real_world_metrics(function_input, function_output, execution_context)

        # Calculate performance scores from real data
        performance_score = metrics.get("system_performance", 0.8)
        user_satisfaction = metrics.get("user_feedback_score", 0.7)
        system_efficiency = metrics.get("resource_utilization", 0.9)
        safety_score = metrics.get("safety_compliance", 1.0)

        return SimulationFeedback(
            performance_score=performance_score,
            user_satisfaction=user_satisfaction,
            system_efficiency=system_efficiency,
            safety_score=safety_score,
            domain_metrics=metrics.get("domain_specific", {}),
            feedback_mode=FeedbackMode.REAL_WORLD,
            simulation_confidence=1.0,  # Real data has high confidence
            real_data_available=True,
            model_accuracy=1.0,  # No model involved
            scenario_context=self._extract_scenario_context(function_input, execution_context),
        )

    def _collect_real_world_metrics(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Collect metrics from real-world sources"""
        metrics = {}

        # Example: Collect from configured data sources
        for source_name, source_config in self.data_sources.items():
            try:
                source_data = self._query_data_source(source_name, source_config, function_input, function_output)
                metrics.update(source_data)
            except Exception as e:
                self.warning(f"Failed to collect from {source_name}: {e}")

        return metrics

    def _query_data_source(
        self, source_name: str, source_config: dict[str, Any], function_input: dict[str, Any], function_output: Any
    ) -> dict[str, Any]:
        """Query individual data source"""
        # Placeholder implementation - would integrate with actual data sources
        # like databases, APIs, sensors, user feedback systems, etc.

        if source_config.get("type") == "sensor":
            return self._collect_sensor_data(source_config)
        elif source_config.get("type") == "api":
            return self._collect_api_data(source_config, function_input, function_output)
        elif source_config.get("type") == "database":
            return self._collect_database_metrics(source_config, function_input)
        else:
            return {}

    def _collect_sensor_data(self, sensor_config: dict[str, Any]) -> dict[str, Any]:
        """Collect data from sensors"""
        # Placeholder for sensor integration
        return {"sensor_readings": 0.8}

    def _collect_api_data(self, api_config: dict[str, Any], function_input: dict[str, Any], function_output: Any) -> dict[str, Any]:
        """Collect data from APIs"""
        # Placeholder for API integration
        return {"api_metrics": 0.9}

    def _collect_database_metrics(self, db_config: dict[str, Any], function_input: dict[str, Any]) -> dict[str, Any]:
        """Collect metrics from database"""
        # Placeholder for database integration
        return {"historical_performance": 0.85}

    def _extract_scenario_context(self, function_input: dict[str, Any], execution_context: dict[str, Any]) -> dict[str, Any]:
        """Extract relevant scenario context"""
        return {
            "environment": execution_context.get("environment", "production"),
            "user_type": function_input.get("user_type", "standard"),
            "time_of_day": datetime.now().hour,
            "system_load": execution_context.get("system_load", "normal"),
        }

    def get_capabilities(self) -> FeedbackCapabilities:
        """Get real-world provider capabilities"""
        return FeedbackCapabilities(
            supported_modes=[FeedbackMode.REAL_WORLD],
            supported_domains=list(self.config.get("supported_domains", [])),
            available_metrics=list(self.data_sources.keys()) + ["system_performance", "user_satisfaction"],
            simulation_models=[],  # No simulation models
            typical_latency_ms=500.0,  # API/sensor latency
            confidence_range=(0.8, 1.0),  # High confidence in real data
            accuracy_estimate=0.95,  # Real data is accurate
            requires_real_data=True,
            requires_user_input=False,
            requires_domain_config=True,
        )


class SimulationFeedbackProvider(FeedbackProvider):
    """Feedback provider using domain simulation models"""

    def __init__(self, simulation_models: dict[str, Any], config: dict[str, Any] | None = None):
        super().__init__(config)
        self.simulation_models = simulation_models
        self.model_accuracy = config.get("model_accuracy", 0.85) if config else 0.85

    def generate_feedback(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> SimulationFeedback:
        """Generate feedback using simulation models"""

        # Run relevant simulation models
        simulation_results = self._run_simulations(function_input, function_output, execution_context)

        # Extract performance metrics from simulation
        performance_score = simulation_results.get("performance", 0.7)
        user_satisfaction = simulation_results.get("user_satisfaction", 0.8)
        system_efficiency = simulation_results.get("efficiency", 0.75)
        safety_score = simulation_results.get("safety", 0.9)

        return SimulationFeedback(
            performance_score=performance_score,
            user_satisfaction=user_satisfaction,
            system_efficiency=system_efficiency,
            safety_score=safety_score,
            domain_metrics=simulation_results.get("domain_metrics", {}),
            feedback_mode=FeedbackMode.SIMULATION,
            simulation_confidence=self.model_accuracy,
            real_data_available=False,
            model_accuracy=self.model_accuracy,
            scenario_context=simulation_results.get("scenario_context", {}),
        )

    def _run_simulations(self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]) -> dict[str, Any]:
        """Run all available simulation models"""
        results = {}

        for model_name, model in self.simulation_models.items():
            try:
                if hasattr(model, "simulate"):
                    model_result = model.simulate(input_data=function_input, output_data=function_output, context=execution_context)
                    results[model_name] = model_result
                else:
                    self.warning(f"Model {model_name} doesn't have simulate method")
            except Exception as e:
                self.warning(f"Simulation {model_name} failed: {e}")

        # Aggregate results from multiple models
        return self._aggregate_simulation_results(results)

    def _aggregate_simulation_results(self, model_results: dict[str, Any]) -> dict[str, Any]:
        """Aggregate results from multiple simulation models"""
        if not model_results:
            return {"performance": 0.5, "user_satisfaction": 0.5, "efficiency": 0.5, "safety": 0.5, "domain_metrics": {}}

        # Extract metrics from SimulationResult objects
        all_performance_metrics = {}
        all_domain_metrics = {}

        for model_name, result in model_results.items():
            if hasattr(result, "performance_metrics"):
                # It's a SimulationResult object
                for metric, value in result.performance_metrics.items():
                    if metric not in all_performance_metrics:
                        all_performance_metrics[metric] = []
                    all_performance_metrics[metric].append(value)

                for metric, value in result.domain_metrics.items():
                    if metric not in all_domain_metrics:
                        all_domain_metrics[metric] = []
                    all_domain_metrics[metric].append(value)
            else:
                # It's a dictionary (fallback)
                for metric, value in result.items():
                    if metric not in all_performance_metrics:
                        all_performance_metrics[metric] = []
                    all_performance_metrics[metric].append(value)

        # Calculate averages
        aggregated_performance = {}
        for metric, values in all_performance_metrics.items():
            aggregated_performance[metric] = sum(values) / len(values) if values else 0.5

        aggregated_domain = {}
        for metric, values in all_domain_metrics.items():
            aggregated_domain[metric] = sum(values) / len(values) if values else 0.5

        # Map common performance metrics to expected names
        aggregated = {
            "performance": aggregated_performance.get("temperature_control", aggregated_performance.get("performance", 0.7)),
            "user_satisfaction": aggregated_domain.get("comfort_score", 0.8),
            "efficiency": aggregated_performance.get("energy_efficiency", aggregated_performance.get("efficiency", 0.75)),
            "safety": 0.9,  # Default safety score
            "domain_metrics": aggregated_domain,
        }

        return aggregated

    def get_capabilities(self) -> FeedbackCapabilities:
        """Get simulation provider capabilities"""
        return FeedbackCapabilities(
            supported_modes=[FeedbackMode.SIMULATION, FeedbackMode.SAFE_TESTING],
            supported_domains=list(self.config.get("supported_domains", [])),
            available_metrics=list(self.simulation_models.keys()) + ["performance", "efficiency"],
            simulation_models=list(self.simulation_models.keys()),
            typical_latency_ms=200.0,  # Faster than real-world
            confidence_range=(0.6, 0.9),  # Model-dependent confidence
            accuracy_estimate=self.model_accuracy,
            requires_real_data=False,
            requires_user_input=False,
            requires_domain_config=True,
        )


class HybridFeedbackProvider(FeedbackProvider):
    """Feedback provider combining real-world and simulation data"""

    def __init__(
        self,
        real_provider: FeedbackProvider,
        simulation_provider: FeedbackProvider,
        config: dict[str, Any] | None = None,
    ):
        super().__init__(config)
        self.real_provider = real_provider
        self.simulation_provider = simulation_provider
        self.real_weight = config.get("real_weight", 0.7) if config else 0.7
        self.simulation_weight = 1.0 - self.real_weight

    def generate_feedback(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> SimulationFeedback:
        """Generate hybrid feedback combining real and simulated data"""

        # Get feedback from both providers
        real_feedback = self.real_provider.generate_feedback(function_input, function_output, execution_context)
        sim_feedback = self.simulation_provider.generate_feedback(function_input, function_output, execution_context)

        # Weighted combination of scores
        performance_score = real_feedback.performance_score * self.real_weight + sim_feedback.performance_score * self.simulation_weight

        user_satisfaction = real_feedback.user_satisfaction * self.real_weight + sim_feedback.user_satisfaction * self.simulation_weight

        system_efficiency = real_feedback.system_efficiency * self.real_weight + sim_feedback.system_efficiency * self.simulation_weight

        safety_score = real_feedback.safety_score * self.real_weight + sim_feedback.safety_score * self.simulation_weight

        # Combine domain metrics
        combined_metrics = {}
        combined_metrics.update(real_feedback.domain_metrics)
        for key, value in sim_feedback.domain_metrics.items():
            if key in combined_metrics:
                combined_metrics[key] = combined_metrics[key] * self.real_weight + value * self.simulation_weight
            else:
                combined_metrics[key] = value * self.simulation_weight

        # Combined confidence based on both sources
        combined_confidence = (
            real_feedback.simulation_confidence * self.real_weight + sim_feedback.simulation_confidence * self.simulation_weight
        )

        return SimulationFeedback(
            performance_score=performance_score,
            user_satisfaction=user_satisfaction,
            system_efficiency=system_efficiency,
            safety_score=safety_score,
            domain_metrics=combined_metrics,
            feedback_mode=FeedbackMode.HYBRID,
            simulation_confidence=combined_confidence,
            real_data_available=real_feedback.real_data_available,
            model_accuracy=(real_feedback.model_accuracy + sim_feedback.model_accuracy) / 2,
            scenario_context={**real_feedback.scenario_context, **sim_feedback.scenario_context},
        )

    def get_capabilities(self) -> FeedbackCapabilities:
        """Get hybrid provider capabilities"""
        real_caps = self.real_provider.get_capabilities()
        sim_caps = self.simulation_provider.get_capabilities()

        return FeedbackCapabilities(
            supported_modes=[FeedbackMode.HYBRID],
            supported_domains=list(set(real_caps.supported_domains + sim_caps.supported_domains)),
            available_metrics=list(set(real_caps.available_metrics + sim_caps.available_metrics)),
            simulation_models=sim_caps.simulation_models,
            typical_latency_ms=max(real_caps.typical_latency_ms, sim_caps.typical_latency_ms),
            confidence_range=(
                min(real_caps.confidence_range[0], sim_caps.confidence_range[0]),
                max(real_caps.confidence_range[1], sim_caps.confidence_range[1]),
            ),
            accuracy_estimate=(real_caps.accuracy_estimate + sim_caps.accuracy_estimate) / 2,
            requires_real_data=real_caps.requires_real_data,
            requires_user_input=real_caps.requires_user_input or sim_caps.requires_user_input,
            requires_domain_config=real_caps.requires_domain_config or sim_caps.requires_domain_config,
        )


class SafeTestingFeedbackProvider(SimulationFeedbackProvider):
    """Feedback provider for safe development/testing with constraints"""

    def __init__(self, simulation_models: dict[str, Any], safety_constraints: dict[str, Any], config: dict[str, Any] | None = None):
        super().__init__(simulation_models, config)
        self.safety_constraints = safety_constraints

    def generate_feedback(
        self, function_input: dict[str, Any], function_output: Any, execution_context: dict[str, Any]
    ) -> SimulationFeedback:
        """Generate safe testing feedback with constraints"""

        # Check safety constraints first
        constraint_violations = self._check_safety_constraints(function_input, function_output)

        if constraint_violations:
            # Return safe feedback indicating constraint violations
            return SimulationFeedback(
                performance_score=0.0,
                user_satisfaction=0.0,
                system_efficiency=0.0,
                safety_score=0.0,
                feedback_mode=FeedbackMode.SAFE_TESTING,
                simulation_confidence=1.0,  # High confidence in constraint checking
                real_data_available=False,
                errors=[f"Safety constraint violated: {violation}" for violation in constraint_violations],
            )

        # Run constrained simulation
        feedback = super().generate_feedback(function_input, function_output, execution_context)
        feedback.feedback_mode = FeedbackMode.SAFE_TESTING

        # Apply safety bounds to scores
        feedback.safety_score = max(0.8, feedback.safety_score)  # Minimum safety in testing

        return feedback

    def _check_safety_constraints(self, function_input: dict[str, Any], function_output: Any) -> list[str]:
        """Check function parameters against safety constraints"""
        violations = []

        # Check input constraints
        for param, value in function_input.items():
            if param in self.safety_constraints.get("input_bounds", {}):
                bounds = self.safety_constraints["input_bounds"][param]
                if isinstance(value, (int, float)):
                    if value < bounds.get("min", float("-inf")) or value > bounds.get("max", float("inf")):
                        violations.append(f"Parameter {param}={value} outside safe bounds {bounds}")

        # Check output constraints
        if hasattr(function_output, "__dict__"):
            output_dict = function_output.__dict__
        elif isinstance(function_output, dict):
            output_dict = function_output
        else:
            output_dict = {"result": function_output}

        for param, value in output_dict.items():
            if param in self.safety_constraints.get("output_bounds", {}):
                bounds = self.safety_constraints["output_bounds"][param]
                if isinstance(value, (int, float)):
                    if value < bounds.get("min", float("-inf")) or value > bounds.get("max", float("inf")):
                        violations.append(f"Output {param}={value} outside safe bounds {bounds}")

        return violations

    def get_capabilities(self) -> FeedbackCapabilities:
        """Get safe testing provider capabilities"""
        base_caps = super().get_capabilities()
        base_caps.supported_modes = [FeedbackMode.SAFE_TESTING]
        base_caps.confidence_range = (0.9, 1.0)  # High confidence in safety
        return base_caps
