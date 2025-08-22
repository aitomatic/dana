"""
Pythonic Function Factory for Dana built-in functions.

This module provides a factory for creating Pythonic built-in function wrappers
using a central dispatch approach instead of individual function files.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from enum import Enum
from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.runtime_scopes import RuntimeScopes
from dana.core.concurrency import LazyPromise
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.sandbox_context import SandboxContext
from dana.registry.function_registry import FunctionMetadata, FunctionRegistry

from .type_wrapper import create_type_wrapper


class UnsupportedReason(Enum):
    """Reasons why certain built-in functions are not supported."""

    SECURITY_RISK = "security_risk"
    FILE_SYSTEM_ACCESS = "file_system_access"
    NETWORK_ACCESS = "network_access"
    SYSTEM_MODIFICATION = "system_modification"
    ARBITRARY_CODE_EXECUTION = "arbitrary_code_execution"
    MEMORY_SAFETY = "memory_safety"
    COMPLEXITY = "complexity"
    DEPRECATED = "deprecated"


class PythonicBuiltinsFactory:
    """Factory for creating Pythonic built-in function wrappers."""

    @staticmethod
    def _smart_max(*args):
        """Smart max wrapper that supports both max(iterable) and max(a, b, ...) syntax."""
        # Resolve any Promise objects in arguments
        from dana.core.concurrency import resolve_if_promise

        resolved_args = [resolve_if_promise(arg) for arg in args]

        if len(resolved_args) == 0:
            raise TypeError("max expected at least 1 argument, got 0")
        elif len(resolved_args) == 1:
            # Single argument case
            if isinstance(resolved_args[0], list | tuple | set):
                if len(resolved_args[0]) == 0:
                    raise ValueError("max() arg is an empty sequence")
                return max(resolved_args[0])  # max([1,2,3]) or max((1,2,3)) or max({1,2,3})
            else:
                # Single non-iterable argument: just return it
                return resolved_args[0]  # max(42) returns 42
        else:
            # Multiple arguments case
            return max(*resolved_args)  # max(1,2,3) or max(1,2)

    @staticmethod
    def _smart_min(*args):
        """Smart min wrapper that supports both min(iterable) and min(a, b, ...) syntax."""
        # Resolve any Promise objects in arguments
        from dana.core.concurrency import resolve_if_promise

        resolved_args = [resolve_if_promise(arg) for arg in args]

        if len(resolved_args) == 0:
            raise TypeError("min expected at least 1 argument, got 0")
        elif len(resolved_args) == 1:
            # Single argument case
            if isinstance(resolved_args[0], list | tuple | set):
                if len(resolved_args[0]) == 0:
                    raise ValueError("min() arg is an empty sequence")
                return min(resolved_args[0])  # min([1,2,3]) or min((1,2,3)) or min({1,2,3})
            else:
                # Single non-iterable argument: just return it
                return resolved_args[0]  # min(42) returns 42
        else:
            # Multiple arguments case
            return min(*resolved_args)  # min(1,2,3) or min(1,2)

    @staticmethod
    def _smart_sum(*args):
        """Smart sum wrapper that supports both sum(iterable) and sum(iterable, start) syntax."""
        # Resolve any Promise objects in arguments
        from dana.core.concurrency import resolve_if_promise

        resolved_args = [resolve_if_promise(arg) for arg in args]

        if len(resolved_args) == 1:
            return sum(resolved_args[0])  # sum([1,2,3])
        elif len(resolved_args) == 2:
            return sum(resolved_args[0], resolved_args[1])  # sum([1,2,3], 10)
        else:
            # This should not happen due to signature validation, but just in case
            raise TypeError(f"sum expected 1 or 2 arguments, got {len(resolved_args)}")

    # Configuration-driven approach with type validation
    FUNCTION_CONFIGS = {
        # Numeric functions
        "len": {
            "func": len,
            "types": [list, dict, str, tuple, set, LazyPromise],
            "doc": "Return the length of an object",
            "signatures": [(list,), (dict,), (str,), (tuple,), (set,), (LazyPromise,)],
        },
        # Smart wrappers for flexible argument handling
        "sum": {
            "func": sum,
            "types": [],  # Skip type validation - smart wrapper handles it
            "doc": "Return the sum of a sequence of numbers, optionally with a start value",
            "signatures": [
                (list,),
                (tuple,),
                (set,),
                (list, int),
                (list, float),
                (tuple, int),
                (tuple, float),
                (set, int),
                (set, float),
                (type({}.keys()),),
                (type({}.values()),),
            ],  # Allow list/tuple/set with optional start
        },
        "max": {
            "func": max,
            "types": [],  # Skip type validation - smart wrapper handles it
            "doc": "Return the largest item in an iterable or among multiple arguments",
            "signatures": [],  # Skip signature validation - smart wrapper handles it
        },
        "min": {
            "func": min,
            "types": [],  # Skip type validation - smart wrapper handles it
            "doc": "Return the smallest item in an iterable or among multiple arguments",
            "signatures": [],  # Skip signature validation - smart wrapper handles it
        },
        # Original basic versions (strict iterable-only)
        "basic_sum": {
            "func": sum,
            "types": [list, tuple, set],
            "doc": "Return the sum of a sequence of numbers (strict iterable-only version)",
            "signatures": [(list,), (tuple,), (set,)],
        },
        "basic_max": {
            "func": max,
            "types": [list, tuple, set],
            "doc": "Return the largest item in an iterable (strict iterable-only version)",
            "signatures": [(list,), (tuple,), (set,)],
        },
        "basic_min": {
            "func": min,
            "types": [list, tuple, set],
            "doc": "Return the smallest item in an iterable (strict iterable-only version)",
            "signatures": [(list,), (tuple,), (set,)],
        },
        "abs": {
            "func": abs,
            "types": [int, float, LazyPromise],
            "doc": "Return the absolute value of a number",
            "signatures": [(int,), (float,), (LazyPromise,)],
        },
        "round": {
            "func": round,
            "types": [float, int, LazyPromise],
            "doc": "Round a number to a given precision",
            "signatures": [(float,), (int,), (float, int), (LazyPromise,)],
        },
        # Type conversion functions
        "int": {
            "func": int,
            "types": [str, float, bool, LazyPromise],
            "doc": "Convert a value to an integer",
            "signatures": [(int,), (str,), (float,), (bool,), (LazyPromise,)],
        },
        "float": {
            "func": float,
            "types": [str, int, bool, LazyPromise],
            "doc": "Convert a value to a float",
            "signatures": [(str,), (int,), (bool,), (LazyPromise,)],
        },
        "bool": {
            "func": lambda v: PythonicBuiltinsFactory._semantic_bool_wrapper(v),
            "types": [str, int, float, list, dict, LazyPromise],
            "doc": "Convert a value to a boolean with semantic understanding",
            "signatures": [(str,), (int,), (float,), (list,), (dict,), (LazyPromise,)],
        },
        "type": {
            # SECURITY: Dana's type() function returns a secure wrapper object.
            # This provides rich type information while maintaining security boundaries
            # and preventing introspection attacks on internal Python type system details.
            "func": lambda v: create_type_wrapper(v),
            "types": [object, LazyPromise],
            "doc": "Return a secure type wrapper with rich type information (e.g., 'ResourceInstance[User]', 'StructInstance[Point]'). Provides safe access to type details while maintaining sandbox security.",
            "signatures": [(object,), (LazyPromise,)],
        },
        # Collection functions
        "sorted": {
            "func": sorted,
            "types": [list, tuple, set, LazyPromise],
            "doc": "Return a new sorted list from an iterable",
            "signatures": [(list,), (tuple,), (set,), (LazyPromise,)],
        },
        "reversed": {
            "func": reversed,
            "types": [list, tuple, str, LazyPromise],
            "doc": "Return a reverse iterator",
            "signatures": [(list,), (tuple,), (str,), (LazyPromise,)],
        },
        "enumerate": {
            "func": enumerate,
            "types": [list, tuple, str, LazyPromise],
            "doc": "Return an enumerate object",
            "signatures": [(list,), (tuple,), (str,), (LazyPromise,)],
        },
        # Logic functions
        "all": {
            "func": all,
            "types": [list, tuple, set, LazyPromise],
            "doc": "Return True if all elements are true",
            "signatures": [(list,), (tuple,), (set,), (LazyPromise,)],
        },
        "any": {
            "func": any,
            "types": [list, tuple, set, LazyPromise],
            "doc": "Return True if any element is true",
            "signatures": [(list,), (tuple,), (set,), (LazyPromise,)],
        },
        # Range function
        "range": {"func": range, "types": [int], "doc": "Return a range object", "signatures": [(int,), (int, int), (int, int, int)]},
        # List constructor
        "list": {
            "func": list,
            "types": [list, tuple, set, str, range, type(reversed([])), type({}.keys()), type({}.values()), type({}.items()), LazyPromise],
            "doc": "Convert an iterable to a list",
            "signatures": [
                (),  # Empty list: list()
                (list,),
                (tuple,),
                (set,),
                (str,),
                (range,),
                (type(reversed([])),),
                (type(enumerate([])),),
                (type({}.keys()),),
                (type({}.values()),),
                (type({}.items()),),
                (LazyPromise,),
            ],
        },
        # Set constructor
        "set": {
            "func": set,
            "types": [list, tuple, set, str, range, type(reversed([])), type({}.keys()), type({}.values()), type({}.items()), LazyPromise],
            "doc": "Convert an iterable to a set (removes duplicates) or create an empty set",
            "signatures": [
                (),  # Empty set: set()
                (list,),
                (tuple,),
                (set,),
                (str,),
                (range,),
                (type(reversed([])),),
                (type(enumerate([])),),
                (type({}.keys()),),
                (type({}.values()),),
                (type({}.items()),),
                (LazyPromise,),
            ],
        },
        # String conversion function
        "str": {
            "func": str,
            "types": [int, float, bool, list, dict, tuple, set, type(None), LazyPromise],
            "doc": "Convert a value to a string",
            "signatures": [(int,), (float,), (bool,), (list,), (dict,), (tuple,), (set,), (type(None),), (LazyPromise,)],
        },
    }

    # Explicitly unsupported functions with clear rationales
    UNSUPPORTED_FUNCTIONS = {
        # File system access
        "open": {
            "reason": UnsupportedReason.FILE_SYSTEM_ACCESS,
            "message": "File operations are not allowed in Dana sandbox for security reasons",
            "alternative": "Use Dana's built-in file handling functions or request file access through the sandbox API",
        },
        "input": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Interactive input is not supported in Dana sandbox environments",
            "alternative": "Pass data through function parameters or context variables",
        },
        # Code execution
        "eval": {
            "reason": UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            "message": "Dynamic code evaluation poses severe security risks",
            "alternative": "Use Dana's expression evaluation or predefined functions",
        },
        "exec": {
            "reason": UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            "message": "Dynamic code execution is prohibited for security",
            "alternative": "Structure your code using Dana functions and control flow",
        },
        "compile": {
            "reason": UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            "message": "Code compilation is not allowed in sandbox",
            "alternative": "Use Dana's built-in parsing and execution mechanisms",
        },
        # System access
        "globals": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Global namespace access bypasses Dana's scoping security",
            "alternative": "Use Dana's scoped variables (private:, public:, local:, system:)",
        },
        "locals": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Local namespace access bypasses Dana's scoping security",
            "alternative": "Use Dana's scoped variables and function parameters",
        },
        "vars": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Variable namespace inspection bypasses security boundaries",
            "alternative": "Use explicit variable access through Dana's scoping system",
        },
        "dir": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Object introspection can reveal sensitive implementation details",
            "alternative": "Use documented APIs and Dana's type system",
        },
        # Import system
        "__import__": {
            "reason": UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            "message": "Dynamic imports can load arbitrary code",
            "alternative": "Use Dana's import system with pre-approved modules",
        },
        # Memory and object manipulation
        "id": {
            "reason": UnsupportedReason.MEMORY_SAFETY,
            "message": "Memory address access can leak sensitive information",
            "alternative": "Use object equality comparisons or unique identifiers",
        },
        "hash": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Hash values can be used for timing attacks or fingerprinting",
            "alternative": "Use Dana's built-in comparison and equality functions",
        },
        "memoryview": {
            "reason": UnsupportedReason.MEMORY_SAFETY,
            "message": "Direct memory access bypasses sandbox protections",
            "alternative": "Use Dana's safe data structures and operations",
        },
        # Attribute manipulation
        "getattr": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Dynamic attribute access can bypass access controls",
            "alternative": "Use explicit attribute access or Dana's property system",
        },
        "setattr": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Dynamic attribute modification can compromise object integrity",
            "alternative": "Use explicit assignment or Dana's property system",
        },
        "delattr": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Dynamic attribute deletion can break object contracts",
            "alternative": "Use explicit deletion or Dana's lifecycle management",
        },
        "hasattr": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Attribute existence checks can reveal implementation details",
            "alternative": "Use try/catch blocks or explicit interface checks",
        },
        # Class and type manipulation
        "isinstance": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Type checking is handled by Dana's type system",
            "alternative": "Use Dana's built-in type validation and conversion functions",
        },
        "issubclass": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Class hierarchy inspection is not needed in Dana",
            "alternative": "Use Dana's interface and trait system",
        },
        # Advanced iteration
        "iter": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Iterator protocol is handled internally by Dana",
            "alternative": "Use for loops, list comprehensions, or Dana's iteration functions",
        },
        "next": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Manual iterator advancement is not needed in Dana",
            "alternative": "Use for loops or Dana's collection processing functions",
        },
        # Callable and function manipulation
        "callable": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Callable detection can reveal implementation details",
            "alternative": "Use explicit function calls or Dana's function registry",
        },
        # String and representation
        "repr": {
            "reason": UnsupportedReason.SECURITY_RISK,
            "message": "Object representation can leak sensitive information",
            "alternative": "Use explicit string conversion or Dana's formatting functions",
        },
        "ascii": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "ASCII representation is rarely needed in modern applications",
            "alternative": "Use standard string operations and Unicode handling",
        },
        # Numeric functions with security implications
        "pow": {
            "reason": UnsupportedReason.MEMORY_SAFETY,
            "message": "Arbitrary exponentiation can cause memory exhaustion",
            "alternative": "Use the ** operator with reasonable limits or math functions",
        },
        "divmod": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Division with remainder is available through / and % operators",
            "alternative": "Use division (/) and modulo (%) operators separately",
        },
        # Format and conversion
        "format": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "String formatting is handled by Dana's f-string system",
            "alternative": "Use f-strings or Dana's string formatting functions",
        },
        "bin": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Binary representation is rarely needed in business logic",
            "alternative": "Use bitwise operations or specialized encoding functions",
        },
        "oct": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Octal representation is rarely needed in modern applications",
            "alternative": "Use decimal or hexadecimal representations",
        },
        "hex": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Hexadecimal representation should use specialized formatting",
            "alternative": "Use Dana's number formatting functions or string operations",
        },
        # Object lifecycle
        "object": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Base object creation is handled by Dana's object system",
            "alternative": "Use Dana's data structures (dict, list) or define custom types",
        },
        # Slice objects
        "slice": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Slice objects are created automatically by slice syntax",
            "alternative": "Use slice syntax [start:end:step] directly",
        },
        # Property and descriptor
        "property": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Property creation is handled by Dana's property system",
            "alternative": "Use Dana's getter/setter syntax or computed properties",
        },
        # Class methods and static methods
        "classmethod": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Class methods are not part of Dana's function model",
            "alternative": "Use regular functions or Dana's module system",
        },
        "staticmethod": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Static methods are not needed in Dana's function model",
            "alternative": "Use regular functions in appropriate modules",
        },
        # Super and inheritance
        "super": {
            "reason": UnsupportedReason.COMPLEXITY,
            "message": "Inheritance is handled differently in Dana",
            "alternative": "Use Dana's composition and trait system",
        },
    }

    @classmethod
    def _resolve_promise_args(cls, args: tuple) -> tuple:
        """Resolve any LazyPromise objects in the arguments to their actual values."""
        resolved_args = []
        for arg in args:
            if isinstance(arg, LazyPromise):
                resolved_args.append(arg._ensure_resolved())
            else:
                resolved_args.append(arg)
        return tuple(resolved_args)

    @classmethod
    def _semantic_bool_wrapper(cls, value):
        """Enhanced boolean conversion with semantic understanding."""
        try:
            from dana.core.lang.interpreter.enhanced_coercion import semantic_bool

            return semantic_bool(value)
        except ImportError:
            # Fallback to standard bool if enhanced coercion is not available
            return bool(value)

    @classmethod
    def create_function(cls, name: str):
        """Create a Dana-compatible function wrapper."""
        # Check if function is explicitly unsupported
        if name in cls.UNSUPPORTED_FUNCTIONS:
            cls._raise_unsupported_error(name)

        if name not in cls.FUNCTION_CONFIGS:
            # Check if it's a known Python built-in that we haven't classified
            cls._handle_unknown_builtin(name)

        config = cls.FUNCTION_CONFIGS[name]
        python_func = config["func"]
        config["types"]
        signatures = config["signatures"]

        def dana_wrapper(context: SandboxContext, *args, **kwargs):
            # Resolve any LazyPromise objects in the arguments
            resolved_args = cls._resolve_promise_args(args)

            # Validate arguments against signatures
            cls._validate_args(name, resolved_args, signatures)

            # Execute the Python function with safety guards
            try:
                return cls._execute_with_guards(python_func, resolved_args)
            except Exception as e:
                raise SandboxError(f"Built-in function '{name}' failed: {str(e)}")

        dana_wrapper.__name__ = name
        dana_wrapper.__doc__ = config["doc"]
        return dana_wrapper

    @classmethod
    def _raise_unsupported_error(cls, name: str):
        """Raise a detailed error for unsupported functions."""
        config = cls.UNSUPPORTED_FUNCTIONS[name]
        reason = config["reason"]
        message = config["message"]
        alternative = config["alternative"]

        # Create a detailed error message with security context
        error_msg = f"""
Built-in function '{name}' is not supported in Dana sandbox.

Reason: {reason.value.replace("_", " ").title()}
Details: {message}

Alternative: {alternative}

For security and safety, Dana restricts access to certain Python built-ins.
This helps maintain a secure execution environment while providing
the functionality you need through safer alternatives.
        """.strip()

        raise SandboxError(error_msg)

    @classmethod
    def _handle_unknown_builtin(cls, name: str):
        """Handle unknown built-in functions with helpful guidance."""
        # List of common Python built-ins for better error messages
        python_builtins = {
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "breakpoint",
            "bytearray",
            "bytes",
            "callable",
            "chr",
            "classmethod",
            "compile",
            "complex",
            "delattr",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "eval",
            "exec",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "globals",
            "hasattr",
            "hash",
            "help",
            "hex",
            "id",
            "input",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "locals",
            "map",
            "max",
            "memoryview",
            "min",
            "next",
            "object",
            "oct",
            "open",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "vars",
            "zip",
        }

        if name in python_builtins:
            error_msg = f"""
Built-in function '{name}' is not available in Dana.

This function may be:
1. Explicitly unsupported for security reasons
2. Not yet implemented in Dana's built-in function set
3. Available through a different Dana function or syntax

Supported built-ins: {", ".join(sorted(cls.FUNCTION_CONFIGS.keys()))}

If you need this functionality, consider:
- Using an alternative from the supported built-ins list
- Implementing the logic using Dana's core functions
- Requesting this function be added to Dana's built-in set
            """.strip()
        else:
            error_msg = f"""
Function '{name}' is not a recognized built-in function.

Available built-ins: {", ".join(sorted(cls.FUNCTION_CONFIGS.keys()))}

If this is a custom function, make sure it's:
- Defined in your Dana code
- Imported from a module
- Available in the current scope
            """.strip()

        raise SandboxError(error_msg)

    @classmethod
    def _validate_args(cls, name: str, args: tuple, expected_signatures: list[tuple]):
        """Validate arguments against expected type signatures."""
        # Skip validation for functions with empty signatures (smart wrappers handle their own validation)
        if not expected_signatures:
            return

        valid_signature = False

        for signature in expected_signatures:
            if len(args) == len(signature):
                if all(isinstance(arg, sig_type) for arg, sig_type in zip(args, signature, strict=False)):
                    valid_signature = True
                    break

        if not valid_signature:
            expected_arg_counts = sorted(set(len(sig) for sig in expected_signatures))
            actual_arg_count = len(args)

            # For "basic_" functions (strict validation versions), always show detailed signature errors
            if name.startswith("basic_"):
                arg_types = [type(arg).__name__ for arg in args]
                expected_sigs = [f"({', '.join(t.__name__ for t in sig)})" for sig in expected_signatures]
                raise TypeError(
                    f"Invalid arguments for '{name}': got ({', '.join(arg_types)}), expected one of: {', '.join(expected_sigs)}"
                )
            # Generate user-friendly error messages for smart wrapper functions
            elif actual_arg_count == 0 and min(expected_arg_counts) > 0:
                raise TypeError(
                    f"{name} expected at least {min(expected_arg_counts)} argument{'s' if min(expected_arg_counts) > 1 else ''}, got 0"
                )
            elif actual_arg_count > max(expected_arg_counts):
                raise TypeError(
                    f"{name} expected at most {max(expected_arg_counts)} argument{'s' if max(expected_arg_counts) > 1 else ''}, got {actual_arg_count}"
                )
            else:
                # Fall back to detailed signature error for type mismatches
                arg_types = [type(arg).__name__ for arg in args]
                expected_sigs = [f"({', '.join(t.__name__ for t in sig)})" for sig in expected_signatures]
                raise TypeError(
                    f"Invalid arguments for '{name}': got ({', '.join(arg_types)}), expected one of: {', '.join(expected_sigs)}"
                )

    @classmethod
    def _execute_with_guards(cls, func: callable, args: tuple):
        """Execute function with safety guards."""
        # TODO: Add timeout and memory limits for production
        # TODO: Consider subprocess isolation for high-security environments
        return func(*args)

    @classmethod
    def get_available_functions(cls) -> list[str]:
        """Get list of available function names."""
        return list(cls.FUNCTION_CONFIGS.keys())

    @classmethod
    def get_function_info(cls, name: str) -> dict[str, Any]:
        """Get information about a specific function."""
        if name not in cls.FUNCTION_CONFIGS:
            raise ValueError(f"Unknown function: {name}")
        return cls.FUNCTION_CONFIGS[name].copy()

    @classmethod
    def get_unsupported_functions(cls) -> list[str]:
        """Get list of explicitly unsupported function names."""
        return list(cls.UNSUPPORTED_FUNCTIONS.keys())

    @classmethod
    def get_unsupported_info(cls, name: str) -> dict[str, Any]:
        """Get information about why a function is unsupported."""
        if name not in cls.UNSUPPORTED_FUNCTIONS:
            raise ValueError(f"Function '{name}' is not in the unsupported list")
        return cls.UNSUPPORTED_FUNCTIONS[name].copy()

    @classmethod
    def is_supported(cls, name: str) -> bool:
        """Check if a function is supported."""
        return name in cls.FUNCTION_CONFIGS

    @classmethod
    def is_unsupported(cls, name: str) -> bool:
        """Check if a function is explicitly unsupported."""
        return name in cls.UNSUPPORTED_FUNCTIONS

    @classmethod
    def get_functions_by_reason(cls, reason: UnsupportedReason) -> list[str]:
        """Get all functions unsupported for a specific reason."""
        return [name for name, config in cls.UNSUPPORTED_FUNCTIONS.items() if config["reason"] == reason]

    @classmethod
    def get_security_report(cls) -> dict[str, Any]:
        """Generate a security report of function restrictions."""
        report = {
            "supported_functions": len(cls.FUNCTION_CONFIGS),
            "unsupported_functions": len(cls.UNSUPPORTED_FUNCTIONS),
            "unsupported_by_reason": {},
            "security_critical": [],
        }

        # Group by reason
        for reason in UnsupportedReason:
            functions = cls.get_functions_by_reason(reason)
            if functions:
                report["unsupported_by_reason"][reason.value] = functions

        # Identify security-critical restrictions
        security_reasons = [
            UnsupportedReason.SECURITY_RISK,
            UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            UnsupportedReason.FILE_SYSTEM_ACCESS,
            UnsupportedReason.NETWORK_ACCESS,
            UnsupportedReason.SYSTEM_MODIFICATION,
            UnsupportedReason.MEMORY_SAFETY,
        ]

        for reason in security_reasons:
            functions = cls.get_functions_by_reason(reason)
            report["security_critical"].extend(functions)

        return report


# Bind smart wrappers after class definition to avoid staticmethod.__func__ typing issues
PythonicBuiltinsFactory.FUNCTION_CONFIGS["sum"]["func"] = PythonicBuiltinsFactory._smart_sum
PythonicBuiltinsFactory.FUNCTION_CONFIGS["max"]["func"] = PythonicBuiltinsFactory._smart_max
PythonicBuiltinsFactory.FUNCTION_CONFIGS["min"]["func"] = PythonicBuiltinsFactory._smart_min


def do_register_py_builtins(registry: FunctionRegistry) -> None:
    """Register all Pythonic built-in functions using the factory.

    This function registers built-in functions with HIGHEST priority,
    ensuring the correct lookup order for safety and predictability:
    1. Built-in functions (highest priority - registered here)
    2. Core functions (medium priority)
    3. User-defined functions (lowest priority)

    Built-ins take precedence to prevent accidental shadowing of critical
    functions and maintain consistent behavior across Dana programs.

    Args:
        registry: The function registry to register functions with
    """
    factory = PythonicBuiltinsFactory()

    for function_name in factory.FUNCTION_CONFIGS:
        wrapper = factory.create_function(function_name)
        metadata = FunctionMetadata(source_file="<built-in>")
        metadata.context_aware = True
        metadata.is_public = True
        metadata.doc = factory.FUNCTION_CONFIGS[function_name]["doc"]

        # Register with overwrite=True to enforce built-in precedence
        # Built-in functions take precedence over user-defined functions for safety
        registry.register(
            name=function_name,
            func=wrapper,
            namespace=RuntimeScopes.SYSTEM,
            func_type=FunctionType.PYTHON,
            metadata=metadata,
            overwrite=True,  # Built-ins take precedence for safety
            trusted_for_context=True,  # Built-in functions are trusted to receive context
        )

    # Register handlers for explicitly unsupported functions
    # This provides better error messages than "function not found"
    for function_name in factory.UNSUPPORTED_FUNCTIONS:

        def create_unsupported_handler(name):
            def unsupported_handler(context: SandboxContext, *args, **kwargs):
                factory._raise_unsupported_error(name)

            unsupported_handler.__name__ = f"{name}_unsupported"
            return unsupported_handler

        handler = create_unsupported_handler(function_name)
        metadata = FunctionMetadata(source_file="<unsupported>")
        metadata.context_aware = True
        metadata.is_public = True  # Must be public to be callable (will raise error when called)
        metadata.doc = f"Unsupported function: {factory.UNSUPPORTED_FUNCTIONS[function_name]['message']}"

        # Register with overwrite=True to enforce built-in error handling precedence
        # Built-in error handlers take precedence for security
        registry.register(
            name=function_name,
            func=handler,
            namespace=RuntimeScopes.SYSTEM,
            func_type=FunctionType.PYTHON,
            metadata=metadata,
            overwrite=True,  # Built-in error handlers take precedence for security
            trusted_for_context=True,  # Error handlers are trusted to receive context
        )
