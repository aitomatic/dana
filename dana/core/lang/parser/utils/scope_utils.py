"""
Scope utility functions for Dana language parsing.

This module provides utilities for handling Dana's scoping system,
including automatic scope insertion and scope validation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import ParseError


def insert_local_scope(parts: list[str] | str) -> Any:
    """Insert local scope prefix to parts if not already present.

    Args:
        parts: Either a string variable name or list of name parts

    Returns:
        Modified parts with local scope prefix if needed

    Raises:
        ParseError: If parts is invalid or contains dots for simple names
    """
    if isinstance(parts, str):
        if "." in parts:
            raise ParseError(f"Local variable must be a simple name: {parts}")
        return f"local:{parts}"
    elif isinstance(parts, list):
        if len(parts) == 0:
            raise ParseError("No local variable name provided")
        elif len(parts) > 1:
            # For nested identifiers, keep as is
            return parts
        else:
            parts.insert(0, "local")
            return parts
    else:
        raise ParseError(f"Invalid type for local variable: {type(parts)}")


def has_scope_prefix(name: str) -> bool:
    """Check if a variable name already has a scope prefix.

    Args:
        name: Variable name to check

    Returns:
        True if name has a scope prefix (local:, private:, public:, system:)
    """
    scope_prefixes = ["local:", "private:", "public:", "system:"]
    return any(name.startswith(prefix) for prefix in scope_prefixes)


def extract_scope_and_name(name: str) -> tuple[str | None, str]:
    """Extract scope prefix and variable name from a scoped variable.

    Args:
        name: Variable name potentially with scope prefix

    Returns:
        Tuple of (scope_prefix, variable_name). If no scope, returns (None, name)
    """
    scope_prefixes = ["local", "private", "public", "system"]

    for prefix in scope_prefixes:
        if name.startswith(f"{prefix}:"):
            return prefix, name[len(prefix) + 1 :]

    return None, name


def validate_scope_name(scope: str) -> bool:
    """Validate that a scope name is valid.

    Args:
        scope: Scope name to validate

    Returns:
        True if scope is valid
    """
    valid_scopes = {"local", "private", "public", "system"}
    return scope in valid_scopes
