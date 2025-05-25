#!/usr/bin/env python3
"""
Cleanup script for function call implementation.

This script removes the old function call implementation after we've confirmed
the new implementation works correctly.

USE WITH CAUTION: This is a destructive operation that modifies source files.
Make sure you have committed your changes before running this script.
"""

import re
import sys
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))


def cleanup_sandbox_function():
    """Remove old implementation from SandboxFunction."""
    filepath = project_root / "opendxa/dana/sandbox/interpreter/functions/sandbox_function.py"
    with open(filepath) as file:
        content = file.read()

    # Find the __call__ method and replace with simpler version
    pattern = r"def __call__\([^)]*\):.*?# Legacy code path.*?sanitized_context\.set_scope\(\"local\", saved_local_context\)"
    replacement = """def __call__(
        self,
        context: Optional[SandboxContext] = None,
        local_context: Optional[Dict[str, Any]] = None,
        *the_args: Any,
        **the_kwargs: Any,
    ) -> Any:
        \"\"\"Call the function with arguments.

        Args:
            context: Optional context to use for execution
            local_context: Optional local context to use for execution
            *the_args: Positional arguments
            **the_kwargs: Keyword arguments

        Returns:
            The function result
        \"\"\"
        # Ensure context is never None
        actual_context = context or self.context
        if actual_context is None:
            actual_context = SandboxContext()
        return self._call_with_adapter(actual_context, local_context, list(the_args), the_kwargs)"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Change feature flag to always be enabled
    new_content = new_content.replace(
        "self._use_adapter = False  # Feature flag for adapter pattern", "self._use_adapter = True  # Always use adapter pattern"
    )

    return filepath, new_content


def cleanup_expression_evaluator():
    """Remove old implementation from ExpressionEvaluator."""
    filepath = project_root / "opendxa/dana/sandbox/interpreter/executor/expression_evaluator.py"
    with open(filepath) as file:
        content = file.read()

    # Find the _evaluate_function_call method
    pattern = r"def _evaluate_function_call.*?# Use the ArgumentProcessor if enabled.*?# Original implementation.*?return result"
    replacement = """def _evaluate_function_call(
        self,
        node: FunctionCall,
        context: SandboxContext,
    ) -> Any:
        \"\"\"Evaluate a function call expression.

        Args:
            node: The function call node
            context: The context for evaluation

        Returns:
            The result of the function call
        \"\"\"
        # Special handling for local.reason - redirect to the global reason function
        function_name = node.name
        if function_name == "local.reason":
            function_name = "reason"
            
        # Import ArgumentProcessor
        from opendxa.dana.sandbox.interpreter.functions.argument_processor import ArgumentProcessor
        
        # Process arguments using the processor
        args, kwargs = ArgumentProcessor.evaluate_args(
            node.args,
            evaluator=self,
            context=context
        )
        
        # Call the function
        result = self.function_registry.call(
            function_name,
            args=args,
            kwargs=kwargs,
            context=context,
        )
        
        return result"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Change feature flag to always be enabled
    new_content = new_content.replace("self._use_arg_processor = False", "self._use_arg_processor = True")

    return filepath, new_content


def cleanup_function_registry():
    """Remove old implementation from FunctionRegistry."""
    filepath = project_root / "opendxa/dana/sandbox/interpreter/functions/function_registry.py"
    with open(filepath) as file:
        content = file.read()

    # Remove feature flag and conditional code
    pattern = r"# Feature flag to control use of ArgumentProcessor.*?# Fall back to original implementation.*?pass"
    replacement = "# Always use ArgumentProcessor"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Remove original implementation
    pattern = r"try:.*?# Original implementation.*?result = func\(context, local_context, \*call_args, \*\*call_kwargs\)"
    replacement = "try:"

    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)

    return filepath, new_content


def cleanup_python_function():
    """Remove old implementation from PythonFunction."""
    filepath = project_root / "opendxa/dana/sandbox/interpreter/functions/python_function.py"
    with open(filepath) as file:
        content = file.read()

    # Remove conditional code for context injection
    pattern = r"# Only inject context manually if not using the adapter pattern.*?if not self\._use_adapter:"
    replacement = ""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Change feature flag to always be enabled
    new_content = new_content.replace(
        "self._use_adapter = False  # Keep disabled for now", "self._use_adapter = True  # Always use adapter pattern"
    )

    return filepath, new_content


def cleanup_dana_function():
    """Update DanaFunction."""
    filepath = project_root / "opendxa/dana/sandbox/interpreter/functions/dana_function.py"
    with open(filepath) as file:
        content = file.read()

    # Change feature flag to always be enabled
    new_content = content.replace(
        "self._use_adapter = False  # Keep disabled for now", "self._use_adapter = True  # Always use adapter pattern"
    )

    return filepath, new_content


def main():
    """Run the cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old function call implementation")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run mode)")

    args = parser.parse_args()

    # Collect all cleanup functions
    cleanup_functions = [
        cleanup_sandbox_function,
        cleanup_expression_evaluator,
        cleanup_function_registry,
        cleanup_python_function,
        cleanup_dana_function,
    ]

    # Run each cleanup function
    for cleanup_func in cleanup_functions:
        filepath, new_content = cleanup_func()

        # Get the original content
        with open(filepath) as file:
            original_content = file.read()

        # If content changed
        if original_content != new_content:
            if args.apply:
                # Write the changes
                with open(filepath, "w") as file:
                    file.write(new_content)
                print(f"Updated {filepath.relative_to(project_root)}")
            else:
                print(f"Would update {filepath.relative_to(project_root)}")
        else:
            print(f"No changes needed in {filepath.relative_to(project_root)}")

    if not args.apply:
        print("\nThis was a dry run. To apply changes, use --apply")


if __name__ == "__main__":
    main()
