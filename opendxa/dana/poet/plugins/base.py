"""
POET Plugin Base Classes

Defines the abstract base classes and interfaces for POET plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class POETPlugin(ABC):
    """
    Abstract base class for all POET plugins.

    Plugins provide domain-specific intelligence for the POET framework,
    implementing the perceive-operate-enforce-train loop with specialized
    knowledge and optimizations.
    """

    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Get unique plugin identifier.

        Returns:
            str: Unique name for this plugin
        """
        pass

    @abstractmethod
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """
        Process and enhance function inputs with domain intelligence.

        Args:
            args: Original positional arguments
            kwargs: Original keyword arguments

        Returns:
            Dict with 'args' and 'kwargs' keys containing processed arguments
        """
        pass

    @abstractmethod
    def validate_output(self, result: Any, context: Dict[str, Any]) -> Any:
        """
        Validate and potentially modify function output.

        Args:
            result: Function execution result
            context: Execution context including inputs and metadata

        Returns:
            Validated (and potentially modified) result
        """
        pass

    def get_performance_optimizations(self) -> Dict[str, Any]:
        """
        Get domain-specific performance optimizations.

        Returns:
            Dict containing optimization parameters like timeout_multiplier,
            retry_strategy, cache_enabled, etc.
        """
        return {}

    def get_learning_hints(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide domain-specific learning guidance for POET training.

        Args:
            execution_context: Current execution context

        Returns:
            Dict containing learning parameters like parameter_bounds,
            learning_rate, convergence_threshold, etc.
        """
        return {}

    def cleanup(self) -> None:
        """
        Cleanup plugin resources.

        Called when plugin is being unloaded or system is shutting down.
        """
        pass

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get comprehensive plugin information.

        Returns:
            Dict containing plugin metadata, capabilities, version, etc.
        """
        return {
            "name": self.get_plugin_name(),
            "type": "poet_plugin",
            "version": getattr(self, "__version__", "unknown"),
            "author": getattr(self, "__author__", "unknown"),
            "capabilities": ["process_inputs", "validate_output"],
        }

    # Learning Integration Methods (Optional - for backwards compatibility)

    def receive_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Receive feedback about plugin performance for domain learning.

        Args:
            feedback: ExecutionFeedback containing performance metrics,
                     user feedback, and execution context

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation does nothing.
        """
        pass

    def update_from_learning(self, learning_insights: Dict[str, Any]) -> None:
        """
        Update plugin behavior based on learning insights.

        Args:
            learning_insights: Learning insights from cross-plugin coordination
                              or advanced learning algorithms

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation does nothing.
        """
        pass

    def get_domain_metrics(self, execution_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract domain-specific metrics for learning from execution results.

        Args:
            execution_result: Complete execution result including function output,
                            performance metrics, and execution context

        Returns:
            Dict mapping metric names to float values for learning analysis

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation returns empty dict.
        """
        return {}

    def adapt_parameters(self, current_params: Dict[str, Any], performance_history: List[float]) -> Dict[str, Any]:
        """
        Adapt domain-specific parameters based on performance history.

        Args:
            current_params: Current plugin configuration parameters
            performance_history: Recent performance scores for trend analysis

        Returns:
            Updated parameters for improved domain performance

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation returns parameters unchanged.
        """
        return current_params

    def get_learnable_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get plugin parameters that can be learned/optimized.

        Returns:
            Dict mapping parameter names to their metadata:
            - current_value: Current parameter value
            - range: Tuple of (min, max) for valid values
            - type: Parameter type ('continuous', 'discrete', 'categorical')
            - impact: Description of what this parameter affects

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation returns empty dict.
        """
        return {}

    def apply_learned_parameters(self, learned_params: Dict[str, Any]) -> None:
        """
        Apply learned parameters to plugin behavior.

        Args:
            learned_params: Parameters learned through the learning system

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation does nothing.
        """
        pass

    def get_learning_status(self) -> Dict[str, Any]:
        """
        Get current learning status and statistics for this plugin.

        Returns:
            Dict containing learning status information:
            - learning_enabled: Whether plugin supports learning
            - parameters_learned: Number of parameters being optimized
            - learning_progress: Learning convergence status
            - performance_trend: Recent performance trend

        Note:
            This is an optional method for learning-enabled plugins.
            Default implementation returns basic status.
        """
        return {
            "learning_enabled": False,
            "parameters_learned": 0,
            "learning_progress": "not_applicable",
            "performance_trend": "stable",
        }
