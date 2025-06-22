"""
Core POET transpilation logic
"""

import ast
import textwrap

from .domains.base import FunctionInfo
from .domains.computation import ComputationDomain
from .domains.registry import DomainRegistry
from .errors import POETTranspilationError
from .types import POETConfig


class PoetTranspiler:
    def __init__(self):
        """Initialize the transpiler with domain registry."""
        self.domain_registry = DomainRegistry()
        # Register default domains
        self.domain_registry.register("mathematical_operations", ComputationDomain())
        self.domain_registry.register("computation", ComputationDomain())
        
        # Register POET domains with learning
        from .domains.prompt_optimization import PromptOptimizationDomain
        from .domains.ml_monitoring import MLMonitoringDomain
        self.domain_registry.register("prompt_optimization", PromptOptimizationDomain())
        self.domain_registry.register("ml_monitoring", MLMonitoringDomain())
    
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

            # Extract function information
            func_info = self._extract_function_info(py_func_def, original_code, config)
            
            # Get domain template
            domain_template = self._get_domain_template(config.domain)
            
            # Generate P→O→E phases
            perceive_block = domain_template.generate_perceive(func_info)
            operate_block = domain_template.generate_operate(func_info)
            enforce_block = domain_template.generate_enforce(func_info)
            
            # Build enhanced function
            enhanced_code = self._build_enhanced_function(
                func_info, config, perceive_block, operate_block, enforce_block
            )
            
            # Generate training code if enabled
            train_code = None
            if config.optimize_for or config.enable_training:
                train_code = self._generate_training_code(function_name, config)
            
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
    
    def _extract_function_info(self, func_def: ast.FunctionDef, source_code: str, config: POETConfig) -> FunctionInfo:
        """Extract function information from AST node."""
        # Get function signature
        signature = f"({ast.unparse(func_def.args)})"
        
        # Get annotations
        annotations = {}
        for arg in func_def.args.args:
            if arg.annotation:
                annotations[arg.arg] = ast.unparse(arg.annotation)
        if func_def.returns:
            annotations["return"] = ast.unparse(func_def.returns)
        
        # Get docstring
        docstring = ast.get_docstring(func_def)
        
        # Get original body as source code
        body_lines = []
        for stmt in func_def.body:
            # Skip docstring
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                continue
            body_lines.append(ast.unparse(stmt))
        body_source = "\n".join(body_lines)
        
        return FunctionInfo(
            name=func_def.name,
            source_code=body_source,
            signature=signature,
            docstring=docstring,
            annotations=annotations,
            file_path=None,  # Not available in this context
            domain=config.domain or "general",
            retries=config.retries,
            timeout=int(config.timeout) if config.timeout else None,
            optimize_for=config.optimize_for,
            enable_monitoring=config.enable_monitoring,
            cache_strategy="none",  # Default for now
            fallback_strategy="original"  # Default for now
        )
    
    def _get_domain_template(self, domain: str | None):
        """Get domain template or use default."""
        if domain and self.domain_registry.has_domain(domain):
            return self.domain_registry.get_domain(domain)
        # Default to computation domain for now
        return ComputationDomain()
    
    def _build_enhanced_function(self, func_info: FunctionInfo, config: POETConfig, 
                                perceive_block, operate_block, enforce_block) -> str:
        """Build the complete enhanced function with P→O→E phases."""
        
        # Extract parameter list for function signature (remove parentheses as signature already has them)
        params_str = func_info.signature.strip('()')
        
        # Extract parameter names from signature
        param_names = self._extract_param_names(params_str)
        
        # Build imports
        imports = set()
        imports.update(perceive_block.imports)
        imports.update(operate_block.imports)
        imports.update(enforce_block.imports)
        imports_str = "\n".join(sorted(imports))
        
        # Build the enhanced function
        enhanced_function = f'''
{imports_str}

def {func_info.name}_poet({params_str}):
    """
    POET-enhanced version of {func_info.name}.
    
    This function implements Plan-Observe-Execute (P→O→E) phases:
    - Perceive: Input validation and preparation
    - Operate: Core logic execution with retry and monitoring
    - Enforce: Output validation and business rules
    
    Domain: {config.domain or "general"}
    """
    
    # === PERCEIVE PHASE ===
    # Validate and prepare inputs
    try:
{textwrap.indent(perceive_block.code, "        ")}
    except Exception as e:
        log(f"Perceive phase failed: {{e}}")
        raise ValueError(f"Input validation failed: {{e}}") from e
    
    # === OPERATE PHASE ===
    # Execute core logic with reliability enhancements
    max_retries = {config.retries}
    retry_count = 0
    last_error = None
    
    while retry_count <= max_retries:
        try:
            # Define original function inline
            def _original_func({params_str}):
{textwrap.indent(func_info.source_code, "                ")}
            
            # Execute with monitoring
{textwrap.indent(operate_block.code.replace("func(*args, **kwargs)", 
            f"_original_func({', '.join(param_names)})"), "            ")}
            break  # Success, exit retry loop
            
        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count <= max_retries:
                log(f"Operate phase failed (attempt {{retry_count}}/{{max_retries}}): {{e}}")
            else:
                log(f"Operate phase failed after {{max_retries}} retries: {{e}}")
                raise RuntimeError(f"Operation failed after {{max_retries}} retries: {{e}}") from e
    
    # === ENFORCE PHASE ===
    # Validate output and apply business rules
    try:
        final_result = result  # From operate phase
{textwrap.indent(enforce_block.code, "        ")}
        
        return final_result
        
    except Exception as e:
        log(f"Enforce phase failed: {{e}}")
        raise ValueError(f"Output validation failed: {{e}}") from e

# Alias for backward compatibility
{func_info.name} = {func_info.name}_poet
'''
        
        return enhanced_function.strip()
    
    def _extract_param_names(self, params_str: str) -> list[str]:
        """Extract parameter names from a parameter string."""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            # Remove type annotations and default values
            if ':' in param:
                param = param.split(':')[0].strip()
            if '=' in param:
                param = param.split('=')[0].strip()
            if param and not param.startswith('*'):
                params.append(param)
        
        return params
    
    def _generate_training_code(self, function_name: str, config: POETConfig) -> str:
        """Generate training code for the enhanced function."""
        return f'''
def train_{function_name}(feedback_data: dict):
    """
    Training function for {function_name}.
    Collects feedback and optimizes the POET phases.
    """
    log(f"Training {function_name} with feedback: {{feedback_data}}")
    
    # Extract performance metrics
    metrics = feedback_data.get("metrics", {{}})
    errors = feedback_data.get("errors", [])
    
    # Update phase configurations based on feedback
    if errors:
        log(f"Errors detected: {{errors}}")
        # TODO: Adjust validation rules in Perceive phase
        # TODO: Tune retry strategy in Operate phase
        # TODO: Update enforcement rules in Enforce phase
    
    # Store training data for future optimization
    training_metadata = {{
        "function": "{function_name}",
        "domain": "{config.domain}",
        "timestamp": feedback_data.get("timestamp"),
        "metrics": metrics,
        "errors": errors
    }}
    
    log(f"Training completed for {function_name}")
    return training_metadata
'''
