"""
Trailer Processing Module for Dana Language Parsing.

This module provides focused, single-responsibility classes for handling
different types of trailers in method chaining and expression processing.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.ast import (
    AttributeAccess,
    Expression,
    FunctionCall,
    ObjectFunctionCall,
    SubscriptExpression,
    Location,
)
from dana.common.exceptions import SandboxError


class TrailerValidationError(SandboxError):
    """Raised when trailer validation fails."""

    pass


class TrailerValidator:
    """Validates trailer structure and content."""

    @staticmethod
    def validate_function_call_trailer(trailer: Any) -> None:
        """Validate function call trailer structure."""
        if trailer is None:
            return  # Empty arguments are valid

        if not hasattr(trailer, "data"):
            raise TrailerValidationError(f"Function call trailer missing 'data' attribute: {type(trailer)}")

        if trailer.data != "arguments":
            raise TrailerValidationError(f"Expected 'arguments', got '{trailer.data}'")

    @staticmethod
    def validate_attribute_trailer(trailer: Any) -> None:
        """Validate attribute access trailer structure."""
        if not hasattr(trailer, "type"):
            raise TrailerValidationError(f"Attribute trailer missing 'type' attribute: {type(trailer)}")

        if trailer.type != "NAME":
            raise TrailerValidationError(f"Expected 'NAME', got '{trailer.type}'")

        if not hasattr(trailer, "value"):
            raise TrailerValidationError("Attribute trailer missing 'value' attribute")


class FunctionCallHandler:
    """Handles function call trailer processing."""

    def __init__(self, transformer):
        self.transformer = transformer
        self.validator = TrailerValidator()

    def handle_function_call(self, current_base: Expression, trailer: Any) -> ObjectFunctionCall | FunctionCall:
        """
        Handle function call trailers.

        Args:
            current_base: The current base expression
            trailer: Function call trailer (arguments or None)

        Returns:
            ObjectFunctionCall for method calls, FunctionCall for regular calls

        Raises:
            TrailerValidationError: If trailer structure is invalid
        """
        self.validator.validate_function_call_trailer(trailer)

        # Process function arguments
        if trailer is not None and hasattr(trailer, "children"):
            args = self.transformer._process_function_arguments(trailer.children)
        else:
            args = {"__positional": []}  # Empty arguments

        # Check if current_base is AttributeAccess (method call pattern)
        if isinstance(current_base, AttributeAccess):
            return self._create_method_call(current_base, args)
        else:
            return self._create_function_call(current_base, args)

    def _create_method_call(self, attribute_access: AttributeAccess, args: dict[str, Any]) -> ObjectFunctionCall:
        """Create ObjectFunctionCall for method calls."""
        object_expr = attribute_access.object
        method_name = attribute_access.attribute

        return ObjectFunctionCall(
            object=object_expr, method_name=method_name, args=args, location=getattr(attribute_access, "location", None)
        )

    def _create_function_call(self, base: Expression, args: dict[str, Any]) -> FunctionCall:
        """Create FunctionCall for regular function calls."""
        name = getattr(base, "name", None)
        if not isinstance(name, str):
            name = str(base)

        return FunctionCall(name=name, args=args, location=getattr(base, "location", None))


class AttributeAccessHandler:
    """Handles attribute access trailer processing."""

    def __init__(self, transformer):
        self.transformer = transformer
        self.validator = TrailerValidator()

    def handle_attribute_access(self, current_base: Expression, trailer: Any) -> AttributeAccess:
        """
        Handle attribute access trailers.

        Args:
            current_base: The current base expression
            trailer: Attribute access trailer with NAME type

        Returns:
            AttributeAccess node

        Raises:
            TrailerValidationError: If trailer structure is invalid
        """
        self.validator.validate_attribute_trailer(trailer)

        # Get location from the trailer token (where the attribute is)
        location = None
        if hasattr(trailer, "line") and hasattr(trailer, "column"):
            location = Location(line=trailer.line, column=trailer.column, source=getattr(self.transformer, "current_filename", ""))

        return AttributeAccess(object=current_base, attribute=trailer.value, location=location)


class IndexingHandler:
    """Handles indexing and slicing trailer processing."""

    def __init__(self, transformer):
        self.transformer = transformer

    def handle_indexing(self, current_base: Expression, trailer: Any) -> SubscriptExpression:
        """
        Handle indexing/slicing trailers.

        Args:
            current_base: The current base expression
            trailer: Indexing/slicing trailer

        Returns:
            SubscriptExpression node
        """
        return SubscriptExpression(object=current_base, index=trailer, location=getattr(current_base, "location", None))


class ChainMetrics:
    """Tracks and analyzes method chain metrics."""

    def __init__(self):
        self.chain_length_warning_threshold = 20
        self.chain_length_error_threshold = 50

    def analyze_chain(self, trailers: list[Any]) -> dict[str, Any]:
        """
        Analyze method chain for metrics and optimization opportunities.

        Args:
            trailers: List of trailer elements

        Returns:
            Dictionary with chain analysis results
        """
        chain_length = len(trailers)
        trailer_types = self._count_trailer_types(trailers)

        analysis = {"length": chain_length, "types": trailer_types, "warnings": [], "errors": []}

        # Check for performance warnings
        if chain_length >= self.chain_length_warning_threshold:
            warning_msg = f"Long method chain detected: {chain_length} operations (threshold: {self.chain_length_warning_threshold})"
            analysis["warnings"].append(warning_msg)
            DANA_LOGGER.warning(warning_msg)

        # Check for errors
        if chain_length >= self.chain_length_error_threshold:
            error_msg = f"Extremely long method chain: {chain_length} operations (limit: {self.chain_length_error_threshold})"
            analysis["errors"].append(error_msg)

        return analysis

    def _count_trailer_types(self, trailers: list[Any]) -> dict[str, int]:
        """Count different types of trailers in the chain."""
        counts = {"function_calls": 0, "attribute_access": 0, "indexing": 0, "unknown": 0}

        for trailer in trailers:
            if (hasattr(trailer, "data") and trailer.data == "arguments") or trailer is None:
                counts["function_calls"] += 1
            elif hasattr(trailer, "type") and trailer.type == "NAME":
                counts["attribute_access"] += 1
            elif trailer is not None:
                counts["indexing"] += 1
            else:
                counts["unknown"] += 1

        return counts


class TrailerProcessor:
    """
    Main trailer processor that orchestrates different handler types.

    This class implements the sequential trailer processing logic that enables
    proper method chaining by maintaining state through each operation.
    """

    def __init__(self, transformer):
        self.transformer = transformer
        self.function_handler = FunctionCallHandler(transformer)
        self.attribute_handler = AttributeAccessHandler(transformer)
        self.indexing_handler = IndexingHandler(transformer)
        self.metrics = ChainMetrics()

    def process_trailers(self, base: Expression, trailers: list[Any]) -> Expression:
        """
        Process trailers sequentially to handle method chaining.

        This is the main entry point that replaces the original trailer method
        logic with a cleaner, more maintainable approach.

        Args:
            base: Base expression to start the chain
            trailers: List of trailer elements to process

        Returns:
            Final expression after processing all trailers

        Raises:
            TrailerValidationError: If any trailer is invalid
            SandboxError: If chain length exceeds limits
        """
        # Analyze chain metrics
        analysis = self.metrics.analyze_chain(trailers)

        # Check for errors that should prevent processing
        if analysis["errors"]:
            raise SandboxError(f"Method chain too long: {analysis['errors'][0]}")

        # Process trailers sequentially
        current_base = base

        for i, trailer in enumerate(trailers):
            try:
                current_base = self._process_single_trailer(current_base, trailer, i)
            except Exception as e:
                # Add context to errors
                raise SandboxError(f"Error processing trailer {i + 1}/{len(trailers)}: {str(e)}") from e

        return current_base

    def _process_single_trailer(self, current_base: Expression, trailer: Any, position: int) -> Expression:
        """
        Process a single trailer element.

        Args:
            current_base: Current base expression
            trailer: Trailer to process
            position: Position in trailer list (for error reporting)

        Returns:
            Updated expression after processing this trailer
        """
        # Case 1: Function call - ( ... ) or empty arguments (None)
        if (hasattr(trailer, "data") and trailer.data == "arguments") or trailer is None:
            return self.function_handler.handle_function_call(current_base, trailer)

        # Case 2: Attribute access - .NAME
        elif hasattr(trailer, "type") and trailer.type == "NAME":
            return self.attribute_handler.handle_attribute_access(current_base, trailer)

        # Case 3: Indexing/Slicing - [ ... ]
        else:
            return self.indexing_handler.handle_indexing(current_base, trailer)
