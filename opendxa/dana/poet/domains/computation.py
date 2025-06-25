"""
Computation Domain Template

Implements Use Case A: Simple Math Functions (POE)
Provides enhanced mathematical operations with comprehensive validation,
error handling, and reliability features.

Features:
- Input type and range validation
- Mathematical constraint checking (division by zero, overflow, etc.)
- Retry logic for transient errors
- Result validation and business rule enforcement
- Comprehensive error messages
"""

from typing import Any

from .base import BaseDomainTemplate, CodeBlock, FunctionInfo


class ComputationDomain(BaseDomainTemplate):
    """
    Domain template for mathematical and computational functions.

    Enhances functions with:
    - Type validation for numeric inputs
    - Range checking and overflow protection
    - Mathematical constraint validation (e.g., division by zero)
    - Numerical stability checks
    - Result validation for mathematical properties
    """

    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate comprehensive input validation for mathematical operations"""

        # Analyze function signature to determine validation strategy
        param_validations = []

        # Extract parameter information
        signature_analysis = self._analyze_function_signature(func_info)

        for param_name, param_info in signature_analysis.items():
            param_type = param_info.get("type", "Any")
            is_numeric = param_type in ["int", "float", "complex"] or "float" in param_type.lower()

            if is_numeric:
                param_validations.append(
                    f"""
    # Validate {param_name} (numeric)
    if not isinstance({param_name}, (int, float, complex)):
        raise TypeError(f"Parameter '{param_name}' must be numeric, got {{type({param_name}).__name__}}")
    
    if isinstance({param_name}, (int, float)):
        if math.isnan({param_name}):
            raise ValueError(f"Parameter '{param_name}' cannot be NaN")
        if math.isinf({param_name}):
            raise ValueError(f"Parameter '{param_name}' cannot be infinite")
        
        # Range validation for very large numbers
        if abs({param_name}) > 1e100:
            raise ValueError(f"Parameter '{param_name}' is too large: {{{param_name}}}")
""".strip()
                )
            else:
                param_validations.append(
                    f"""
    # Validate {param_name} (general)
    if {param_name} is None:
        raise ValueError(f"Parameter '{param_name}' cannot be None")
""".strip()
                )

        # Add domain-specific mathematical constraints
        constraints = self._generate_mathematical_constraints(func_info)

        validation_code = f"""
import math

# === Input Type and Range Validation ===
{chr(10).join(param_validations) if param_validations else "# No specific parameter validation needed"}

# === Mathematical Constraint Validation ===
{constraints}

# Store validated inputs for operation phase
validated_inputs = {{{", ".join(f'"{p}": {p}' for p in signature_analysis.keys())}}}
""".strip()

        return CodeBlock(
            code=validation_code,
            dependencies=["math"],
            imports=["import math"],
            metadata={
                "phase": "perceive",
                "domain": "computation",
                "validation_types": list(signature_analysis.keys()),
                "constraints_applied": True,
            },
        )

    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate enhanced mathematical operation with numerical stability"""

        # Call parent for basic retry logic
        parent_block = super()._generate_operate(func_info)

        # Add computation-specific enhancements
        enhanced_operation = f"""
{parent_block.code}

# === Numerical Stability Enhancements ===
# Check for numerical stability issues
if isinstance(result, (int, float, complex)):
    if isinstance(result, (int, float)):
        if math.isnan(result):
            raise ValueError("Operation produced NaN result - numerical instability detected")
        if math.isinf(result):
            raise ValueError("Operation produced infinite result - possible overflow")
    
    # Check for underflow (result too close to zero when it shouldn't be)
    if isinstance(result, float) and result != 0.0 and abs(result) < 1e-300:
        log(f"Warning: Result {{result}} may be subject to underflow")

# Store operation metadata
operation_metadata = {{
    "numerical_stable": True,
    "result_type": type(result).__name__,
    "result_magnitude": abs(result) if isinstance(result, (int, float, complex)) else None
}}
""".strip()

        return CodeBlock(
            code=enhanced_operation,
            dependencies=parent_block.dependencies + ["math"],
            imports=parent_block.imports + ["import math"],
            metadata={**parent_block.metadata, "domain": "computation", "numerical_stability": True, "enhanced_operation": True},
        )

    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate mathematical result validation and business rules"""

        # Call parent for basic enforcement
        parent_block = super()._generate_enforce(func_info)

        # Add computation-specific result validation
        mathematical_enforcement = f"""
{parent_block.code}

# === Mathematical Result Validation ===
if isinstance(final_result, (int, float, complex)):
    # Validate numerical result properties
    if isinstance(final_result, (int, float)):
        if math.isnan(final_result):
            raise ValueError("Final result is NaN - computation failed")
        if math.isinf(final_result):
            raise ValueError("Final result is infinite - overflow detected")
    
    # Business rule: reasonable magnitude
    if isinstance(final_result, (int, float)) and abs(final_result) > 1e50:
        log(f"Warning: Result {{final_result}} has very large magnitude")
    
    # Additional domain-specific validations
    {self._generate_result_constraints(func_info)}

# Store final validation metadata
validation_metadata = {{
    "result_validated": True,
    "mathematical_properties_checked": True,
    "business_rules_applied": True,
    "final_result_type": type(final_result).__name__
}}
""".strip()

        return CodeBlock(
            code=mathematical_enforcement,
            dependencies=parent_block.dependencies + ["math"],
            imports=parent_block.imports + ["import math"],
            metadata={**parent_block.metadata, "domain": "computation", "mathematical_validation": True, "business_rules": True},
        )

    def _analyze_function_signature(self, func_info: FunctionInfo) -> dict[str, dict[str, Any]]:
        """Analyze function signature to extract parameter information"""
        signature = func_info.signature
        annotations = func_info.annotations

        # Extract parameter names from signature
        param_info = {}

        if "(" in signature and ")" in signature:
            params_str = signature.split("(")[1].split(")")[0]
            if params_str.strip():
                for param in params_str.split(","):
                    param = param.strip()
                    if ":" in param:
                        param_name = param.split(":")[0].strip()
                        param_type = param.split(":")[1].split("=")[0].strip()
                    else:
                        param_name = param.split("=")[0].strip()
                        param_type = "Any"

                    if param_name and not param_name.startswith("*"):
                        param_info[param_name] = {"type": param_type, "annotation": annotations.get(param_name, None)}

        return param_info

    def _generate_mathematical_constraints(self, func_info: FunctionInfo) -> str:
        """Generate domain-specific mathematical constraints"""

        # Detect common mathematical patterns and add appropriate constraints
        source_code = func_info.source_code.lower()
        constraints = []

        # Division operations
        if "/" in source_code or "divide" in func_info.name.lower():
            constraints.append(
                """
# Division by zero protection
for param_name, param_value in validated_inputs.items():
    if isinstance(param_value, (int, float)) and param_value == 0:
        if 'denom' in param_name.lower() or 'b' == param_name or 'divisor' in param_name.lower():
            raise ValueError(f"Division by zero: parameter '{param_name}' cannot be zero")
""".strip()
            )

        # Square root operations
        if "sqrt" in source_code or "**0.5" in source_code:
            constraints.append(
                """
# Square root domain validation
for param_name, param_value in validated_inputs.items():
    if isinstance(param_value, (int, float)) and param_value < 0:
        if 'sqrt' in func_info.name.lower() or any(x in source_code for x in ['sqrt', '**0.5']):
            raise ValueError(f"Square root of negative number: parameter '{param_name}' = {{param_value}}")
""".strip()
            )

        # Logarithm operations
        if "log" in source_code:
            constraints.append(
                """
# Logarithm domain validation  
for param_name, param_value in validated_inputs.items():
    if isinstance(param_value, (int, float)) and param_value <= 0:
        if any(x in source_code for x in ['log', 'ln']):
            raise ValueError(f"Logarithm of non-positive number: parameter '{param_name}' = {{param_value}}")
""".strip()
            )

        return "\n\n".join(constraints) if constraints else "# No specific mathematical constraints detected"

    def _generate_result_constraints(self, func_info: FunctionInfo) -> str:
        """Generate result-specific validation constraints"""

        constraints = []
        func_info.annotations.get("return", "")

        # Percentage results should be in reasonable range
        if "percent" in func_info.name.lower() or "rate" in func_info.name.lower():
            constraints.append(
                """
    # Percentage/rate validation
    if isinstance(final_result, (int, float)):
        if final_result < 0:
            log(f"Warning: Negative percentage/rate result: {{final_result}}")
        if final_result > 100 and "percent" in func_info.name.lower():
            log(f"Warning: Percentage > 100%: {{final_result}}")
""".strip()
            )

        # Probability results should be [0, 1]
        if "prob" in func_info.name.lower() or "probability" in func_info.name.lower():
            constraints.append(
                """
    # Probability validation
    if isinstance(final_result, (int, float)):
        if final_result < 0 or final_result > 1:
            raise ValueError(f"Probability result out of range [0,1]: {{final_result}}")
""".strip()
            )

        # Count/index results should be non-negative integers
        if any(word in func_info.name.lower() for word in ["count", "index", "length", "size"]):
            constraints.append(
                """
    # Count/index validation
    if isinstance(final_result, (int, float)):
        if final_result < 0:
            raise ValueError(f"Count/index result cannot be negative: {{final_result}}")
        if isinstance(final_result, float) and not final_result.is_integer():
            log(f"Warning: Non-integer count/index result: {{final_result}}")
""".strip()
            )

        return "\n".join(constraints) if constraints else "# No specific result constraints applied"
