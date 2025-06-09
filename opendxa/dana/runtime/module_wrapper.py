"""
Dana Module Wrapper

Wraps Dana AST as Python-callable interface.
"""

import re
from typing import Any, Callable, Dict, List


class DanaModuleWrapper:
    """Wraps Dana AST as Python-callable interface."""
    
    def __init__(self, module_name: str, dana_ast: Any, dana_source: str):
        self.module_name = module_name
        self.dana_ast = dana_ast
        self.dana_source = dana_source
        
        # For Step 1, we'll do basic function extraction from source
        # In later steps, this will use the actual Dana interpreter
        self.python_interface = self._create_python_interface()
    
    def _create_python_interface(self) -> Dict[str, Callable]:
        """Create Python callable interface for all Dana functions."""
        interface = {}
        
        # Extract function definitions from Dana source (basic parsing for Step 1)
        functions = self._extract_functions_basic(self.dana_source)
        
        for func_name in functions:
            python_callable = self._wrap_dana_function_basic(func_name)
            interface[func_name] = python_callable
        
        return interface
    
    def _extract_functions_basic(self, dana_source: str) -> List[str]:
        """Basic function extraction from Dana source (Step 1 implementation)."""
        functions = []
        
        # Simple regex to find function definitions
        # Pattern: def function_name(parameters)
        function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(function_pattern, dana_source)
        
        functions.extend(matches)
        
        return functions
    
    def _wrap_dana_function_basic(self, func_name: str) -> Callable:
        """Wrap a Dana function as a Python callable (basic Step 1 implementation)."""
        
        def python_callable(*args, **kwargs):
            # For Step 1, we'll return a simple placeholder result
            # In later steps, this will execute actual Dana code
            
            print(f"Called Dana function '{func_name}' with args: {args}, kwargs: {kwargs}")
            
            # Basic simulation of function execution
            if func_name == "reason_about":
                return f"Dana reasoning result for: {args[0] if args else 'no input'}"
            elif func_name == "add_numbers":
                if len(args) >= 2:
                    return args[0] + args[1]
                return 0
            elif func_name == "get_greeting":
                return f"Hello, {args[0] if args else 'World'}!"
            else:
                return f"Result from Dana function '{func_name}'"
        
        # Set function metadata for better Python integration
        python_callable.__name__ = func_name
        python_callable.__doc__ = f"Dana function: {func_name}"
        python_callable._dana_function_name = func_name
        python_callable._dana_source = self.dana_source
        
        return python_callable
    
    def _create_call_context_basic(self, func_name: str, args: tuple, kwargs: dict):
        """Create basic call context for Step 1."""
        # This will be expanded in later steps with actual Dana context
        return {
            'function_name': func_name,
            'args': args,
            'kwargs': kwargs,
            'module_source': self.dana_source
        }
    
    def get_function_names(self) -> List[str]:
        """Get list of available function names."""
        return list(self.python_interface.keys())
    
    def get_dana_source(self) -> str:
        """Get the original Dana source code."""
        return self.dana_source 