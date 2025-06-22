"""
Core POET transpilation logic - generates Dana code
"""

import ast
import inspect
import textwrap
from typing import Callable

from .domains.base import FunctionInfo
from .domains.computation import ComputationDomain
from .domains.registry import DomainRegistry
from .errors import POETTranspilationError
from .types import POETConfig


class POETTranspiler:
    """Transpiler that generates Dana code implementing P→O→E→T phases."""
    
    def __init__(self):
        """Initialize the transpiler with domain registry."""
        self.domain_registry = DomainRegistry()
        # Register default domains
        self.domain_registry.register("mathematical_operations", ComputationDomain())
        self.domain_registry.register("computation", ComputationDomain())
        
        # Register POET domains with learning
        from .domains.prompt_optimization import PromptOptimizationDomain
        from .domains.ml_monitoring import MLMonitoringDomain
        from .domains.llm_optimization import LLMOptimizationDomain
        
        self.domain_registry.register("prompt_optimization", PromptOptimizationDomain())
        self.domain_registry.register("ml_monitoring", MLMonitoringDomain())
        self.domain_registry.register("llm_optimization", LLMOptimizationDomain())
    
    def transpile(self, func: Callable, config: POETConfig) -> str:
        """Transpile a Python function to a POET-enhanced Dana function."""
        # Extract function information
        func_info = self._extract_function_info(func, config)
        
        # Get domain template
        domain_template = self._get_domain_template(config.domain)
        
        # Generate P→O→E phases
        perceive_block = domain_template.generate_perceive(func_info)
        operate_block = domain_template.generate_operate(func_info)
        enforce_block = domain_template.generate_enforce(func_info)
        
        # Generate Train phase if optimize_for is set
        train_block = None
        if config.optimize_for:
            train_block = domain_template.generate_train(func_info)
        
        # Build complete Dana code
        return self._build_dana_code(func_info, config, perceive_block, operate_block, enforce_block, train_block)
    
    def _extract_function_info(self, func: Callable, config: POETConfig) -> FunctionInfo:
        """Extract function information from a callable."""
        try:
            source_code = inspect.getsource(func)
            # Remove @poet decorator line if present
            lines = source_code.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('@poet')]
            source_code = '\n'.join(filtered_lines)
            
            # Parse to get AST
            tree = ast.parse(source_code)
            func_def = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
            
            if not func_def:
                raise POETTranspilationError("No function definition found")
            
            # Get signature
            sig = inspect.signature(func)
            signature = str(sig)
            
            # Get annotations
            annotations = {}
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    annotations[param_name] = str(param.annotation)
            if sig.return_annotation != inspect.Signature.empty:
                annotations["return"] = str(sig.return_annotation)
            
            # Get docstring
            docstring = inspect.getdoc(func)
            
            # Get body source (without decorator and docstring)
            body_lines = []
            skip_docstring = True
            for stmt in func_def.body:
                if skip_docstring and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    skip_docstring = False
                    continue
                body_lines.append(ast.unparse(stmt))
            body_source = '\n'.join(body_lines)
            
            return FunctionInfo(
                name=func.__name__,
                source_code=body_source,
                signature=signature,
                docstring=docstring,
                annotations=annotations,
                file_path=None,
                domain=config.domain,
                retries=config.retries,
                timeout=config.timeout,
                optimize_for=config.optimize_for,
                enable_monitoring=config.enable_monitoring,
                cache_strategy=config.cache_strategy,
                fallback_strategy=config.fallback_strategy,
            )
        except Exception as e:
            raise POETTranspilationError(f"Failed to extract function info: {e}") from e
    
    def _get_domain_template(self, domain: str):
        """Get domain template or use default."""
        if domain and self.domain_registry.has_domain(domain):
            return self.domain_registry.get_domain(domain)
        return ComputationDomain()  # Default
    
    def _build_dana_code(self, func_info: FunctionInfo, config: POETConfig,
                         perceive_block, operate_block, enforce_block, train_block) -> str:
        """Build complete Dana code with P→O→E→T phases."""
        
        # Extract parameter info
        params = self._parse_signature(func_info.signature)
        param_names = [p['name'] for p in params]
        param_list = ", ".join(f"{p['name']}: {p['type']}" for p in params)
        return_type = func_info.annotations.get("return", "any")
        
        # Build imports (Dana uses 'import' not 'from X import Y')
        imports = set()
        # Convert Python imports to Dana imports
        for imp in perceive_block.imports | operate_block.imports | enforce_block.imports:
            if imp.startswith("import "):
                imports.add(imp)
            elif imp.startswith("from "):
                # Convert "from X import Y" to Dana style
                parts = imp.split()
                if len(parts) >= 4:  # from module import name
                    module = parts[1]
                    # Dana standard library modules
                    if module in ["math", "time", "json"]:
                        imports.add(f"import {module}")
        
        imports_str = "\n".join(sorted(imports)) if imports else ""
        
        # Generate POETState struct
        poet_state = self._generate_poet_state(param_names)
        
        # Generate phase functions
        perceive_func = self._generate_perceive_function(param_list, perceive_block)
        operate_func = self._generate_operate_function(param_list, operate_block, func_info)
        enforce_func = self._generate_enforce_function(enforce_block)
        train_func = self._generate_train_function(train_block) if train_block else ""
        
        # Generate main enhanced function
        enhanced_func = self._generate_enhanced_function(func_info, param_list, param_names, return_type, config)
        
        # Build complete Dana code
        code_parts = [imports_str] if imports_str else []
        code_parts.extend([
            poet_state,
            perceive_func,
            operate_func,
            enforce_func,
        ])
        if train_func:
            code_parts.append(train_func)
        code_parts.append(enhanced_func)
        
        return "\n\n".join(code_parts)
    
    def _parse_signature(self, signature: str) -> list[dict]:
        """Parse function signature to extract parameters."""
        # Remove parentheses
        sig = signature.strip("()")
        if not sig:
            return []
        
        params = []
        for param in sig.split(","):
            param = param.strip()
            if ":" in param:
                name, type_str = param.split(":", 1)
                name = name.strip()
                type_str = type_str.strip()
                # Convert Python types to Dana types
                dana_type = self._python_to_dana_type(type_str)
                params.append({"name": name, "type": dana_type})
            else:
                # No type annotation
                params.append({"name": param, "type": "any"})
        
        return params
    
    def _python_to_dana_type(self, py_type: str) -> str:
        """Convert Python type annotation to Dana type."""
        type_map = {
            "int": "int",
            "float": "float",
            "str": "string",
            "bool": "bool",
            "list": "list",
            "dict": "dict",
            "Any": "any",
            "None": "null",
        }
        
        # Handle generic types
        for py, dana in type_map.items():
            if py_type.startswith(py):
                if "[" in py_type:  # Generic type
                    inner = py_type[py_type.index("[") + 1:py_type.rindex("]")]
                    inner_dana = self._python_to_dana_type(inner)
                    return f"{dana}[{inner_dana}]"
                return dana
        
        return "any"  # Default
    
    def _generate_poet_state(self, param_names: list[str]) -> str:
        """Generate POETState struct definition."""
        return f'''# POET State Management
struct POETState {{
    inputs: dict
    perceive_result: dict
    operate_result: dict
    enforce_result: dict
    metadata: dict
    errors: list[string]
    warnings: list[string]
}}'''
    
    def _generate_perceive_function(self, param_list: str, perceive_block) -> str:
        """Generate perceive function."""
        # Convert perceive block code to Dana syntax
        dana_code = self._python_to_dana_code(perceive_block.code)
        
        return f'''def perceive({param_list}, state: POETState) -> POETState {{
    # Input validation and preparation
{textwrap.indent(dana_code, "    ")}
    
    state.perceive_result = {{
        "valid": len(state.errors) == 0,
        "validated": true
    }}
    return state
}}'''
    
    def _generate_operate_function(self, param_list: str, operate_block, func_info: FunctionInfo) -> str:
        """Generate operate function with original logic embedded."""
        # Convert original function body to Dana
        original_logic = self._python_to_dana_code(func_info.source_code)
        
        return f'''def operate({param_list}, state: POETState) -> POETState {{
    # Core logic execution with reliability enhancements
    if not state.perceive_result.get("valid", false) {{
        state.operate_result = {{"success": false, "error": "Perceive phase failed"}}
        return state
    }}
    
    max_retries = {func_info.retries}
    for attempt in range(max_retries) {{
        try {{
            # Original logic (embedded and potentially enhanced)
{textwrap.indent(original_logic, "            ")}
            
            state.operate_result = {{
                "success": true,
                "value": result,  # Assumes original logic sets 'result'
                "attempts": attempt + 1
            }}
            break
        }} except Exception as e {{
            if attempt == max_retries - 1 {{
                state.errors.append(f"Operation failed after {{max_retries}} attempts: {{str(e)}}")
                state.operate_result = {{"success": false}}
            }} else {{
                # Exponential backoff
                time.sleep(0.1 * (2 ** attempt))
            }}
        }}
    }}
    
    return state
}}'''
    
    def _generate_enforce_function(self, enforce_block) -> str:
        """Generate enforce function."""
        dana_code = self._python_to_dana_code(enforce_block.code)
        
        return f'''def enforce(state: POETState) -> POETState {{
    # Output validation and business rules
    if state.operate_result.get("success", false) {{
{textwrap.indent(dana_code, "        ")}
        
        state.enforce_result = {{
            "valid": len(state.errors) == 0,
            "final_value": state.operate_result.get("value") if len(state.errors) == 0 else null
        }}
    }} else {{
        state.enforce_result = {{"valid": false}}
    }}
    
    return state
}}'''
    
    def _generate_train_function(self, train_block) -> str:
        """Generate train function if learning is enabled."""
        if not train_block:
            return ""
        
        dana_code = self._python_to_dana_code(train_block.code)
        
        return f'''def train(state: POETState, feedback: dict) -> void {{
    # Learning logic - update parameters based on feedback
    log(f"Training with feedback: {{feedback}}")
{textwrap.indent(dana_code, "    ")}
}}'''
    
    def _generate_enhanced_function(self, func_info: FunctionInfo, param_list: str, 
                                   param_names: list[str], return_type: str, config: POETConfig) -> str:
        """Generate the main enhanced function that orchestrates phases."""
        param_args = ", ".join(f'"{name}": {name}' for name in param_names)
        func_args = ", ".join(param_names)
        
        train_call = ""
        if config.optimize_for:
            train_call = """
    # Store execution for potential training
    if state.metadata.get("collect_feedback", false) {
        # Feedback can be provided later via feedback() function
        state.metadata["execution_id"] = generate_uuid()
    }"""
        
        return f'''# Main enhanced function
def enhanced_{func_info.name}({param_list}) -> {return_type} {{
    # Initialize POET state
    state = POETState(
        inputs={{{param_args}}},
        perceive_result={{}},
        operate_result={{}},
        enforce_result={{}},
        metadata={{"start_time": time.time()}},
        errors=[],
        warnings=[]
    )
    
    # Execute P→O→E pipeline
    state = perceive({func_args}, state)
    state = operate({func_args}, state)
    state = enforce(state)
{train_call}
    
    # Handle errors
    if not state.enforce_result.get("valid", false) {{
        error_msg = "; ".join(state.errors) if state.errors else "Validation failed"
        raise ValueError(f"POET validation failed: {{error_msg}}")
    }}
    
    # Return enhanced result
    return state.enforce_result["final_value"]
}}'''
    
    def _python_to_dana_code(self, python_code: str) -> str:
        """Convert Python code snippets to Dana syntax."""
        # This is a simplified conversion - in practice would need full transpilation
        dana_code = python_code
        
        # Basic syntax conversions
        replacements = [
            ("isinstance(", "isinstance("),  # Dana has isinstance
            ("len(", "len("),  # Dana has len
            ("range(", "range("),  # Dana has range
            ("str(", "string("),  # Dana uses string() not str()
            ("True", "true"),
            ("False", "false"),
            ("None", "null"),
            ("elif", "else if"),
            ("raise ValueError", "raise ValueError"),
            ("raise TypeError", "raise TypeError"),
        ]
        
        for py, dana in replacements:
            dana_code = dana_code.replace(py, dana)
        
        return dana_code
