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
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionRegistry
from dana.core.lang.sandbox_context import SandboxContext


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


class PythonicFunctionFactory:
    """Factory for creating Pythonic built-in function wrappers."""

    # Configuration-driven approach with type validation
    FUNCTION_CONFIGS = {
        # Numeric functions
        "len": {
            "func": len,
            "types": [list, dict, str, tuple],
            "doc": "Return the length of an object",
            "signatures": [(list,), (dict,), (str,), (tuple,)],
        },
        "sum": {"func": sum, "types": [list, tuple], "doc": "Return the sum of a sequence of numbers", "signatures": [(list,), (tuple,)]},
        "max": {"func": max, "types": [list, tuple], "doc": "Return the largest item in an iterable", "signatures": [(list,), (tuple,)]},
        "min": {"func": min, "types": [list, tuple], "doc": "Return the smallest item in an iterable", "signatures": [(list,), (tuple,)]},
        "abs": {"func": abs, "types": [int, float], "doc": "Return the absolute value of a number", "signatures": [(int,), (float,)]},
        "round": {
            "func": round,
            "types": [float, int],
            "doc": "Round a number to a given precision",
            "signatures": [(float,), (int,), (float, int)],
        },
        # Type conversion functions
        "int": {
            "func": int,
            "types": [str, float, bool],
            "doc": "Convert a value to an integer",
            "signatures": [(str,), (float,), (bool,)],
        },
        "float": {"func": float, "types": [str, int, bool], "doc": "Convert a value to a float", "signatures": [(str,), (int,), (bool,)]},
        "bool": {
            "func": lambda v: PythonicFunctionFactory._semantic_bool_wrapper(v),
            "types": [str, int, float, list, dict],
            "doc": "Convert a value to a boolean with semantic understanding",
            "signatures": [(str,), (int,), (float,), (list,), (dict,)],
        },
        "type": {
            # SECURITY: Dana's type() function is NOT the same as Python's type() function.
            # Returns string name instead of type object to prevent introspection attacks.
            # This is a deliberate sandbox security choice to prevent malicious code from
            # accessing type internals, performing isinstance checks, or gaining access
            # to class hierarchies and internal Python type system details.
            # Dana: type(obj) -> "str", Python: type(obj).__name__ -> "str"
            "func": lambda v: type(v).__name__,
            "types": [object],
            "doc": "Return the type name of a value as a string (e.g., 'int', 'list', 'dict'). SECURITY NOTE: Unlike Python's type(), this returns a string for sandbox security.",
            "signatures": [(object,)],
        },
        # Collection functions
        "sorted": {
            "func": sorted,
            "types": [list, tuple],
            "doc": "Return a new sorted list from an iterable",
            "signatures": [(list,), (tuple,)],
        },
        "reversed": {
            "func": reversed,
            "types": [list, tuple, str],
            "doc": "Return a reverse iterator",
            "signatures": [(list,), (tuple,), (str,)],
        },
        "enumerate": {
            "func": enumerate,
            "types": [list, tuple, str],
            "doc": "Return an enumerate object",
            "signatures": [(list,), (tuple,), (str,)],
        },
        # Logic functions
        "all": {"func": all, "types": [list, tuple], "doc": "Return True if all elements are true", "signatures": [(list,), (tuple,)]},
        "any": {"func": any, "types": [list, tuple], "doc": "Return True if any element is true", "signatures": [(list,), (tuple,)]},
        # Range function
        "range": {"func": range, "types": [int], "doc": "Return a range object", "signatures": [(int,), (int, int), (int, int, int)]},
        # List constructor
        "list": {
            "func": list,
            "types": [list, tuple, str, range, type(reversed([]))],
            "doc": "Convert an iterable to a list",
            "signatures": [(list,), (tuple,), (str,), (range,), (type(reversed([])),), (type(enumerate([])),)],
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
            # Validate arguments against signatures
            cls._validate_args(name, args, signatures)

            # Execute the Python function with safety guards
            try:
                return cls._execute_with_guards(python_func, args)
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
        valid_signature = False

        for signature in expected_signatures:
            if len(args) == len(signature):
                if all(isinstance(arg, sig_type) for arg, sig_type in zip(args, signature, strict=False)):
                    valid_signature = True
                    break

        if not valid_signature:
            arg_types = [type(arg).__name__ for arg in args]
            expected_sigs = [f"({', '.join(t.__name__ for t in sig)})" for sig in expected_signatures]
            raise TypeError(f"Invalid arguments for '{name}': got ({', '.join(arg_types)}), expected one of: {', '.join(expected_sigs)}")

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


def register_pythonic_builtins(registry: FunctionRegistry) -> None:
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
    factory = PythonicFunctionFactory()

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
            func_type=FunctionType.PYTHON,
            metadata=metadata,
            overwrite=True,  # Built-in error handlers take precedence for security
            trusted_for_context=True,  # Error handlers are trusted to receive context
        )
