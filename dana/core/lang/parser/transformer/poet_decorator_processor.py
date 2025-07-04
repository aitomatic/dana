"""
POET Decorator Comment Processor

This module handles parsing of POET decorator comments in Dana code.
Uses comments that look like decorators: # @poet(domain="building_management")

Author: Dana Framework
"""

import ast
import re
from dataclasses import dataclass
from typing import Any

from dana.common.utils.logging import DANA_LOGGER


@dataclass
class POETDecoratorConfig:
    """Configuration extracted from a POET decorator comment."""

    domain: str | None = None
    timeout: float | None = None
    retries: int | None = None
    enable_training: bool = True
    collect_metrics: bool = True
    profile: str | None = None
    interrupts: str | None = None


class POETDecoratorProcessor:
    """Processes POET decorator comments and extracts configuration."""

    # Pattern to match POET decorator comments: # @poet(...)
    POET_DECORATOR_PATTERN = re.compile(r"^\s*#\s*@poet\s*(?:\((.*?)\))?\s*$", re.IGNORECASE | re.MULTILINE)

    def __init__(self):
        """Initialize the POET decorator processor."""
        self.logger = DANA_LOGGER.getChild(__name__)

    def extract_poet_config(self, comment: str) -> POETDecoratorConfig | None:
        """
        Extract POET configuration from a decorator comment.

        Args:
            comment: Comment string like "# @poet(domain='building_management')"

        Returns:
            POETDecoratorConfig if valid POET decorator, None otherwise
        """
        if not comment or not isinstance(comment, str):
            return None

        # Remove the # prefix and whitespace
        clean_comment = comment.lstrip("#").strip()

        # Check if it matches our POET decorator pattern
        match = self.POET_DECORATOR_PATTERN.match(f"# {clean_comment}")
        if not match:
            return None

        # Extract the arguments part (everything inside parentheses)
        args_str = match.group(1)
        if not args_str:
            # Empty decorator: # @poet()
            return POETDecoratorConfig()

        return self._parse_decorator_args(args_str)

    def _parse_decorator_args(self, args_str: str) -> POETDecoratorConfig | None:
        """
        Parse decorator arguments string into POETDecoratorConfig.

        Args:
            args_str: Arguments string like 'domain="building_management", timeout=30.0'

        Returns:
            POETDecoratorConfig with parsed values
        """
        try:
            # Create a safe evaluation context
            # We'll parse this as a Python function call to extract arguments
            fake_call = f"poet({args_str})"

            # Parse as Python AST to safely extract arguments
            try:
                tree = ast.parse(fake_call, mode="eval")
                call_node = tree.body

                if not isinstance(call_node, ast.Call):
                    self.logger.warning(f"Invalid POET decorator syntax: {args_str}")
                    return None

                return self._extract_args_from_call(call_node)

            except SyntaxError as e:
                self.logger.warning(f"Syntax error in POET decorator: {args_str} - {e}")
                return None

        except Exception as e:
            self.logger.error(f"Error parsing POET decorator args: {args_str} - {e}")
            return None

    def _extract_args_from_call(self, call_node: ast.Call) -> POETDecoratorConfig:
        """
        Extract arguments from AST Call node into POETDecoratorConfig.

        Args:
            call_node: AST Call node representing the decorator call

        Returns:
            POETDecoratorConfig with extracted values
        """
        config = POETDecoratorConfig()

        # Process keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg is None:
                continue  # Skip **kwargs

            value = self._extract_ast_value(keyword.value)

            # Map to config fields
            if keyword.arg == "domain" and isinstance(value, str):
                config.domain = value
            elif keyword.arg == "timeout" and isinstance(value, int | float):
                config.timeout = float(value)
            elif keyword.arg == "retries" and isinstance(value, int):
                config.retries = value
            elif keyword.arg == "enable_training" and isinstance(value, bool):
                config.enable_training = value
            elif keyword.arg == "collect_metrics" and isinstance(value, bool):
                config.collect_metrics = value
            elif keyword.arg == "profile" and isinstance(value, str):
                config.profile = value
            elif keyword.arg == "interrupts" and isinstance(value, str):
                config.interrupts = value
            else:
                self.logger.warning(f"Unknown POET decorator argument: {keyword.arg}={value}")

        # Process positional arguments (if any)
        if call_node.args:
            self.logger.warning("Positional arguments not supported in POET decorators, use keyword arguments")

        return config

    def _extract_ast_value(self, node: ast.AST) -> Any:
        """
        Extract Python value from AST node.

        Args:
            node: AST node representing a literal value

        Returns:
            Python value (str, int, float, bool, None)
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.NameConstant | ast.Name):
            if hasattr(node, "value"):
                return node.value
            elif hasattr(node, "id"):
                # Handle True, False, None
                if node.id == "True":
                    return True
                elif node.id == "False":
                    return False
                elif node.id == "None":
                    return None
                else:
                    return node.id
        else:
            self.logger.warning(f"Unsupported AST node type in POET decorator: {type(node)}")
            return None

    def find_poet_decorators_in_code(self, code: str) -> list[tuple[int, POETDecoratorConfig]]:
        """
        Find all POET decorator comments in code and return their line numbers and configs.

        Args:
            code: Dana source code

        Returns:
            List of (line_number, POETDecoratorConfig) tuples
        """
        decorators = []
        lines = code.split("\n")

        for line_num, line in enumerate(lines, 1):
            config = self.extract_poet_config(line)
            if config is not None:
                decorators.append((line_num, config))

        return decorators

    def apply_poet_to_function(self, function_name: str, config: POETDecoratorConfig) -> dict[str, Any]:
        """
        Convert POETDecoratorConfig to POET function parameters.

        Args:
            function_name: Name of the function to enhance
            config: POET configuration from decorator

        Returns:
            Dictionary of POET parameters
        """
        poet_params = {}

        if config.domain:
            poet_params["domain"] = config.domain
        if config.timeout is not None:
            poet_params["timeout"] = config.timeout
        if config.retries is not None:
            poet_params["retries"] = config.retries
        if config.profile:
            poet_params["profile"] = config.profile
        if config.interrupts:
            poet_params["interrupts"] = config.interrupts

        # Always include these
        poet_params["enable_training"] = config.enable_training
        poet_params["collect_metrics"] = config.collect_metrics

        return poet_params


# Global processor instance
_poet_processor = POETDecoratorProcessor()


def extract_poet_config(comment: str) -> POETDecoratorConfig | None:
    """
    Extract POET configuration from a decorator comment.

    Args:
        comment: Comment string like "# @poet(domain='building_management')"

    Returns:
        POETDecoratorConfig if valid POET decorator, None otherwise
    """
    return _poet_processor.extract_poet_config(comment)


def find_poet_decorators_in_code(code: str) -> list[tuple[int, POETDecoratorConfig]]:
    """
    Find all POET decorator comments in code.

    Args:
        code: Dana source code

    Returns:
        List of (line_number, POETDecoratorConfig) tuples
    """
    return _poet_processor.find_poet_decorators_in_code(code)
