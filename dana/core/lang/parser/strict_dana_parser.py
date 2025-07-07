"""Strict Dana Parser with enhanced AST validation.

This module provides a variant of the DanaParser that enforces strict AST validation.
It is a drop-in replacement for DanaParser with additional options for validation.
"""

from typing import Any, cast

from lark import Tree

from dana.core.lang.ast import Program
from dana.core.lang.parser.dana_parser import DanaParser
from dana.core.lang.parser.utils.ast_validator import AstValidator


class StrictDanaParser(DanaParser, AstValidator):
    """
    A stricter version of DanaParser that enforces AST validation.

    This parser is identical to DanaParser but adds options for enforcing
    that no Lark Tree nodes remain in the AST after transformation.
    """

    def __init__(self, strict_validation: bool = False, **kwargs):
        """
        Initialize the parser with optional strict validation.

        Args:
            strict_validation: If True, raises an exception if Tree nodes
                               are found in the AST after transformation
            **kwargs: Additional arguments to pass to DanaParser.__init__
        """
        super().__init__(**kwargs)
        self.strict_validation = strict_validation

    def transform(self, parse_tree: Tree, do_type_check: bool = False) -> Program:
        """
        Transform a parse tree into an AST with enhanced validation.

        This overrides the DanaParser.transform method to add validation
        that can optionally be strict (raise exceptions on invalid ASTs).

        Args:
            parse_tree: The parse tree to transform
            do_type_check: Whether to perform type checking

        Returns:
            The transformed and validated AST

        Raises:
            TypeError: If self.strict_validation is True and Tree nodes are found
        """
        # Transform the parse tree into AST nodes
        self.debug("Transforming parse tree to AST")
        ast = cast(Program, self.transformer.transform(parse_tree))

        # Set the source text on the program
        ast.source_text = self.program_text

        self.debug(f"Successfully parsed program with {len(ast.statements)} statements")

        # Validate the AST
        valid, _ = self.validate_ast(ast, strict=self.strict_validation)

        # Perform type checking if enabled and parsing was successful
        if do_type_check and ast.statements:
            from dana.core.lang.parser.utils.type_checker import TypeChecker

            TypeChecker.check_types(ast)

        return ast

    def parse(self, program_text: str, do_transform: bool = True, do_type_check: bool = False, strict: bool | None = None) -> Any:
        """
        Parse a Dana program string into an AST with enhanced validation.

        This extends the DanaParser.parse method to add a strict option
        that can override the parser's default strict_validation setting.

        Args:
            program_text: The program text to parse
            do_transform: Whether to perform transformation to AST
            do_type_check: Whether to perform type checking
            strict: If not None, overrides self.strict_validation

        Returns:
            A parse tree or AST
        """
        # Store original strict setting if we need to temporarily override it
        original_strict = self.strict_validation
        if strict is not None:
            self.strict_validation = strict

        try:
            # Call the parent's parse method
            return super().parse(program_text, do_transform, do_type_check)
        finally:
            # Restore the original strict setting
            if strict is not None:
                self.strict_validation = original_strict


def create_parser(strict: bool = False, **kwargs) -> DanaParser:
    """
    Factory function to create either a regular or strict Dana parser.

    Args:
        strict: If True, creates a StrictDanaParser with strict_validation=True
               If False, creates a regular DanaParser
        **kwargs: Additional arguments to pass to the parser constructor

    Returns:
        A DanaParser or StrictDanaParser instance
    """
    if strict:
        return StrictDanaParser(strict_validation=True, **kwargs)
    else:
        return DanaParser(**kwargs)
