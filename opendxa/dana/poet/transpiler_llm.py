"""
LLM-Powered POET Transpiler

This is how POET should really work - using LLM intelligence to generate
context-aware enhancements rather than hard-coded templates.
"""

import inspect
from typing import Callable

from opendxa.common.resource.llm_resource import LLMResource
from .types import POETConfig
from opendxa.common.types import BaseRequest


class POETTranspilerLLM:
    """LLM-powered transpiler that generates intelligent enhancements."""

    def __init__(self):
        self.llm = LLMResource()

    def transpile(self, func: Callable, config: POETConfig) -> str:
        """Use LLM to generate POET-enhanced Dana code."""

        # Extract function information
        source_code = inspect.getsource(func)
        signature = inspect.signature(func)
        docstring = inspect.getdoc(func) or "No description provided"

        # Build comprehensive prompt for LLM
        prompt = self._build_generation_prompt(
            function_name=func.__name__, source_code=source_code, signature=str(signature), docstring=docstring, config=config
        )

        # Generate enhanced Dana code using LLM
        request = BaseRequest(
            arguments={
                "messages": [{"role": "system", "content": self._get_system_prompt()}, {"role": "user", "content": prompt}],
                "temperature": 0.3,  # Low temperature for consistent code generation
                "max_tokens": 4000,
            }
        )

        response = self.llm.query_sync(request)

        # Handle BaseResponse object properly
        if hasattr(response, "content") and response.content:
            if isinstance(response.content, dict):
                # If content is a dict, extract the message content
                if "choices" in response.content and len(response.content["choices"]) > 0:
                    dana_code = response.content["choices"][0]["message"]["content"]
                else:
                    # Fallback: try to get content directly
                    dana_code = str(response.content)
            else:
                # Content is a string or other type
                dana_code = str(response.content)
        elif hasattr(response, "__getitem__"):
            # Handle dictionary-like response
            try:
                dana_code = response["choices"][0]["message"]["content"]
            except (KeyError, TypeError):
                dana_code = str(response)
        else:
            # Fallback for any other response type
            dana_code = str(response)

        # Post-process to ensure valid Dana syntax
        return self._post_process_dana_code(dana_code)

    def _get_system_prompt(self) -> str:
        """System prompt that teaches the LLM about POET and Dana."""
        return """You are an expert code generator for the POET framework. POET enhances functions 
with four phases: Perceive (input validation), Operate (core logic with reliability), 
Enforce (output validation), and Train (learning from feedback).

Generate Dana code that:
1. Uses POETState struct to track state through phases
2. Implements perceive() for intelligent input validation based on the function's purpose
3. Implements operate() with the original logic plus retry, monitoring, and error handling
4. Implements enforce() with output validation appropriate to the domain
5. Implements train() if optimize_for is set in the config
6. Creates enhanced_{function_name}() that orchestrates all phases

Dana syntax reminders:
- Use 'true/false' not 'True/False'
- Use 'null' not 'None'
- Use 'string()' not 'str()'
- Blocks use { } not indentation
- 'else if' not 'elif'
"""

    def _build_generation_prompt(self, function_name: str, source_code: str, signature: str, docstring: str, config: POETConfig) -> str:
        """Build detailed prompt for LLM code generation."""

        domain_instructions = self._get_domain_instructions(config.domain)

        return f"""Generate POET-enhanced Dana code for this Python function:

Function Name: {function_name}
Signature: {signature}
Documentation: {docstring}
Domain: {config.domain}
Configuration: 
- retries: {config.retries}
- timeout: {config.timeout}
- optimize_for: {config.optimize_for or "None (POE only)"}

Original Python Code:
```python
{source_code}
```

{domain_instructions}

Requirements:
1. Analyze the function deeply - understand what it REALLY does, not just surface patterns
2. Generate intelligent validation in perceive() based on the function's actual purpose
3. Add domain-specific enhancements in operate() that make sense for this function
4. Create meaningful output validation in enforce() based on expected results
5. If optimize_for is set, implement train() with appropriate learning logic

Generate complete Dana code with all phases implemented intelligently.
"""

    def _get_domain_instructions(self, domain: str | None) -> str:
        """Get domain-specific instructions for the LLM."""
        if not domain:
            domain = "computation"  # Default domain

        domain_prompts = {
            "mathematical_operations": """
This is a mathematical function. Consider:
- What mathematical constraints apply? (division by zero, domain restrictions, etc.)
- What numerical stability issues might occur?
- What are reasonable bounds for inputs and outputs?
- Are there mathematical properties the result should satisfy?
""",
            "llm_optimization": """
This is an LLM interaction function. Consider:
- How to validate prompts for quality and safety?
- How to handle API failures and retry intelligently?
- How to monitor token usage and costs?
- How to validate response quality and coherence?
""",
            "prompt_optimization": """
This is a prompt generation function that should learn. Consider:
- How to generate multiple prompt variants for A/B testing?
- How to track which variants perform best?
- How to learn from user feedback about prompt quality?
- How to automatically improve prompts over time?
""",
            "ml_monitoring": """
This is an ML monitoring function. Consider:
- What statistical tests are appropriate for the data?
- How to detect drift, anomalies, or degradation?
- What thresholds should adapt based on historical data?
- How to reduce false positives while maintaining sensitivity?
""",
        }

        return domain_prompts.get(
            domain,
            """
Analyze the function's purpose and generate appropriate enhancements.
Think about what could go wrong and how to make it bulletproof.
""",
        )

    def _post_process_dana_code(self, dana_code: str) -> str:
        """Clean up and validate generated Dana code."""
        # Remove any markdown code blocks if LLM included them
        if "```" in dana_code:
            lines = dana_code.split("\n")
            in_code_block = False
            cleaned_lines = []

            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not line.strip().startswith("```"):
                    cleaned_lines.append(line)

            dana_code = "\n".join(cleaned_lines)

        return dana_code.strip()


# Example of what the LLM would generate for safe_divide:
EXAMPLE_LLM_OUTPUT = """
import math
import time

struct POETState {
    inputs: dict
    perceive_result: dict
    operate_result: dict
    enforce_result: dict
    metadata: dict
    errors: list[string]
    warnings: list[string]
}

def perceive(a: float, b: float, state: POETState) -> POETState {
    # Intelligent validation based on function purpose (division)
    
    # Type validation with meaningful errors
    if not isinstance(a, (int, float)) {
        state.errors.append(f"Dividend 'a' must be numeric, got {type(a).__name__}")
    }
    if not isinstance(b, (int, float)) {
        state.errors.append(f"Divisor 'b' must be numeric, got {type(b).__name__}")
    }
    
    # Division-specific validation
    if isinstance(b, (int, float)) {
        if b == 0 {
            state.errors.append("Division by zero: divisor 'b' cannot be zero")
        } else if abs(b) < 1e-10 {
            state.warnings.append(f"Divisor 'b' is very small ({b}), may cause numerical instability")
        }
    }
    
    # Check for numerical issues in inputs
    for param_name, value in [("a", a), ("b", b)] {
        if isinstance(value, float) {
            if math.isnan(value) {
                state.errors.append(f"Parameter '{param_name}' is NaN")
            } else if math.isinf(value) {
                state.errors.append(f"Parameter '{param_name}' is infinite")
            }
        }
    }
    
    # Domain knowledge: warn about potential precision loss
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) {
        if abs(a) > 1e15 or abs(b) < 1e-15 {
            state.warnings.append("Large dividend or tiny divisor may cause precision loss")
        }
    }
    
    state.perceive_result = {
        "valid": len(state.errors) == 0,
        "dividend_magnitude": abs(a) if isinstance(a, (int, float)) else null,
        "divisor_magnitude": abs(b) if isinstance(b, (int, float)) else null
    }
    return state
}

def operate(a: float, b: float, state: POETState) -> POETState {
    # Execute division with reliability enhancements
    
    if not state.perceive_result["valid"] {
        state.operate_result = {"success": false, "error": "Input validation failed"}
        return state
    }
    
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries) {
        try {
            # Monitor computation time
            start_time = time.time()
            
            # Original logic with enhancement
            result = a / b
            
            computation_time = time.time() - start_time
            
            # Check for numerical issues in result
            if isinstance(result, float) {
                if math.isnan(result) {
                    raise ValueError("Division produced NaN - numerical instability")
                } else if math.isinf(result) {
                    # Infinity might be valid for division by very small numbers
                    state.warnings.append(f"Division produced infinity: {a} / {b}")
                }
            }
            
            state.operate_result = {
                "success": true,
                "value": result,
                "attempts": attempt + 1,
                "computation_time": computation_time,
                "precision_warning": abs(b) < 1e-10 or abs(a) > 1e15
            }
            break
            
        } except Exception as e {
            if attempt == max_retries - 1 {
                state.errors.append(f"Division failed after {max_retries} attempts: {str(e)}")
                state.operate_result = {"success": false, "attempts": max_retries}
            } else {
                # Exponential backoff
                time.sleep(retry_delay * (2 ** attempt))
            }
        }
    }
    
    return state
}

def enforce(state: POETState) -> POETState {
    # Validate division result meets business rules
    
    if not state.operate_result.get("success", false) {
        state.enforce_result = {"valid": false}
        return state
    }
    
    result = state.operate_result["value"]
    
    # Domain-specific validation for division results
    if isinstance(result, (int, float)) {
        # Check for unreasonable magnitudes that suggest errors
        if abs(result) > 1e100 {
            state.errors.append(f"Division result unreasonably large: {result}")
        }
        
        # Warn about potential precision issues
        if state.operate_result.get("precision_warning", false) {
            state.warnings.append("Result may have reduced precision due to extreme input values")
        }
        
        # Business rule: financial calculations often need specific precision
        if "financial" in state.metadata.get("context", "") {
            # Round to reasonable precision for financial calculations
            result = round(result, 4)
            state.warnings.append("Result rounded to 4 decimal places for financial context")
        }
    }
    
    state.enforce_result = {
        "valid": len(state.errors) == 0,
        "final_value": result if len(state.errors) == 0 else null,
        "has_warnings": len(state.warnings) > 0,
        "quality_score": 1.0 if not state.warnings else 0.8
    }
    
    return state
}

def enhanced_safe_divide(a: float, b: float) -> float {
    # Initialize POET state
    state = POETState(
        inputs={"a": a, "b": b},
        perceive_result={},
        operate_result={},
        enforce_result={},
        metadata={
            "function": "safe_divide",
            "domain": "mathematical_operations",
            "start_time": time.time()
        },
        errors=[],
        warnings=[]
    )
    
    # Execute P→O→E pipeline
    state = perceive(a, b, state)
    state = operate(a, b, state)
    state = enforce(state)
    
    # Log warnings if any
    if state.warnings {
        for warning in state.warnings {
            log(f"Warning: {warning}")
        }
    }
    
    # Handle errors
    if not state.enforce_result.get("valid", false) {
        error_msg = "; ".join(state.errors) if state.errors else "Validation failed"
        raise ValueError(f"POET validation failed: {error_msg}")
    }
    
    return state.enforce_result["final_value"]
}
"""
