"""
Domain-Specific Objective Definitions

This module contains pre-defined objective functions for different POET domains,
implementing common industry patterns and best practices.
"""

from .base import MultiObjective, ObjectiveFunction, ObjectivePriority, ObjectiveType


class CommonObjectives:
    """Common objectives that apply to all POET functions."""

    @staticmethod
    def maximize_success_rate(min_required: float = 0.8) -> ObjectiveFunction:
        """All functions must maintain minimum success rate."""
        return ObjectiveFunction(
            name="maximize_success_rate",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.CRITICAL,
            metric_name="success_rate",
            weight=0.4,
            min_value=min_required,
            description=f"Function success rate must be at least {min_required*100}%",
            unit="percentage",
        )

    @staticmethod
    def minimize_execution_time(max_allowed: float = 30.0) -> ObjectiveFunction:
        """Minimize function execution time."""
        return ObjectiveFunction(
            name="minimize_execution_time",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="execution_time",
            weight=0.3,
            max_value=max_allowed,
            description=f"Execution time should be minimized (max {max_allowed}s)",
            unit="seconds",
        )

    @staticmethod
    def minimize_retry_count(max_retries: int = 3) -> ObjectiveFunction:
        """Minimize number of retries needed."""
        return ObjectiveFunction(
            name="minimize_retry_count",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.MEDIUM,
            metric_name="retry_count",
            weight=0.2,
            max_value=float(max_retries),
            description=f"Number of retries should be minimized (max {max_retries})",
            unit="count",
        )

    @staticmethod
    def maximize_output_quality(min_quality: float = 0.7) -> ObjectiveFunction:
        """Maximize output quality score."""
        return ObjectiveFunction(
            name="maximize_output_quality",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="output_quality",
            weight=0.3,
            min_value=min_quality,
            description=f"Output quality must be at least {min_quality*100}%",
            unit="score",
        )


class BuildingManagementObjectives:
    """Objectives specific to building management and HVAC systems."""

    @staticmethod
    def maximize_energy_efficiency(weight: float = 0.4) -> ObjectiveFunction:
        """Maximize building energy efficiency."""
        return ObjectiveFunction(
            name="maximize_energy_efficiency",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="energy_efficiency",
            weight=weight,
            min_value=0.3,  # Must be at least 30% efficient
            description="Maximize energy efficiency while maintaining comfort",
            unit="efficiency_ratio",
        )

    @staticmethod
    def maximize_comfort_score(weight: float = 0.3, min_comfort: float = 0.7) -> ObjectiveFunction:
        """Maximize occupant comfort."""
        return ObjectiveFunction(
            name="maximize_comfort_score",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="comfort_score",
            weight=weight,
            min_value=min_comfort,
            description=f"Occupant comfort must be at least {min_comfort*100}%",
            unit="comfort_index",
        )

    @staticmethod
    def equipment_safety_constraint() -> ObjectiveFunction:
        """Critical equipment safety constraint."""
        return ObjectiveFunction(
            name="equipment_safety_constraint",
            type=ObjectiveType.CONSTRAINT,
            priority=ObjectivePriority.CRITICAL,
            metric_name="equipment_safety_score",
            min_value=0.95,  # 95% safety minimum
            description="Equipment safety score must never drop below 95%",
            unit="safety_score",
        )

    @staticmethod
    def minimize_operating_cost(max_cost: float = 100.0) -> ObjectiveFunction:
        """Minimize operating costs."""
        return ObjectiveFunction(
            name="minimize_operating_cost",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.MEDIUM,
            metric_name="operating_cost",
            weight=0.2,
            max_value=max_cost,
            description=f"Operating cost should not exceed ${max_cost}/hour",
            unit="dollars_per_hour",
        )

    @staticmethod
    def temperature_bounds_constraint(min_temp: float = 65.0, max_temp: float = 80.0) -> ObjectiveFunction:
        """Temperature must stay within acceptable bounds."""
        return ObjectiveFunction(
            name="temperature_bounds_constraint",
            type=ObjectiveType.CONSTRAINT,
            priority=ObjectivePriority.HIGH,
            metric_name="current_temperature",
            min_value=min_temp,
            max_value=max_temp,
            description=f"Temperature must stay between {min_temp}°F and {max_temp}°F",
            unit="fahrenheit",
        )

    @staticmethod
    def response_time_constraint(max_response: float = 5.0) -> ObjectiveFunction:
        """HVAC system must respond within time limit."""
        return ObjectiveFunction(
            name="response_time_constraint",
            type=ObjectiveType.CONSTRAINT,
            priority=ObjectivePriority.CRITICAL,
            metric_name="response_time",
            max_value=max_response,
            description=f"System response time must not exceed {max_response} seconds",
            unit="seconds",
        )

    @staticmethod
    def create_hvac_multi_objective(energy_priority: float = 0.8, optimization_method: str = "constraint_satisfaction") -> MultiObjective:
        """Create multi-objective for HVAC optimization."""

        # Adjust weights based on energy priority
        energy_weight = energy_priority * 0.5  # 0.0 to 0.4
        comfort_weight = (1 - energy_priority) * 0.4  # 0.0 to 0.4

        objectives = [
            # Common objectives
            CommonObjectives.maximize_success_rate(),
            CommonObjectives.minimize_execution_time(),
            # HVAC-specific objectives
            BuildingManagementObjectives.maximize_energy_efficiency(energy_weight),
            BuildingManagementObjectives.maximize_comfort_score(comfort_weight),
            BuildingManagementObjectives.minimize_operating_cost(),
            # Critical constraints
            BuildingManagementObjectives.equipment_safety_constraint(),
            BuildingManagementObjectives.response_time_constraint(),
            BuildingManagementObjectives.temperature_bounds_constraint(),
        ]

        return MultiObjective(name="hvac_optimization", objectives=objectives, method=optimization_method)


class LLMOptimizationObjectives:
    """Objectives specific to LLM optimization and prompt engineering."""

    @staticmethod
    def minimize_token_usage(weight: float = 0.2) -> ObjectiveFunction:
        """Minimize LLM token consumption."""
        return ObjectiveFunction(
            name="minimize_token_usage",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.MEDIUM,
            metric_name="token_usage",
            weight=weight,
            description="Minimize token usage to reduce costs",
            unit="tokens",
        )

    @staticmethod
    def maximize_output_relevance(weight: float = 0.3) -> ObjectiveFunction:
        """Maximize relevance of LLM output."""
        return ObjectiveFunction(
            name="maximize_output_relevance",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="output_relevance",
            weight=weight,
            min_value=0.7,
            description="LLM output must be highly relevant to the query",
            unit="relevance_score",
        )

    @staticmethod
    def minimize_latency(max_latency: float = 10.0) -> ObjectiveFunction:
        """Minimize LLM response latency."""
        return ObjectiveFunction(
            name="minimize_latency",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="response_latency",
            weight=0.25,
            max_value=max_latency,
            description=f"Response latency should not exceed {max_latency} seconds",
            unit="seconds",
        )

    @staticmethod
    def content_safety_constraint() -> ObjectiveFunction:
        """Ensure content safety compliance."""
        return ObjectiveFunction(
            name="content_safety_constraint",
            type=ObjectiveType.CONSTRAINT,
            priority=ObjectivePriority.CRITICAL,
            metric_name="content_safety_score",
            min_value=0.95,
            description="Content must meet safety guidelines (95% minimum)",
            unit="safety_score",
        )

    @staticmethod
    def create_llm_multi_objective(cost_priority: float = 0.3) -> MultiObjective:
        """Create multi-objective for LLM optimization."""

        # Adjust weights based on cost vs quality priority
        token_weight = cost_priority * 0.3
        quality_weight = (1 - cost_priority) * 0.4

        objectives = [
            # Common objectives
            CommonObjectives.maximize_success_rate(),
            CommonObjectives.maximize_output_quality(),
            # LLM-specific objectives
            LLMOptimizationObjectives.minimize_token_usage(token_weight),
            LLMOptimizationObjectives.maximize_output_relevance(quality_weight),
            LLMOptimizationObjectives.minimize_latency(),
            # Critical constraints
            LLMOptimizationObjectives.content_safety_constraint(),
        ]

        return MultiObjective(name="llm_optimization", objectives=objectives, method="constraint_satisfaction")


class FinancialServicesObjectives:
    """Objectives for financial services and compliance domains."""

    @staticmethod
    def minimize_false_positives(max_rate: float = 0.05) -> ObjectiveFunction:
        """Minimize false positive rate in fraud detection."""
        return ObjectiveFunction(
            name="minimize_false_positives",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="false_positive_rate",
            weight=0.3,
            max_value=max_rate,
            description=f"False positive rate must not exceed {max_rate*100}%",
            unit="rate",
        )

    @staticmethod
    def maximize_detection_accuracy(min_accuracy: float = 0.9) -> ObjectiveFunction:
        """Maximize fraud detection accuracy."""
        return ObjectiveFunction(
            name="maximize_detection_accuracy",
            type=ObjectiveType.MAXIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="detection_accuracy",
            weight=0.4,
            min_value=min_accuracy,
            description=f"Detection accuracy must be at least {min_accuracy*100}%",
            unit="accuracy",
        )

    @staticmethod
    def regulatory_compliance_constraint() -> ObjectiveFunction:
        """Ensure 100% regulatory compliance."""
        return ObjectiveFunction(
            name="regulatory_compliance_constraint",
            type=ObjectiveType.CONSTRAINT,
            priority=ObjectivePriority.CRITICAL,
            metric_name="compliance_score",
            min_value=1.0,  # 100% compliance required
            description="Must maintain 100% regulatory compliance",
            unit="compliance_score",
        )

    @staticmethod
    def minimize_processing_time(max_time: float = 2.0) -> ObjectiveFunction:
        """Minimize transaction processing time."""
        return ObjectiveFunction(
            name="minimize_processing_time",
            type=ObjectiveType.MINIMIZE,
            priority=ObjectivePriority.HIGH,
            metric_name="processing_time",
            weight=0.2,
            max_value=max_time,
            description=f"Processing time should not exceed {max_time} seconds",
            unit="seconds",
        )

    @staticmethod
    def create_fraud_detection_multi_objective(accuracy_priority: float = 0.8) -> MultiObjective:
        """Create multi-objective for fraud detection."""

        objectives = [
            # Common objectives
            CommonObjectives.maximize_success_rate(),
            # Financial services objectives
            FinancialServicesObjectives.maximize_detection_accuracy(),
            FinancialServicesObjectives.minimize_false_positives(),
            FinancialServicesObjectives.minimize_processing_time(),
            # Critical constraints
            FinancialServicesObjectives.regulatory_compliance_constraint(),
        ]

        return MultiObjective(name="fraud_detection", objectives=objectives, method="constraint_satisfaction")


def get_domain_objectives(domain: str, **kwargs) -> MultiObjective:
    """
    Get pre-configured multi-objective for a domain.

    Args:
        domain: Domain name ("building_management", "llm_optimization", "financial_services")
        **kwargs: Domain-specific configuration parameters

    Returns:
        MultiObjective: Configured multi-objective for the domain
    """

    if domain == "building_management":
        energy_priority = kwargs.get("energy_priority", 0.8)
        method = kwargs.get("optimization_method", "constraint_satisfaction")
        return BuildingManagementObjectives.create_hvac_multi_objective(energy_priority, method)

    elif domain == "llm_optimization":
        cost_priority = kwargs.get("cost_priority", 0.3)
        return LLMOptimizationObjectives.create_llm_multi_objective(cost_priority)

    elif domain == "financial_services":
        accuracy_priority = kwargs.get("accuracy_priority", 0.8)
        return FinancialServicesObjectives.create_fraud_detection_multi_objective(accuracy_priority)

    else:
        # Default to common objectives only
        objectives = [
            CommonObjectives.maximize_success_rate(),
            CommonObjectives.minimize_execution_time(),
            CommonObjectives.minimize_retry_count(),
            CommonObjectives.maximize_output_quality(),
        ]

        return MultiObjective(name=f"{domain}_default", objectives=objectives, method="weighted_sum")
