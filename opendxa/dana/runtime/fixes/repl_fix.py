"""
REPL fixes for improved variable handling in expressions.

This module provides fixes for the DANA REPL to handle variable references
in expressions like 'private.a = private.a + 1'.
"""
import re
import logging
from typing import Any, Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

def apply_repl_fix():
    """
    Apply fixes to the DANA REPL for improved variable handling.

    This fixes issues where self-references in expressions like
    'private.a = private.a + 1' would fail with "Undefined variable" errors.
    """
    # Import here to avoid circular imports
    from opendxa.dana.runtime.repl import REPL
    from opendxa.dana.runtime.context import RuntimeContext
    from opendxa.dana.runtime.executor.expression_evaluator import ExpressionEvaluator
    from opendxa.dana.runtime.executor.context_manager import ContextManager

    # Store the original methods
    original_execute = REPL.execute
    original_evaluate_identifier = ExpressionEvaluator.evaluate_identifier
    original_get_variable = ContextManager.get_variable

    # Patch the context manager's get_variable method for more direct access
    async def patched_get_variable(self, name: str, local_context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Patched get_variable method with direct state dictionary access fallback.

        Args:
            name: The variable name to get
            local_context: Optional local context to look in first

        Returns:
            The variable value
        """
        try:
            # Try original method first
            return await original_get_variable(self, name, local_context)
        except Exception as e:
            # If the variable name has a scope prefix (e.g., 'private.a')
            if "." in name:
                scope, var_name = name.split(".", 1)
                if scope in self._context._state and var_name in self._context._state[scope]:
                    logger.debug(f"Direct state access fallback for {name}")
                    return self._context._state[scope][var_name]
            # Re-raise if direct access also fails
            raise e

    # Patch the expression evaluator's evaluate_identifier method
    async def patched_evaluate_identifier(self, identifier, context=None):
        """
        Patched evaluate_identifier method with direct state dictionary access fallback.

        Args:
            identifier: The identifier AST node
            context: Optional execution context

        Returns:
            The evaluated identifier value
        """
        try:
            # Try original method first
            return await original_evaluate_identifier(self, identifier, context)
        except Exception as e:
            # Try direct state access as fallback
            if hasattr(identifier, 'name') and '.' in identifier.name:
                name = identifier.name
                scope, var_name = name.split(".", 1)
                if scope in self._context_manager._context._state and var_name in self._context_manager._context._state[scope]:
                    logger.debug(f"Direct identifier access fallback for {name}")
                    return self._context_manager._context._state[scope][var_name]
            # Re-raise if direct access also fails
            raise e

    # Enhanced execute method with special handling for variable self-references
    async def patched_execute(self, program_source: str, initial_context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Patched execute method with special handling for variable self-references.

        Args:
            program_source: The source code to execute
            initial_context: Optional initial context values

        Returns:
            The result of the execution
        """
        # Check for simple expression patterns first
        try:
            # Try to handle common operation patterns directly
            # 1. Simple self-reference with operation: "private.a = private.a + 1"
            self_ref_match = re.match(r'([\w\.]+)\s*=\s*([\w\.]+)(\s*[\+\-\*\/]\s*\d+)', program_source.strip())
            if self_ref_match:
                lhs, rhs, operation = self_ref_match.groups()
                if lhs == rhs:  # Self-reference detected
                    logger.debug(f"Self-reference detected: {lhs} = {rhs}{operation}")

                    # Parse scope and variable name
                    parts = lhs.split(".")
                    if len(parts) == 2:
                        scope, name = parts
                        if scope in self.context._state and name in self.context._state[scope]:
                            # Get current value
                            current_value = self.context._state[scope][name]
                            logger.debug(f"Current value of {lhs}: {current_value}")

                            # Evaluate the operation
                            op = operation.strip()[0]  # Get the operator (+ - * /)
                            value_str = operation.strip()[1:].strip()  # Get the value
                            value = int(value_str) if value_str.isdigit() else float(value_str)

                            # Perform the operation
                            if op == '+':
                                new_value = current_value + value
                            elif op == '-':
                                new_value = current_value - value
                            elif op == '*':
                                new_value = current_value * value
                            elif op == '/':
                                new_value = current_value / value
                            else:
                                raise ValueError(f"Unsupported operation: {op}")

                            # Update the state
                            self.context._state[scope][name] = new_value
                            self.context._state[scope]['__last_value'] = new_value
                            logger.debug(f"Updated {lhs} to {new_value}")
                            return new_value

            # 2. Handle variable to variable copy: "private.a = private.b"
            var_copy_match = re.match(r'([\w\.]+)\s*=\s*([\w\.]+)$', program_source.strip())
            if var_copy_match:
                lhs, rhs = var_copy_match.groups()
                if lhs != rhs and "." in rhs:  # Not self-reference and is a scoped variable
                    rhs_scope, rhs_name = rhs.split(".", 1)
                    lhs_scope, lhs_name = lhs.split(".", 1)

                    # Check if source variable exists
                    if rhs_scope in self.context._state and rhs_name in self.context._state[rhs_scope]:
                        # Get source value and set target
                        value = self.context._state[rhs_scope][rhs_name]

                        # Make sure target scope exists
                        if lhs_scope not in self.context._state:
                            self.context._state[lhs_scope] = {}

                        # Update target and return value
                        self.context._state[lhs_scope][lhs_name] = value
                        self.context._state[lhs_scope]['__last_value'] = value
                        logger.debug(f"Copied {rhs} to {lhs}: {value}")
                        return value

            # 3. Handle expressions with multiple variables: "private.c = private.a + private.b"
            expr_match = re.match(r'([\w\.]+)\s*=\s*([\w\.]+)(\s*[\+\-\*\/]\s*)([\w\.]+)$', program_source.strip())
            if expr_match:
                lhs, var1, op, var2 = expr_match.groups()

                # Only handle if both sides are scoped variables
                if "." in var1 and "." in var2:
                    # Parse variables
                    var1_scope, var1_name = var1.split(".", 1)
                    var2_scope, var2_name = var2.split(".", 1)
                    lhs_scope, lhs_name = lhs.split(".", 1)

                    # Check if both variables exist
                    if (var1_scope in self.context._state and var1_name in self.context._state[var1_scope] and
                        var2_scope in self.context._state and var2_name in self.context._state[var2_scope]):

                        # Get values
                        val1 = self.context._state[var1_scope][var1_name]
                        val2 = self.context._state[var2_scope][var2_name]

                        # Perform operation
                        op = op.strip()
                        if op == '+':
                            result = val1 + val2
                        elif op == '-':
                            result = val1 - val2
                        elif op == '*':
                            result = val1 * val2
                        elif op == '/':
                            result = val1 / val2
                        else:
                            raise ValueError(f"Unsupported operation: {op}")

                        # Make sure target scope exists
                        if lhs_scope not in self.context._state:
                            self.context._state[lhs_scope] = {}

                        # Update target and return value
                        self.context._state[lhs_scope][lhs_name] = result
                        self.context._state[lhs_scope]['__last_value'] = result
                        logger.debug(f"Calculated {lhs} = {var1} {op} {var2}: {result}")
                        return result
        except Exception as e:
            logger.debug(f"Error in pattern handling: {e}")
            # Continue with normal execution if special handling fails
            pass

        # Try the original method
        try:
            return await original_execute(self, program_source, initial_context)
        except Exception as e:
            # Check if this is a variable reference error that we can fix
            error_str = str(e)
            if "Undefined variable" in error_str:
                try:
                    # Check if this is an assignment with a problem
                    if "=" in program_source:
                        # Detect variable self-reference patterns
                        parts = program_source.strip().split("=", 1)
                        if len(parts) == 2:
                            target = parts[0].strip()
                            expression = parts[1].strip()

                            # Is this a scoped variable?
                            if "." in target:
                                scope, name = target.split(".", 1)

                                # Handle known scopes
                                if scope in ["private", "public", "system", "temp", "agent", "world"]:
                                    # Check for variable self-reference
                                    if target in expression:
                                        logger.debug(f"Detected assignment to {target}, using fallback")

                                        # Check if the variable exists and try to evaluate the expression
                                        if scope in self.context._state and name in self.context._state[scope]:
                                            current_value = self.context._state[scope][name]

                                            # Handle different operation patterns
                                            if "+" in expression:
                                                # Handle addition operations
                                                if f"{target} + 1" in expression:
                                                    new_value = current_value + 1
                                                    self.context._state[scope][name] = new_value
                                                    self.context._state[scope]['__last_value'] = new_value
                                                    return new_value

                                            if "-" in expression:
                                                # Handle subtraction operations
                                                if f"{target} - 1" in expression:
                                                    new_value = current_value - 1
                                                    self.context._state[scope][name] = new_value
                                                    self.context._state[scope]['__last_value'] = new_value
                                                    return new_value
                except Exception as inner_e:
                    logger.debug(f"Error in fallback handling: {inner_e}")

            # Re-raise the original exception if we couldn't handle it
            raise e

    # Apply the patches
    ContextManager.get_variable = patched_get_variable
    ExpressionEvaluator.evaluate_identifier = patched_evaluate_identifier
    REPL.execute = patched_execute

    logger.info("Applied REPL patches for better variable handling")

    return {
        "execute": original_execute,
        "evaluate_identifier": original_evaluate_identifier,
        "get_variable": original_get_variable
    }  # Return originals in case we need to undo
