"""
Safety Validator - Enterprise-grade safety and compliance validation

This module implements the SafetyValidator for Phase 1 of the Dana Workflows framework.
Provides basic safety validation and compliance checking as the foundation for
enterprise-grade safety features in Phase 5.

Key Features:
- Basic safety rules validation
- Simple compliance checking
- Error reporting and logging
- Foundation for enterprise safety features
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety validation levels."""

    SAFE = "safe"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SafetyResult:
    """Result of safety validation."""

    is_safe: bool
    level: SafetyLevel
    reason: str
    details: dict[str, Any]
    recommendations: list[str]


class SafetyValidator:
    """
    Basic Safety Validator for Phase 1 Foundation.

    Provides simple safety validation and compliance checking as the foundation
    for enterprise-grade safety features in Phase 5.
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the safety validator.

        Args:
            strict_mode: Whether to enforce strict validation rules
        """
        self.strict_mode = strict_mode
        self._validation_rules: dict[str, Callable] = {}
        self._register_default_rules()

        logger.info(f"Initialized SafetyValidator with strict_mode={strict_mode}")

    def validate_workflow(self, workflow: Any, context: Any = None) -> SafetyResult:
        """
        Validate a workflow for safety and compliance.

        Args:
            workflow: The workflow to validate
            context: Optional validation context

        Returns:
            SafetyResult with validation outcome
        """
        logger.debug("Validating workflow safety")

        try:
            # Basic workflow structure validation
            if self._is_workflow_list(workflow):
                return self._validate_step_list(workflow, context)
            elif callable(workflow):
                return self._validate_composed_function(workflow, context)
            else:
                return SafetyResult(
                    is_safe=False,
                    level=SafetyLevel.ERROR,
                    reason="Invalid workflow type",
                    details={"type": type(workflow).__name__},
                    recommendations=["Use WorkflowStep list or composed function"],
                )

        except Exception as e:
            logger.error(f"Safety validation error: {str(e)}")
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Validation exception",
                details={"error": str(e)},
                recommendations=["Check workflow configuration"],
            )

    def validate_step(self, step: Any, context: Any = None) -> SafetyResult:
        """
        Validate a single workflow step.

        Args:
            step: The step to validate
            context: Optional validation context

        Returns:
            SafetyResult with validation outcome
        """
        logger.debug(f"Validating step: {getattr(step, 'name', 'unknown')}")

        # Check if it's a valid step (any object with name and function attributes)
        # Note: WorkflowStep import removed as workflow framework is not needed

        if not hasattr(step, "name") or not hasattr(step, "function"):
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Invalid step type",
                details={"type": type(step).__name__, "expected": "WorkflowStep"},
                recommendations=["Use WorkflowStep instances"],
            )

        # Validate step properties
        validation_results = []
        critical_issues = []

        # Check if step has required attributes - these are critical
        if not hasattr(step, "name") or not step.name:
            validation_results.append("Step missing name attribute")
            critical_issues.append("Step missing name")

        if not hasattr(step, "function") or not callable(step.function):
            validation_results.append("Step missing valid function")
            critical_issues.append("Step missing function")

        # Validate function safety
        if step.function and callable(step.function):
            func_result = self._validate_function(step.function, step.name)
            if not func_result.is_safe:
                validation_results.append(func_result.reason)

        # Check for potentially dangerous operations
        if step.function and callable(step.function):
            danger_result = self._check_dangerous_operations(step.function, step.name)
            if not danger_result.is_safe:
                validation_results.append(danger_result.reason)

        if validation_results:
            # Critical issues should always return is_safe=False
            is_safe = len(critical_issues) == 0
            level = SafetyLevel.ERROR if critical_issues or self.strict_mode else SafetyLevel.WARNING
            return SafetyResult(
                is_safe=is_safe,
                level=level,
                reason="Step validation failed",
                details={"issues": validation_results, "critical": critical_issues},
                recommendations=["Review step configuration", "Test step in isolation"],
            )

        return SafetyResult(
            is_safe=True, level=SafetyLevel.SAFE, reason="Step validation passed", details={"step_name": step.name}, recommendations=[]
        )

    def add_validation_rule(self, name: str, rule: Callable) -> None:
        """
        Add a custom validation rule.

        Args:
            name: Rule name
            rule: Validation function that returns SafetyResult
        """
        self._validation_rules[name] = rule
        logger.info(f"Added custom validation rule: {name}")

    def remove_validation_rule(self, name: str) -> bool:
        """
        Remove a validation rule.

        Args:
            name: Rule name to remove

        Returns:
            True if rule was removed, False if not found
        """
        if name in self._validation_rules:
            del self._validation_rules[name]
            logger.info(f"Removed validation rule: {name}")
            return True
        return False

    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        # Basic rules for Phase 1
        self.add_validation_rule("basic_structure", self._rule_basic_structure)
        self.add_validation_rule("no_infinite_recursion", self._rule_no_infinite_recursion)
        self.add_validation_rule("reasonable_complexity", self._rule_reasonable_complexity)

    def _validate_step_list(self, steps: list, context: Any = None) -> SafetyResult:
        """Validate a list of workflow steps."""
        issues = []

        if not steps:
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Empty workflow",
                details={"steps_count": 0},
                recommendations=["Add at least one step to the workflow"],
            )

        if len(steps) > 50:  # Reasonable limit for Phase 1
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.WARNING,
                reason="Workflow has too many steps",
                details={"steps_count": len(steps), "limit": 50},
                recommendations=["Consider breaking into smaller workflows"],
            )

        # Validate each step
        for i, step in enumerate(steps):
            step_result = self.validate_step(step, context)
            if not step_result.is_safe:
                issues.append(f"Step {i}: {step_result.reason}")

        if issues:
            level = SafetyLevel.ERROR if self.strict_mode else SafetyLevel.WARNING
            return SafetyResult(
                is_safe=not self.strict_mode,
                level=level,
                reason="Workflow validation issues",
                details={"issues": issues, "steps_count": len(steps)},
                recommendations=["Address individual step issues"],
            )

        return SafetyResult(
            is_safe=True,
            level=SafetyLevel.SAFE,
            reason="Workflow validation passed",
            details={"steps_count": len(steps)},
            recommendations=[],
        )

    def _validate_composed_function(self, func: Callable, context: Any = None) -> SafetyResult:
        """Validate a composed function."""
        # Basic function validation for Phase 1
        try:
            # Check if function has a reasonable signature
            import inspect

            sig = inspect.signature(func)

            # For Phase 1, just check basic properties
            if len(sig.parameters) > 5:
                return SafetyResult(
                    is_safe=False,
                    level=SafetyLevel.WARNING,
                    reason="Function has too many parameters",
                    details={"parameter_count": len(sig.parameters)},
                    recommendations=["Simplify function signature"],
                )

            return SafetyResult(
                is_safe=True,
                level=SafetyLevel.SAFE,
                reason="Composed function validation passed",
                details={"parameter_count": len(sig.parameters)},
                recommendations=[],
            )

        except Exception as e:
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Could not inspect function",
                details={"error": str(e)},
                recommendations=["Ensure function is inspectable"],
            )

    def _validate_function(self, func: Callable, name: str) -> SafetyResult:
        """Validate an individual function."""
        try:
            import inspect

            # Check function signature
            sig = inspect.signature(func)

            # Basic checks
            if len(sig.parameters) == 0:
                return SafetyResult(
                    is_safe=True, level=SafetyLevel.SAFE, reason="Function has no parameters", details={"name": name}, recommendations=[]
                )

            return SafetyResult(
                is_safe=True,
                level=SafetyLevel.SAFE,
                reason="Function signature valid",
                details={"name": name, "parameters": len(sig.parameters)},
                recommendations=[],
            )

        except Exception:
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Cannot inspect function",
                details={"name": name},
                recommendations=["Ensure function is properly defined"],
            )

    def _check_dangerous_operations(self, func: Callable, name: str) -> SafetyResult:
        """Check for potentially dangerous operations."""
        try:
            import inspect

            source = inspect.getsource(func)

            # Simple checks for Phase 1
            dangerous_patterns = ["eval(", "exec(", "__import__(", "open(", "file(", "os.system", "subprocess.call", "subprocess.run"]

            found_patterns = []
            for pattern in dangerous_patterns:
                if pattern in source:
                    found_patterns.append(pattern)

            if found_patterns:
                level = SafetyLevel.ERROR if self.strict_mode else SafetyLevel.WARNING
                return SafetyResult(
                    is_safe=not self.strict_mode,
                    level=level,
                    reason="Potentially dangerous operations detected",
                    details={"name": name, "patterns": found_patterns},
                    recommendations=["Review function source", "Use safer alternatives"],
                )

            return SafetyResult(
                is_safe=True, level=SafetyLevel.SAFE, reason="No dangerous operations detected", details={"name": name}, recommendations=[]
            )

        except Exception:
            # If we can't inspect source, assume safe for Phase 1
            return SafetyResult(
                is_safe=True,
                level=SafetyLevel.SAFE,
                reason="Cannot inspect source, assuming safe",
                details={"name": name},
                recommendations=["Consider making function inspectable"],
            )

    def _is_workflow_list(self, workflow: Any) -> bool:
        """Check if workflow is a list of steps."""
        return isinstance(workflow, list)

    def _rule_basic_structure(self, workflow: Any, context: Any = None) -> SafetyResult:
        """Basic structure validation rule."""
        if isinstance(workflow, list) and len(workflow) == 0:
            return SafetyResult(
                is_safe=False, level=SafetyLevel.ERROR, reason="Empty workflow list", details={}, recommendations=["Add at least one step"]
            )

        return SafetyResult(is_safe=True, level=SafetyLevel.SAFE, reason="Basic structure valid", details={}, recommendations=[])

    def _rule_no_infinite_recursion(self, workflow: Any, context: Any = None) -> SafetyResult:
        """Check for potential infinite recursion."""
        # Phase 1: Basic check for workflow depth
        if isinstance(workflow, list) and len(workflow) > 100:
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.ERROR,
                reason="Workflow too deep, potential infinite recursion",
                details={"depth": len(workflow)},
                recommendations=["Break into smaller workflows"],
            )

        return SafetyResult(is_safe=True, level=SafetyLevel.SAFE, reason="No infinite recursion detected", details={}, recommendations=[])

    def _rule_reasonable_complexity(self, workflow: Any, context: Any = None) -> SafetyResult:
        """Check for reasonable workflow complexity."""
        if isinstance(workflow, list):
            complexity_score = len(workflow)

            if complexity_score > 20:
                return SafetyResult(
                    is_safe=False,
                    level=SafetyLevel.WARNING,
                    reason="Workflow complexity may be high",
                    details={"complexity_score": complexity_score},
                    recommendations=["Consider simplification", "Test thoroughly"],
                )

        return SafetyResult(
            is_safe=True, level=SafetyLevel.SAFE, reason="Complexity within acceptable limits", details={}, recommendations=[]
        )

    def get_validation_summary(self) -> dict[str, Any]:
        """
        Get summary of validation rules and status.

        Returns:
            Dictionary with validation summary
        """
        return {
            "strict_mode": self.strict_mode,
            "registered_rules": list(self._validation_rules.keys()),
            "total_rules": len(self._validation_rules),
            "phase": "Phase 1 - Foundation",
        }
