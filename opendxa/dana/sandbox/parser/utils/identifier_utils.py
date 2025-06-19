"""
Common utilities for identifier validation in Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""


def is_valid_identifier(term: str) -> bool:
    """
    Check if a term is a valid Python/Dana identifier.

    A valid identifier must:
    - Start with a letter (a-z, A-Z) or underscore (_)
    - Contain only letters, digits, and underscores
    - Support dotted notation (e.g., "obj.attr", "local.var")

    Args:
        term: The term to check

    Returns:
        True if the term is a valid identifier, False otherwise

    Examples:
        >>> is_valid_identifier("x")
        True
        >>> is_valid_identifier("question_2")
        True
        >>> is_valid_identifier("_private")
        True
        >>> is_valid_identifier("obj.attr")
        True
        >>> is_valid_identifier("123invalid")
        False
        >>> is_valid_identifier("with-dash")
        False
        >>> is_valid_identifier("")
        False
    """
    if not term:
        return False

    # Handle dotted identifiers (e.g., "local.var", "obj.attr")
    parts = term.split(".")
    for part in parts:
        if not part:  # Empty part (consecutive dots)
            return False
        # Check if each part is a valid identifier
        if not (part.replace("_", "").isalnum() and (part[0].isalpha() or part[0] == "_")):
            return False

    return True
