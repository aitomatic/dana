"""
Type inference system for IPV optimization.

This module provides the TypeInferenceEngine that can detect expected types
from various sources including AST analysis, runtime context, and assignment patterns.
"""

import ast
import inspect
import re
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin


class TypeInferenceEngine:
    """
    Engine for inferring expected types from various sources.

    The engine can detect types from:
    - AST analysis of assignment statements
    - Runtime type annotations
    - Variable assignment context
    - Generic type parameters
    """

    def __init__(self):
        self._type_cache: Dict[str, Type] = {}
        self._generic_cache: Dict[str, Dict[str, Any]] = {}

    def infer_type_from_context(self, context: Any, variable_name: Optional[str] = None) -> Optional[Type]:
        """
        Infer the expected type from execution context.

        Args:
            context: Execution context (e.g., SandboxContext, frame info)
            variable_name: Name of the variable being assigned to

        Returns:
            Inferred type or None if cannot be determined
        """
        # Try multiple inference strategies
        inferred_type = None

        # Strategy 1: Check if context has type annotation information
        if hasattr(context, "get_type_annotation"):
            inferred_type = context.get_type_annotation(variable_name)
            if inferred_type:
                return inferred_type

        # Strategy 2: Inspect the calling frame for type annotations
        if variable_name:
            inferred_type = self._infer_from_frame_annotations(variable_name)
            if inferred_type:
                return inferred_type

        # Strategy 3: Check for assignment patterns in source code
        if variable_name:
            inferred_type = self._infer_from_assignment_pattern(variable_name)
            if inferred_type:
                return inferred_type

        return None

    def infer_type_from_assignment(self, assignment_code: str) -> Optional[Type]:
        """
        Infer type from assignment statement code.

        Args:
            assignment_code: Python code containing assignment with type annotation

        Returns:
            Inferred type or None
        """
        try:
            # Parse the assignment code
            tree = ast.parse(assignment_code.strip())

            # Look for annotated assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign):
                    return self._ast_annotation_to_type(node.annotation)
                elif isinstance(node, ast.Assign):
                    # Check if there's a type comment
                    if hasattr(node, "type_comment") and node.type_comment:
                        return self._parse_type_comment(node.type_comment)

            return None

        except (SyntaxError, ValueError):
            return None

    def infer_type_from_string(self, type_string: str) -> Optional[Type]:
        """
        Infer type from string representation.

        Args:
            type_string: String representation of type (e.g., "float", "List[str]")

        Returns:
            Inferred type or None
        """
        try:
            # Handle basic types
            basic_types = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "dict": dict,
                "list": list,
                "tuple": tuple,
                "set": set,
                "bytes": bytes,
                "None": type(None),
                "Any": Any,
            }

            # Clean the type string
            type_string = type_string.strip()

            # Check basic types first
            if type_string in basic_types:
                return basic_types[type_string]

            # Handle generic types like List[str], Dict[str, int]
            return self._parse_generic_type(type_string)

        except Exception:
            return None

    def get_type_defaults(self, inferred_type: Type) -> Dict[str, Any]:
        """
        Get default IPV configuration for a specific type.

        Args:
            inferred_type: The inferred type

        Returns:
            Dictionary of default configuration values
        """
        from .base import ContextLevel, PrecisionLevel, ReliabilityLevel, SafetyLevel, StructureLevel

        # Type-specific defaults based on the design document
        type_defaults = {
            float: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
                "auto_cleaning": ["strip_text", "extract_numbers", "handle_currency"],
                "validation_rules": ["numeric_only", "decimal_format"],
            },
            int: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
                "auto_cleaning": ["extract_integers", "handle_text_numbers"],
                "validation_rules": ["integer_only", "no_decimals"],
            },
            bool: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
                "auto_cleaning": ["parse_yes_no", "parse_true_false", "parse_approved_rejected"],
                "validation_rules": ["boolean_only", "unambiguous"],
            },
            str: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.ORGANIZED,
                "context": ContextLevel.STANDARD,
                "auto_cleaning": ["remove_markdown", "clean_bullets", "clean_whitespace"],
                "validation_rules": ["string_format", "reasonable_length"],
            },
            dict: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.DETAILED,
                "auto_cleaning": ["validate_json", "fix_syntax_errors"],
                "validation_rules": ["valid_json", "consistent_structure"],
            },
            list: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.FORMATTED,
                "context": ContextLevel.STANDARD,
                "auto_cleaning": ["parse_arrays", "handle_bullet_points"],
                "validation_rules": ["array_format", "consistent_items"],
            },
        }

        # Get defaults for the specific type
        if inferred_type in type_defaults:
            return type_defaults[inferred_type]

        # Handle generic types
        origin_type = get_origin(inferred_type)
        if origin_type and origin_type in type_defaults:
            defaults = type_defaults[origin_type].copy()
            # Add generic type information
            defaults["generic_args"] = get_args(inferred_type)
            return defaults

        # Default fallback
        return {
            "reliability": ReliabilityLevel.HIGH,
            "precision": PrecisionLevel.SPECIFIC,
            "safety": SafetyLevel.MEDIUM,
            "structure": StructureLevel.ORGANIZED,
            "context": ContextLevel.STANDARD,
            "auto_cleaning": [],
            "validation_rules": [],
        }

    def is_generic_type(self, type_obj: Type) -> bool:
        """Check if a type is a generic type (e.g., List[str], Dict[str, int])."""
        return get_origin(type_obj) is not None

    def get_generic_info(self, type_obj: Type) -> Dict[str, Any]:
        """
        Get information about a generic type.

        Args:
            type_obj: Generic type object

        Returns:
            Dictionary with origin type and type arguments
        """
        if not self.is_generic_type(type_obj):
            return {"origin": type_obj, "args": []}

        return {"origin": get_origin(type_obj), "args": get_args(type_obj)}

    def _infer_from_frame_annotations(self, variable_name: str) -> Optional[Type]:
        """Infer type from frame annotations by inspecting the call stack."""
        try:
            # Get the calling frame (skip this function and the caller)
            frame = inspect.currentframe()
            for _ in range(3):  # Skip a few frames to get to the actual caller
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return None

            # Check local annotations
            if hasattr(frame, "f_locals") and "__annotations__" in frame.f_locals:
                annotations = frame.f_locals["__annotations__"]
                if variable_name in annotations:
                    return annotations[variable_name]

            # Check global annotations
            if hasattr(frame, "f_globals") and "__annotations__" in frame.f_globals:
                annotations = frame.f_globals["__annotations__"]
                if variable_name in annotations:
                    return annotations[variable_name]

            return None

        except Exception:
            return None

    def _infer_from_assignment_pattern(self, variable_name: str) -> Optional[Type]:
        """Infer type from assignment patterns in source code."""
        try:
            # Get the calling frame to access source code
            frame = inspect.currentframe()
            for _ in range(3):
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return None

            # Try to get source lines around the current line
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            # Read source file
            with open(filename) as f:
                lines = f.readlines()

            # Look for type annotations in nearby lines
            search_range = range(max(0, lineno - 5), min(len(lines), lineno + 5))
            for line_idx in search_range:
                line = lines[line_idx].strip()

                # Look for pattern: variable_name: type = ...
                pattern = rf"{re.escape(variable_name)}\s*:\s*([^=]+)\s*="
                match = re.search(pattern, line)
                if match:
                    type_str = match.group(1).strip()
                    return self.infer_type_from_string(type_str)

            return None

        except Exception:
            return None

    def _ast_annotation_to_type(self, annotation_node: ast.AST) -> Optional[Type]:
        """Convert AST annotation node to actual type."""
        try:
            if isinstance(annotation_node, ast.Name):
                # Simple type like 'str', 'int'
                return self.infer_type_from_string(annotation_node.id)
            elif isinstance(annotation_node, ast.Constant):
                # String literal type annotation
                return self.infer_type_from_string(str(annotation_node.value))
            elif isinstance(annotation_node, ast.Subscript):
                # Generic type like List[str]
                return self._parse_generic_from_ast(annotation_node)

            return None

        except Exception:
            return None

    def _parse_type_comment(self, type_comment: str) -> Optional[Type]:
        """Parse type from type comment."""
        return self.infer_type_from_string(type_comment.strip())

    def _parse_generic_type(self, type_string: str) -> Optional[Type]:
        """Parse generic type from string like 'List[str]' or 'Dict[str, int]'."""
        try:
            # Handle common generic patterns
            if type_string.startswith("List[") and type_string.endswith("]"):
                inner_type_str = type_string[5:-1].strip()
                inner_type = self.infer_type_from_string(inner_type_str)
                if inner_type:
                    return List[inner_type]  # type: ignore

            elif type_string.startswith("Dict[") and type_string.endswith("]"):
                inner_str = type_string[5:-1].strip()
                if "," in inner_str:
                    key_str, value_str = inner_str.split(",", 1)
                    key_type = self.infer_type_from_string(key_str.strip())
                    value_type = self.infer_type_from_string(value_str.strip())
                    if key_type and value_type:
                        return Dict[key_type, value_type]  # type: ignore

            elif type_string.startswith("Union[") and type_string.endswith("]"):
                inner_str = type_string[6:-1].strip()
                type_strs = [t.strip() for t in inner_str.split(",")]
                types = [self.infer_type_from_string(t) for t in type_strs]
                if all(types):
                    return Union[tuple(types)]  # type: ignore

            elif type_string.startswith("Optional[") and type_string.endswith("]"):
                inner_type_str = type_string[9:-1].strip()
                inner_type = self.infer_type_from_string(inner_type_str)
                if inner_type:
                    return Union[inner_type, type(None)]  # type: ignore

            return None

        except Exception:
            return None

    def _parse_generic_from_ast(self, subscript_node: ast.Subscript) -> Optional[Type]:
        """Parse generic type from AST subscript node."""
        try:
            # This is a simplified version - a full implementation would handle
            # more complex generic type structures
            if isinstance(subscript_node.value, ast.Name):
                base_type_name = subscript_node.value.id

                if base_type_name == "List":
                    if isinstance(subscript_node.slice, ast.Name):
                        inner_type = self.infer_type_from_string(subscript_node.slice.id)
                        if inner_type:
                            return List[inner_type]  # type: ignore

                elif base_type_name == "Dict":
                    # Handle Dict[key_type, value_type]
                    if isinstance(subscript_node.slice, ast.Tuple):
                        if len(subscript_node.slice.elts) == 2:
                            key_node, value_node = subscript_node.slice.elts
                            if isinstance(key_node, ast.Name) and isinstance(value_node, ast.Name):
                                key_type = self.infer_type_from_string(key_node.id)
                                value_type = self.infer_type_from_string(value_node.id)
                                if key_type and value_type:
                                    return Dict[key_type, value_type]  # type: ignore

            return None

        except Exception:
            return None
