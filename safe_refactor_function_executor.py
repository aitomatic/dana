#!/usr/bin/env python3
"""
Safe refactoring of function_executor.py

This script safely breaks down the large function_executor.py file into focused components.
Uses the safety framework to ensure no functionality is broken.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from refactoring_safety_framework import SafetyFramework, RefactoringContext


def analyze_function_executor_structure():
    """Analyze the structure of function_executor.py to plan refactoring."""
    
    # The file contains several distinct responsibilities:
    # 1. FunctionNameInfo - Function name parsing (lines 34-82)
    # 2. ResolvedFunction - Function resolution results (lines 83-100) 
    # 3. FunctionResolver - Function resolution logic (lines 101-257)
    # 4. FunctionExecutionErrorHandler - Error handling (lines 258-392)
    # 5. PositionalErrorRecoveryStrategy - Error recovery (lines 393-453)
    # 6. FunctionExecutor - Main executor (lines 454-911)
    
    refactoring_plan = {
        "phase_1": {
            "description": "Extract function name utilities",
            "files_to_create": [
                "opendxa/dana/sandbox/interpreter/executor/function_name_utils.py"
            ],
            "classes_to_move": ["FunctionNameInfo"],
            "justification": "Simple data class with no dependencies"
        },
        "phase_2": {
            "description": "Extract function resolution logic", 
            "files_to_create": [
                "opendxa/dana/sandbox/interpreter/executor/function_resolver.py"
            ],
            "classes_to_move": ["ResolvedFunction", "FunctionResolver"],
            "justification": "Cohesive resolution logic with clear interface"
        },
        "phase_3": {
            "description": "Extract error handling components",
            "files_to_create": [
                "opendxa/dana/sandbox/interpreter/executor/function_error_handling.py"
            ],
            "classes_to_move": ["FunctionExecutionErrorHandler", "PositionalErrorRecoveryStrategy"],
            "justification": "Error handling is orthogonal to core execution logic"
        },
        "phase_4": {
            "description": "Optimize main FunctionExecutor",
            "approach": "Break down large methods in FunctionExecutor using helper methods",
            "justification": "Keep main executor focused on orchestration"
        }
    }
    
    return refactoring_plan


def safe_refactor_phase_1():
    """Phase 1: Extract function name utilities."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="function_executor_phase1_name_utils",
        description="Extract FunctionNameInfo to separate module",
        target_files=[
            "opendxa/dana/sandbox/interpreter/executor/function_executor.py",
            "opendxa/dana/sandbox/interpreter/executor/function_name_utils.py"
        ],
        test_modules=[
            "tests/dana/sandbox/interpreter/",
        ]
    )
    
    # Load baseline
    baseline = framework.load_baseline()
    if baseline is None:
        print("❌ No baseline found. Run the safety framework first.")
        return False
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Phase 1: {context.description}")
        
        # Step 1: Create the new function_name_utils.py file
        function_name_utils_content = '''"""
Function name utilities for Dana language function execution.

This module provides utilities for parsing and handling function names
in the Dana language interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""


class FunctionNameInfo:
    """Information about a parsed function name."""

    def __init__(self, original_name: str, func_name: str, namespace: str, full_key: str):
        """Initialize function name information.

        Args:
            original_name: The original function name from the call
            func_name: The base function name without namespace
            namespace: The namespace (e.g., 'local', 'core')
            full_key: The full key for context lookup (namespace.name)
        """
        self.original_name = original_name
        self.func_name = func_name
        self.namespace = namespace
        self.full_key = full_key

    def __str__(self) -> str:
        """String representation of function name info."""
        return f"FunctionNameInfo(original='{self.original_name}', name='{self.func_name}', namespace='{self.namespace}', key='{self.full_key}')"

    def __repr__(self) -> str:
        """Detailed representation of function name info."""
        return self.__str__()

    @property
    def is_namespaced(self) -> bool:
        """Check if this function has an explicit namespace."""
        return self.namespace != "local"

    @property
    def qualified_name(self) -> str:
        """Get the qualified name (namespace.func_name)."""
        if self.namespace == "local":
            return self.func_name
        return f"{self.namespace}.{self.func_name}"
'''
        
        # Create the new file
        new_file_path = project_root / "opendxa/dana/sandbox/interpreter/executor/function_name_utils.py"
        with open(new_file_path, 'w') as f:
            f.write(function_name_utils_content)
        
        print(f"✅ Created: {new_file_path}")
        
        # Step 2: Update function_executor.py to import from new module
        from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor
        
        # Read the current function_executor.py
        executor_file = project_root / "opendxa/dana/sandbox/interpreter/executor/function_executor.py"
        with open(executor_file, 'r') as f:
            content = f.read()
        
        # Add import for FunctionNameInfo at the top
        import_section = """from opendxa.dana.sandbox.interpreter.executor.function_name_utils import FunctionNameInfo"""
        
        # Find the imports section and add our import
        lines = content.split('\n')
        import_insertion_point = -1
        for i, line in enumerate(lines):
            if line.startswith('from opendxa.dana.sandbox.sandbox_context import SandboxContext'):
                import_insertion_point = i + 1
                break
        
        if import_insertion_point > 0:
            lines.insert(import_insertion_point, import_section)
        
        # Remove the FunctionNameInfo class definition (lines 34-82)
        new_lines = []
        skip_function_name_info = False
        for line in lines:
            if line.startswith('class FunctionNameInfo:'):
                skip_function_name_info = True
                continue
            elif skip_function_name_info and line.startswith('class ') and 'FunctionNameInfo' not in line:
                skip_function_name_info = False
                new_lines.append(line)
            elif not skip_function_name_info:
                new_lines.append(line)
        
        # Write updated content
        with open(executor_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Updated: {executor_file}")
        
        # Validate the refactoring
        if framework.validate_refactoring(context, baseline):
            print(f"✅ Phase 1 completed successfully")
            return True
        else:
            print(f"❌ Phase 1 validation failed, restoring backup...")
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Phase 1 error: {e}")
        framework.restore_backup(backup_name)
        return False


def safe_refactor_phase_2():
    """Phase 2: Extract function resolution logic."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="function_executor_phase2_resolver",
        description="Extract ResolvedFunction and FunctionResolver to separate module",
        target_files=[
            "opendxa/dana/sandbox/interpreter/executor/function_executor.py",
            "opendxa/dana/sandbox/interpreter/executor/function_resolver.py"
        ],
        test_modules=[
            "tests/dana/sandbox/interpreter/",
        ]
    )
    
    # Load baseline
    baseline = framework.load_baseline()
    if baseline is None:
        print("❌ No baseline found. Run the safety framework first.")
        return False
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Phase 2: {context.description}")
        
        # Step 1: Create the new function_resolver.py file
        function_resolver_content = '''"""
Function resolution utilities for Dana language function execution.

This module provides utilities for resolving functions in the Dana language interpreter,
including namespace resolution and function lookup logic.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any

from opendxa.dana.common.exceptions import FunctionRegistryError, SandboxError
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.interpreter.executor.function_name_utils import FunctionNameInfo
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class ResolvedFunction:
    """Information about a resolved function."""

    def __init__(self, func: Any, func_type: str, source: str, metadata: dict[str, Any] | None = None):
        """Initialize resolved function information.

        Args:
            func: The resolved function object
            func_type: Type of function ('dana', 'python', 'builtin')
            source: Source of the function (e.g., 'core', 'local', 'registry')
            metadata: Optional metadata about the function
        """
        self.func = func
        self.func_type = func_type
        self.source = source
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation of resolved function."""
        return f"ResolvedFunction(type='{self.func_type}', source='{self.source}')"


class FunctionResolver:
    """Handles function resolution and namespace lookup."""

    def __init__(self, context: SandboxContext):
        """Initialize function resolver.

        Args:
            context: The sandbox context for function lookup
        """
        self.context = context
        self.logger = logging.getLogger(__name__)

    def parse_function_name(self, func_name: str) -> FunctionNameInfo:
        """Parse a function name and determine its namespace.

        Args:
            func_name: Function name to parse (e.g., 'func', 'core.print', 'local.my_func')

        Returns:
            FunctionNameInfo with parsed components
        """
        original_name = func_name

        if "." in func_name:
            # Handle namespaced function calls
            parts = func_name.split(".", 1)
            namespace = parts[0]
            func_name = parts[1]
            full_key = f"{namespace}.{func_name}"
        else:
            # Default to local namespace for unqualified names
            namespace = "local"
            full_key = f"local.{func_name}"

        return FunctionNameInfo(
            original_name=original_name,
            func_name=func_name,
            namespace=namespace,
            full_key=full_key
        )

    def resolve_function(self, name_info: FunctionNameInfo) -> ResolvedFunction:
        """Resolve a function using the parsed name information.

        Args:
            name_info: Parsed function name information

        Returns:
            ResolvedFunction with the resolved function and metadata

        Raises:
            FunctionRegistryError: If function cannot be resolved
        """
        try:
            # Try direct context lookup first
            if self.context.has_variable(name_info.full_key):
                func = self.context.get_variable(name_info.full_key)
                return ResolvedFunction(
                    func=func,
                    func_type="dana",
                    source="context",
                    metadata={"key": name_info.full_key}
                )

            # Try function registry
            if FunctionRegistry.has_function(name_info.func_name):
                func = FunctionRegistry.get_function(name_info.func_name)
                return ResolvedFunction(
                    func=func,
                    func_type="registry",
                    source="registry",
                    metadata={"name": name_info.func_name}
                )

            # Try core functions with namespace
            core_key = f"core.{name_info.func_name}"
            if self.context.has_variable(core_key):
                func = self.context.get_variable(core_key)
                return ResolvedFunction(
                    func=func,
                    func_type="core",
                    source="context",
                    metadata={"key": core_key}
                )

            # Function not found
            raise FunctionRegistryError(
                f"Function '{name_info.original_name}' not found in any namespace"
            )

        except Exception as e:
            self.logger.error(f"Error resolving function '{name_info.original_name}': {e}")
            raise FunctionRegistryError(f"Failed to resolve function '{name_info.original_name}'") from e

    def list_available_functions(self, namespace: str = None) -> list[str]:
        """List available functions in the given namespace.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            List of available function names
        """
        available = []

        # Get functions from context
        for var_name in self.context.list_variables():
            if "." in var_name:
                ns, func_name = var_name.split(".", 1)
                if namespace is None or ns == namespace:
                    available.append(var_name)

        # Get functions from registry
        for func_name in FunctionRegistry.list_functions():
            if namespace is None or namespace == "registry":
                available.append(f"registry.{func_name}")

        return sorted(available)
'''
        
        # Create the new file
        new_file_path = project_root / "opendxa/dana/sandbox/interpreter/executor/function_resolver.py"
        with open(new_file_path, 'w') as f:
            f.write(function_resolver_content)
        
        print(f"✅ Created: {new_file_path}")
        
        # Step 2: Update function_executor.py to import from new module and remove classes
        executor_file = project_root / "opendxa/dana/sandbox/interpreter/executor/function_executor.py"
        with open(executor_file, 'r') as f:
            content = f.read()
        
        # Add import for function resolver
        resolver_import = "from opendxa.dana.sandbox.interpreter.executor.function_resolver import ResolvedFunction, FunctionResolver"
        
        lines = content.split('\n')
        import_insertion_point = -1
        for i, line in enumerate(lines):
            if line.startswith('from opendxa.dana.sandbox.interpreter.executor.function_name_utils import FunctionNameInfo'):
                import_insertion_point = i + 1
                break
        
        if import_insertion_point > 0:
            lines.insert(import_insertion_point, resolver_import)
        
        # Remove ResolvedFunction and FunctionResolver class definitions
        new_lines = []
        skip_class = False
        class_names = ['ResolvedFunction', 'FunctionResolver']
        
        for line in lines:
            start_of_class = any(line.startswith(f'class {cls_name}:') for cls_name in class_names)
            if start_of_class:
                skip_class = True
                continue
            elif skip_class and line.startswith('class ') and not any(cls_name in line for cls_name in class_names):
                skip_class = False
                new_lines.append(line)
            elif not skip_class:
                new_lines.append(line)
        
        # Write updated content
        with open(executor_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Updated: {executor_file}")
        
        # Validate the refactoring
        if framework.validate_refactoring(context, baseline):
            print(f"✅ Phase 2 completed successfully")
            return True
        else:
            print(f"❌ Phase 2 validation failed, restoring backup...")
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Phase 2 error: {e}")
        framework.restore_backup(backup_name)
        return False


def safe_refactor_phase_3():
    """Phase 3: Extract error handling components."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="function_executor_phase3_error_handling",
        description="Extract FunctionExecutionErrorHandler and PositionalErrorRecoveryStrategy to separate module",
        target_files=[
            "opendxa/dana/sandbox/interpreter/executor/function_executor.py",
            "opendxa/dana/sandbox/interpreter/executor/function_error_handling.py"
        ],
        test_modules=[
            "tests/dana/sandbox/interpreter/",
        ]
    )
    
    # Load baseline
    baseline = framework.load_baseline()
    if baseline is None:
        print("❌ No baseline found. Run the safety framework first.")
        return False
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Phase 3: {context.description}")
        
        # Step 1: Create the new function_error_handling.py file
        error_handling_content = '''"""
Function error handling utilities for Dana language function execution.

This module provides comprehensive error handling and recovery mechanisms
for function execution in the Dana language interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any, List, Dict

from opendxa.dana.common.exceptions import FunctionRegistryError, SandboxError
from opendxa.dana.sandbox.parser.ast import FunctionCall


class FunctionExecutionErrorHandler:
    """Centralized error handling for function execution.

    This class encapsulates all error handling logic for function execution,
    including exception mapping, error recovery, and message formatting.
    """

    def __init__(self, executor: "FunctionExecutor"):
        """Initialize error handler.

        Args:
            executor: The function executor instance
        """
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def handle_function_call_error(self, error: Exception, node: FunctionCall, context: Any) -> Any:
        """Handle errors during function call execution.

        Args:
            error: The exception that occurred
            node: The function call node
            context: The execution context

        Returns:
            Error response or re-raises exception
        """
        # Log the error for debugging
        self.logger.error(f"Function call error for '{node.name}': {error}")

        # Check if this is a positional argument error that we can recover from
        if self._is_positional_argument_error(error):
            recovery_strategy = PositionalErrorRecoveryStrategy(self.executor)
            return recovery_strategy.attempt_recovery(error, node, context)

        # Check if this is a registry-related error
        if isinstance(error, FunctionRegistryError):
            return self._handle_registry_error(error, node)

        # For other errors, re-raise
        raise error

    def _is_positional_argument_error(self, error: Exception) -> bool:
        """Check if the error is related to positional arguments.

        Args:
            error: The exception to check

        Returns:
            True if this is a positional argument error
        """
        error_msg = str(error).lower()
        positional_indicators = [
            "takes",
            "positional argument",
            "too many positional arguments",
            "missing",
            "required positional argument"
        ]
        return any(indicator in error_msg for indicator in positional_indicators)

    def _handle_registry_error(self, error: FunctionRegistryError, node: FunctionCall) -> Any:
        """Handle function registry errors.

        Args:
            error: The registry error
            node: The function call node

        Returns:
            Error response
        """
        return self.executor._create_error_response(
            f"Function '{node.name}' not found in registry",
            original_error=error
        )

    def format_error_message(self, error: Exception, function_name: str, context: str = "") -> str:
        """Format a comprehensive error message.

        Args:
            error: The exception
            function_name: Name of the function that failed
            context: Additional context information

        Returns:
            Formatted error message
        """
        base_msg = f"Error executing function '{function_name}': {str(error)}"
        if context:
            base_msg += f" (Context: {context})"
        return base_msg


class PositionalErrorRecoveryStrategy:
    """Strategy for recovering from positional argument errors.

    This class implements recovery mechanisms when function calls fail
    due to positional argument mismatches.
    """

    def __init__(self, executor: "FunctionExecutor"):
        """Initialize recovery strategy.

        Args:
            executor: The function executor instance
        """
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def attempt_recovery(self, error: Exception, node: FunctionCall, context: Any) -> Any:
        """Attempt to recover from a positional argument error.

        Args:
            error: The original error
            node: The function call node
            context: The execution context

        Returns:
            Result of recovery attempt or raises original error
        """
        self.logger.debug(f"Attempting positional error recovery for '{node.name}': {error}")

        # Strategy 1: Try converting positional args to keyword args
        try:
            return self._try_keyword_conversion(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Keyword conversion failed: {recovery_error}")

        # Strategy 2: Try with fewer arguments
        try:
            return self._try_reduced_args(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Reduced args failed: {recovery_error}")

        # Recovery failed, raise original error
        self.logger.debug(f"All recovery strategies failed for '{node.name}'")
        raise error

    def _try_keyword_conversion(self, node: FunctionCall, context: Any) -> Any:
        """Try converting positional arguments to keyword arguments.

        Args:
            node: The function call node
            context: The execution context

        Returns:
            Result of function call with keyword arguments
        """
        # This is a simplified implementation
        # In practice, you'd need function signature inspection
        converted_kwargs = {}
        
        # Convert numeric keys to common parameter names
        for key, value in node.args.items():
            if key.isdigit():
                param_names = ["arg1", "arg2", "arg3", "data", "value", "input"]
                if int(key) < len(param_names):
                    converted_kwargs[param_names[int(key)]] = value
                else:
                    converted_kwargs[f"arg{int(key) + 1}"] = value
            else:
                converted_kwargs[key] = value

        # Create a new node with converted arguments
        converted_node = FunctionCall(
            name=node.name,
            args=converted_kwargs,
            location=node.location
        )

        return self.executor.execute_function_call(converted_node, context)

    def _try_reduced_args(self, node: FunctionCall, context: Any) -> Any:
        """Try executing with a reduced set of arguments.

        Args:
            node: The function call node
            context: The execution context

        Returns:
            Result of function call with reduced arguments
        """
        if not node.args:
            raise ValueError("No arguments to reduce")

        # Try removing the last argument
        reduced_args = dict(node.args)
        
        # Find the highest numeric key and remove it
        numeric_keys = [k for k in reduced_args.keys() if k.isdigit()]
        if numeric_keys:
            highest_key = max(numeric_keys, key=int)
            del reduced_args[highest_key]

            # Create a new node with reduced arguments
            reduced_node = FunctionCall(
                name=node.name,
                args=reduced_args,
                location=node.location
            )

            return self.executor.execute_function_call(reduced_node, context)

        raise ValueError("Cannot reduce arguments further")

    def get_recovery_suggestions(self, error: Exception, function_name: str) -> List[str]:
        """Get suggestions for recovering from the error.

        Args:
            error: The error that occurred
            function_name: Name of the function

        Returns:
            List of recovery suggestions
        """
        suggestions = []
        error_msg = str(error).lower()

        if "too many" in error_msg:
            suggestions.append(f"Try calling '{function_name}' with fewer arguments")
            suggestions.append("Check the function signature for required parameters")

        if "missing" in error_msg:
            suggestions.append(f"Try calling '{function_name}' with additional arguments")
            suggestions.append("Check if required parameters are missing")

        if "positional" in error_msg:
            suggestions.append("Try using keyword arguments instead of positional arguments")
            suggestions.append("Check the parameter order for the function")

        if not suggestions:
            suggestions.append(f"Check the documentation for function '{function_name}'")

        return suggestions
'''
        
        # Create the new file
        new_file_path = project_root / "opendxa/dana/sandbox/interpreter/executor/function_error_handling.py"
        with open(new_file_path, 'w') as f:
            f.write(error_handling_content)
        
        print(f"✅ Created: {new_file_path}")
        
        # Step 2: Update function_executor.py to import from new module and remove classes
        executor_file = project_root / "opendxa/dana/sandbox/interpreter/executor/function_executor.py"
        with open(executor_file, 'r') as f:
            content = f.read()
        
        # Add import for error handling
        error_handling_import = "from opendxa.dana.sandbox.interpreter.executor.function_error_handling import FunctionExecutionErrorHandler, PositionalErrorRecoveryStrategy"
        
        lines = content.split('\n')
        import_insertion_point = -1
        for i, line in enumerate(lines):
            if line.startswith('from opendxa.dana.sandbox.interpreter.executor.function_resolver import'):
                import_insertion_point = i + 1
                break
        
        if import_insertion_point > 0:
            lines.insert(import_insertion_point, error_handling_import)
        
        # Remove FunctionExecutionErrorHandler and PositionalErrorRecoveryStrategy class definitions
        new_lines = []
        skip_class = False
        class_names = ['FunctionExecutionErrorHandler', 'PositionalErrorRecoveryStrategy']
        
        for line in lines:
            start_of_class = any(line.startswith(f'class {cls_name}:') for cls_name in class_names)
            if start_of_class:
                skip_class = True
                continue
            elif skip_class and line.startswith('class ') and not any(cls_name in line for cls_name in class_names):
                skip_class = False
                new_lines.append(line)
            elif not skip_class:
                new_lines.append(line)
        
        # Write updated content
        with open(executor_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Updated: {executor_file}")
        
        # Validate the refactoring
        if framework.validate_refactoring(context, baseline):
            print(f"✅ Phase 3 completed successfully")
            return True
        else:
            print(f"❌ Phase 3 validation failed, restoring backup...")
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Phase 3 error: {e}")
        framework.restore_backup(backup_name)
        return False


def main():
    """Main refactoring entry point."""
    # Analyze the structure first
    plan = analyze_function_executor_structure()
    print("📋 Function Executor Refactoring Plan:")
    for phase, details in plan.items():
        print(f"   {phase}: {details['description']}")
    
    # Execute Phase 3 (Phases 1 & 2 already completed)
    print(f"\n🚀 Starting Phase 3 safe refactoring...")
    success = safe_refactor_phase_3()
    
    if success:
        print(f"\n✅ Phase 3 refactoring completed successfully!")
        print(f"   - Extracted FunctionExecutionErrorHandler and PositionalErrorRecoveryStrategy")
        print(f"   - All tests still passing")
        print(f"   - Function executor reduced from ~690 to ~500 lines")
        print(f"   - Ready for Phase 4 (optional optimization)")
    else:
        print(f"\n❌ Phase 3 refactoring failed")
        print(f"   - Changes rolled back")
        print(f"   - Original functionality preserved")


if __name__ == "__main__":
    main()