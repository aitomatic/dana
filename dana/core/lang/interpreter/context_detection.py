"""
Context Detection Library for Semantic Function Dispatch

This module provides utilities for analyzing AST to detect expected return types
for context-aware function execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import Assignment, FunctionCall, TypeHint


class ContextType(Enum):
    """Types of contexts that can be detected."""

    ASSIGNMENT = "assignment"
    FUNCTION_PARAMETER = "function_parameter"
    RETURN_VALUE = "return_value"
    CONDITIONAL = "conditional"
    EXPRESSION = "expression"
    FUNCTION_CALL = "function_call"  # NEW: For function call contexts like cast()
    UNKNOWN = "unknown"


@dataclass
class TypeContext:
    """Represents a detected type context."""

    expected_type: str
    context_type: ContextType
    confidence: float  # 0.0 to 1.0
    source_node: Any  # AST node that provided the context
    metadata: dict[str, Any]  # Additional context information

    def __str__(self) -> str:
        return f"TypeContext(type={self.expected_type}, context={self.context_type.value}, confidence={self.confidence:.2f})"


class ContextDetector(Loggable):
    """Detects type contexts from AST analysis."""

    def __init__(self):
        super().__init__()
        self._context_cache: dict[str, TypeContext] = {}

    def detect_assignment_context(self, assignment_node: Assignment) -> TypeContext | None:
        """Detect type context from typed assignment.

        Args:
            assignment_node: Assignment AST node

        Returns:
            TypeContext if type hint is present, None otherwise
        """
        if not isinstance(assignment_node, Assignment):
            self.debug(f"Expected Assignment node, got {type(assignment_node)}")
            return None

        if assignment_node.type_hint is None:
            self.debug("No type hint found in assignment")
            return None

        if not isinstance(assignment_node.type_hint, TypeHint):
            self.debug(f"Expected TypeHint, got {type(assignment_node.type_hint)}")
            return None

        type_name = assignment_node.type_hint.name
        self.debug(f"Detected assignment context: {type_name}")

        return TypeContext(
            expected_type=type_name,
            context_type=ContextType.ASSIGNMENT,
            confidence=1.0,  # Explicit type hints have highest confidence
            source_node=assignment_node,
            metadata={"target": str(assignment_node.target), "explicit_hint": True},
        )

    def detect_function_call_context(self, func_call_node: FunctionCall) -> TypeContext | None:
        """Detect type context from function calls, specifically cast() calls.

        Args:
            func_call_node: FunctionCall AST node

        Returns:
            TypeContext if cast() call with type argument is detected, None otherwise
        """
        if not isinstance(func_call_node, FunctionCall):
            self.debug(f"Expected FunctionCall node, got {type(func_call_node)}")
            return None

        # Check if this is a cast() function call
        if func_call_node.name != "cast":
            return None

        # Check if cast() has at least 2 arguments (target_type, value)
        if not hasattr(func_call_node, "args") or not func_call_node.args:
            self.debug("cast() call has no arguments")
            return None

        # Extract arguments - cast() should have (target_type, value)
        args = func_call_node.args
        if isinstance(args, dict) and "__positional" in args:
            positional_args = args["__positional"]
        elif isinstance(args, list):
            positional_args = args
        else:
            self.debug(f"Unexpected args format in cast() call: {type(args)}")
            return None

        if len(positional_args) < 2:
            self.debug(f"cast() call has insufficient arguments: {len(positional_args)}")
            return None

        # The first argument should be the target type
        # __positional is always a list according to the AST structure
        target_type_arg = positional_args[0]  # type: ignore

        # Extract type name from the target type argument
        if hasattr(target_type_arg, "name"):
            type_name = target_type_arg.name
        elif hasattr(target_type_arg, "value"):
            type_name = target_type_arg.value
        else:
            self.debug(f"Cannot extract type name from cast() argument: {target_type_arg}")
            return None

        self.debug(f"Detected cast() function call context: {type_name}")

        return TypeContext(
            expected_type=type_name,
            context_type=ContextType.FUNCTION_CALL,
            confidence=0.95,  # High confidence for explicit cast() calls
            source_node=func_call_node,
            metadata={"function_name": "cast", "cast_target_type": type_name, "explicit_cast": True},
        )

    def detect_function_parameter_context(self, param_name: str, param_type: str) -> TypeContext:
        """Detect type context from function parameter.

        Args:
            param_name: Parameter name
            param_type: Parameter type string

        Returns:
            TypeContext for the parameter
        """
        self.debug(f"Detected parameter context: {param_name}: {param_type}")

        return TypeContext(
            expected_type=param_type,
            context_type=ContextType.FUNCTION_PARAMETER,
            confidence=0.9,  # High confidence for explicit parameters
            source_node=None,
            metadata={"parameter_name": param_name, "explicit_hint": True},
        )

    def detect_conditional_context(self, condition_node: Any) -> TypeContext:
        """Detect boolean context from conditional statements.

        Args:
            condition_node: AST node used in conditional

        Returns:
            TypeContext indicating boolean expected type
        """
        self.debug("Detected conditional context (boolean expected)")

        return TypeContext(
            expected_type="bool",
            context_type=ContextType.CONDITIONAL,
            confidence=0.8,  # High confidence - conditionals expect boolean
            source_node=condition_node,
            metadata={"implicit_boolean": True, "usage": "conditional_expression"},
        )

    def infer_context_from_usage(self, variable_name: str, usage_context: str) -> TypeContext | None:
        """Infer type context from variable usage patterns.

        Args:
            variable_name: Name of the variable
            usage_context: Context description (e.g., "arithmetic", "string_concat")

        Returns:
            TypeContext if inference is possible, None otherwise
        """
        # Simple inference patterns
        inference_patterns = {
            "arithmetic": ("int", 0.6),
            "string_concat": ("str", 0.7),
            "list_access": ("list", 0.7),
            "dict_access": ("dict", 0.7),
            "iteration": ("list", 0.6),
        }

        if usage_context in inference_patterns:
            expected_type, confidence = inference_patterns[usage_context]
            self.debug(f"Inferred context for {variable_name}: {expected_type} (confidence: {confidence})")

            return TypeContext(
                expected_type=expected_type,
                context_type=ContextType.EXPRESSION,
                confidence=confidence,
                source_node=None,
                metadata={"variable_name": variable_name, "usage_pattern": usage_context, "inferred": True},
            )

        return None

    def get_cached_context(self, cache_key: str) -> TypeContext | None:
        """Get cached context by key.

        Args:
            cache_key: Unique key for the context

        Returns:
            Cached TypeContext if found, None otherwise
        """
        return self._context_cache.get(cache_key)

    def cache_context(self, cache_key: str, context: TypeContext) -> None:
        """Cache a detected context.

        Args:
            cache_key: Unique key for the context
            context: TypeContext to cache
        """
        self._context_cache[cache_key] = context
        self.debug(f"Cached context: {cache_key} -> {context}")

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()
        self.debug("Context cache cleared")

    def get_cache_size(self) -> int:
        """Get the current cache size."""
        return len(self._context_cache)

    def detect_current_context(self, context: Any) -> TypeContext | None:
        """Detect type context from current execution environment.

        Args:
            context: Execution context (SandboxContext or similar)

        Returns:
            TypeContext if detectable, None otherwise
        """
        try:
            # Check for assignment type set by AssignmentHandler
            if hasattr(context, "get"):
                current_assignment_type = context.get("system:__current_assignment_type")
                if current_assignment_type is not None:
                    # Handle both Python types and Dana struct type names
                    if hasattr(current_assignment_type, "__name__"):
                        # Python type (int, str, etc.)
                        type_name = current_assignment_type.__name__
                        metadata = {"source": "assignment_handler", "python_type": current_assignment_type}
                    else:
                        # Dana struct type name (string)
                        type_name = str(current_assignment_type)
                        metadata = {"source": "assignment_handler", "dana_struct_type": type_name}

                    self.debug(f"Found assignment type in context: {type_name}")
                    return TypeContext(
                        expected_type=type_name,
                        context_type=ContextType.ASSIGNMENT,
                        confidence=1.0,  # Highest confidence - direct from assignment
                        source_node=None,
                        metadata=metadata,
                    )

            # Try to get current AST node being executed
            if hasattr(context, "get_current_node"):
                current_node = context.get_current_node()
                if isinstance(current_node, Assignment) and current_node.type_hint:
                    return self.detect_assignment_context(current_node)
                elif isinstance(current_node, FunctionCall):
                    return self.detect_function_call_context(current_node)

            # Try to infer from execution context
            return self._infer_from_execution_context(context)

        except Exception as e:
            self.debug(f"Could not detect current context: {e}")
            return None

    def _infer_from_execution_context(self, context: Any) -> TypeContext | None:
        """Infer type context from execution environment.

        Args:
            context: Execution context

        Returns:
            TypeContext if inferable, None otherwise
        """
        try:
            # Check if we're in an assignment expression
            if hasattr(context, "get_execution_stack"):
                execution_stack = context.get_execution_stack()

                for frame in reversed(execution_stack):
                    if hasattr(frame, "node"):
                        if isinstance(frame.node, Assignment) and frame.node.type_hint:
                            return self.detect_assignment_context(frame.node)
                        elif isinstance(frame.node, FunctionCall):
                            return self.detect_function_call_context(frame.node)

            # Check for assignment context in the sandbox state
            if hasattr(context, "_state") and hasattr(context._state, "current_assignment"):
                assignment = context._state.current_assignment
                if assignment and hasattr(assignment, "type_hint") and assignment.type_hint:
                    return self.detect_assignment_context(assignment)

            # Fallback: Check context metadata
            if hasattr(context, "metadata") and isinstance(context.metadata, dict):
                expected_type = context.metadata.get("expected_type")
                if expected_type:
                    self.debug(f"Found expected type in metadata: {expected_type}")
                    return TypeContext(
                        expected_type=expected_type,
                        context_type=ContextType.EXPRESSION,
                        confidence=0.7,  # Medium confidence for metadata
                        source_node=None,
                        metadata={"source": "context_metadata"},
                    )

        except Exception as e:
            self.debug(f"Error inferring from execution context: {e}")

        return None


class ContextAnalyzer(Loggable):
    """High-level context analysis utilities."""

    def __init__(self):
        super().__init__()
        self.detector = ContextDetector()

    def analyze_assignment_chain(self, assignments: list[Assignment]) -> list[TypeContext]:
        """Analyze a chain of assignments for context patterns.

        Args:
            assignments: List of Assignment nodes

        Returns:
            List of detected TypeContext objects
        """
        contexts = []

        for assignment in assignments:
            context = self.detector.detect_assignment_context(assignment)
            if context:
                contexts.append(context)

        self.info(f"Analyzed {len(assignments)} assignments, found {len(contexts)} contexts")
        return contexts

    def find_strongest_context(self, contexts: list[TypeContext]) -> TypeContext | None:
        """Find the context with highest confidence.

        Args:
            contexts: List of TypeContext objects

        Returns:
            TypeContext with highest confidence, or None if empty
        """
        if not contexts:
            return None

        strongest = max(contexts, key=lambda c: c.confidence)
        self.debug(f"Strongest context: {strongest}")
        return strongest

    def merge_contexts(self, contexts: list[TypeContext]) -> TypeContext | None:
        """Merge multiple contexts into a single representative context.

        Args:
            contexts: List of TypeContext objects to merge

        Returns:
            Merged TypeContext or None if no consensus
        """
        if not contexts:
            return None

        if len(contexts) == 1:
            return contexts[0]

        # Group by expected type
        type_groups = {}
        for context in contexts:
            type_name = context.expected_type
            if type_name not in type_groups:
                type_groups[type_name] = []
            type_groups[type_name].append(context)

        # Find most common type
        most_common_type = max(type_groups.keys(), key=lambda t: len(type_groups[t]))
        most_common_contexts = type_groups[most_common_type]

        # Calculate average confidence
        avg_confidence = sum(c.confidence for c in most_common_contexts) / len(most_common_contexts)

        # Use the highest confidence context as base
        base_context = max(most_common_contexts, key=lambda c: c.confidence)

        merged = TypeContext(
            expected_type=most_common_type,
            context_type=base_context.context_type,
            confidence=avg_confidence,
            source_node=base_context.source_node,
            metadata={
                "merged_from": len(most_common_contexts),
                "consensus_strength": len(most_common_contexts) / len(contexts),
                **base_context.metadata,
            },
        )

        self.debug(f"Merged {len(contexts)} contexts into: {merged}")
        return merged


# Convenience functions for easy access
def detect_assignment_context(assignment_node: Assignment) -> TypeContext | None:
    """Convenience function to detect assignment context."""
    detector = ContextDetector()
    return detector.detect_assignment_context(assignment_node)


def detect_conditional_context(condition_node: Any) -> TypeContext:
    """Convenience function to detect conditional context."""
    detector = ContextDetector()
    return detector.detect_conditional_context(condition_node)


def analyze_contexts(assignments: list[Assignment]) -> list[TypeContext]:
    """Convenience function to analyze multiple assignments."""
    analyzer = ContextAnalyzer()
    return analyzer.analyze_assignment_chain(assignments)
