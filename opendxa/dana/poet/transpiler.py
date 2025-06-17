"""
Core POET transpilation logic
"""

import ast

from .errors import POETTranspilationError
from .types import POETConfig


class PoetTranspiler:
    def transpile(self, function_code: str, config: POETConfig, context: dict | None = None) -> dict:
        """Transpile a Python function to a POET-enhanced Dana function."""
        function_name, original_code = self._validate_function_code(function_code)
        return self._generate_enhanced_code(function_name, original_code, config, context)

    def _validate_function_code(self, code: str) -> tuple[str, str]:
        """Validate function code and extract function name and decorator"""
        try:
            tree = ast.parse(code)
            function_def = next((node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)), None)

            if not function_def:
                raise POETTranspilationError("No function definition found in code")

            decorator_found = any(
                isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "poet"
                for decorator in function_def.decorator_list
            )

            if not decorator_found:
                raise POETTranspilationError("Missing @poet decorator")

            return function_def.name, code

        except SyntaxError as e:
            raise POETTranspilationError(f"Invalid Python code: {e}") from e

    def _generate_enhanced_code(self, function_name: str, original_code: str, config: POETConfig, context: dict | None) -> dict:
        """Generate enhanced function code with POET phases"""
        try:
            tree = ast.parse(original_code)
            py_func_def = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)

            if not py_func_def:
                raise POETTranspilationError("No function definition found in the provided code.")

            param_str = ast.unparse(py_func_def.args)

            # A simplistic transpilation of the function body
            dana_body = "\\n    ".join([ast.unparse(s) for s in py_func_def.body])

            enhanced_code = f"""
def {function_name}({param_str}):
    # This is a placeholder for a POET-enhanced function
    # In a real implementation, this would include perceive, operate, enforce phases
    {dana_body}
"""
            train_code = None
            if config.optimize_for or config.enable_training:
                train_code = f"""
def train_{function_name}(feedback_data: dict):
    # Placeholder for training logic
    log(f"Training {function_name} with feedback: {{feedback_data}}")
"""
            return {
                "enhanced_code": enhanced_code,
                "train_code": train_code,
                "metadata": {
                    "function_name": function_name,
                    "domain": config.domain,
                    "optimize_for": config.optimize_for,
                    "retries": config.retries,
                    "timeout": config.timeout,
                    "enable_monitoring": config.enable_monitoring,
                    "context": context,
                },
                "language": "dana",
            }
        except Exception as e:
            raise POETTranspilationError(f"Failed to generate enhanced code: {e}") from e
