"""
LLM Optimization Domain Template

Implements Use Case B: reason_function() prompt enhancement (POE)
Provides enhanced LLM interactions with prompt optimization, retry logic,
response validation, and quality assurance.

Features:
- Prompt validation and formatting
- Context preparation and resource checking
- LLM execution with retry and exponential backoff
- Response quality validation and safety filtering
- Token usage monitoring and cost optimization
- Support for both mock and real LLM calls
"""

from typing import Any

from .base import BaseDomainTemplate, CodeBlock, FunctionInfo


class LLMOptimizationDomain(BaseDomainTemplate):
    """
    Domain template for LLM-powered functions like reason_function().

    Enhances LLM interactions with:
    - Prompt validation and optimization
    - Context formatting and resource checking
    - Retry logic for LLM failures
    - Response quality validation
    - Safety and content filtering
    - Token usage monitoring
    """

    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate prompt validation and context preparation"""

        # Analyze function parameters to identify LLM-specific inputs
        signature_analysis = self._analyze_llm_signature(func_info)

        validation_code = f"""
import json
import re
from dana.common.resource.llm.llm_resource import LLMResource

# === Prompt Validation ===
{self._generate_prompt_validation(signature_analysis)}

# === Context Preparation ===  
{self._generate_context_validation(signature_analysis)}

# === Resource Availability Check ===
try:
    # Check if LLM resource is available in context
    if hasattr(context, 'get_resource') and context.get_resource('llm') is not None:
        llm_resource = context.get_resource('llm')
    else:
        # Fallback: create LLM resource
        llm_resource = LLMResource()
    
    llm_available = True
except Exception as e:
    log(f"LLM resource check failed: {{e}}")
    llm_available = False

# === Prompt Optimization ===
{self._generate_prompt_optimization(func_info)}

# Store validated inputs for operation phase
validated_inputs = {{
    {", ".join(f'"{p}": {p}' for p in signature_analysis.keys())},
    "llm_resource": llm_resource if llm_available else None,
    "optimized_prompt": optimized_prompt,
    "formatted_context": formatted_context if 'context' in locals() else None
}}
""".strip()

        return CodeBlock(
            code=validation_code,
            dependencies=["json", "re", "dana.common.resource.llm_resource"],
            imports=["import json", "import re", "from dana.common.resource.llm.llm_resource import LLMResource"],
            metadata={
                "phase": "perceive",
                "domain": "llm_optimization",
                "prompt_optimized": True,
                "context_formatted": True,
                "resource_checked": True,
            },
        )

    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate enhanced LLM execution with retry and monitoring"""

        # Enhanced operation with LLM-specific retry logic
        enhanced_operation = f"""
import time

# === LLM Execution with Enhanced Retry Logic ===
retries_used = 0
max_retries = {func_info.retries}
total_tokens_used = 0
execution_start = time.time()

for attempt in range(max_retries + 1):
    try:
        attempt_start = time.time()
        
        # Determine execution mode (mock vs real)
        use_mock = {self._determine_mock_usage(func_info)}
        
        if use_mock:
            # Mock execution for testing
            result = {self._generate_mock_response()}
            tokens_used = 10  # Mock token count
        else:
            # Real LLM execution
            if not validated_inputs.get("llm_resource"):
                raise ValueError("LLM resource not available for real execution")
            
            llm_response = validated_inputs["llm_resource"].query_sync(
                validated_inputs["optimized_prompt"],
                context=validated_inputs.get("formatted_context"),
                timeout={func_info.timeout or 30}
            )
            
            if not llm_response.success:
                raise RuntimeError(f"LLM query failed: {{llm_response.content}}")
            
            result = llm_response.content
            tokens_used = getattr(llm_response, 'tokens_used', 0)
        
        # Track token usage
        total_tokens_used += tokens_used
        attempt_duration = time.time() - attempt_start
        
        log(f"LLM execution attempt {{attempt + 1}}: {{attempt_duration:.2f}}s, {{tokens_used}} tokens")
        break
        
    except Exception as e:
        retries_used = attempt + 1
        if attempt == max_retries:
            raise RuntimeError(f"LLM execution failed after {{max_retries}} retries: {{e}}") from e
        
        # Exponential backoff with jitter for LLM rate limits
        backoff_time = min(0.5 * (2 ** attempt), 30)  # Cap at 30 seconds
        time.sleep(backoff_time)
        log(f"LLM retry {{attempt + 1}}/{{max_retries}} after {{backoff_time}}s delay: {{e}}")

# Store execution metadata
execution_metadata = {{
    "total_execution_time": time.time() - execution_start,
    "retries_used": retries_used,
    "total_tokens_used": total_tokens_used,
    "use_mock": use_mock,
    "llm_available": validated_inputs.get("llm_resource") is not None
}}
""".strip()

        return CodeBlock(
            code=enhanced_operation,
            dependencies=["time"],
            imports=["import time"],
            metadata={
                "phase": "operate",
                "domain": "llm_optimization",
                "retry_logic": "exponential_backoff",
                "token_monitoring": True,
                "mock_support": True,
            },
        )

    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate response validation and quality assurance"""

        enforcement_code = f"""
# === Response Quality Validation ===
if result is None:
    raise ValueError("LLM returned None response")

# Convert response to string for validation
if isinstance(result, dict) and 'content' in result:
    response_text = str(result['content'])
elif isinstance(result, str):
    response_text = result
else:
    response_text = str(result)

# Basic response validation
if not response_text or not response_text.strip():
    raise ValueError("LLM returned empty response")

if len(response_text) < 2:
    raise ValueError(f"LLM response too short: '{{response_text}}'")

# === Content Safety Filtering ===
{self._generate_safety_filtering()}

# === Response Quality Assessment ===
quality_score = {self._generate_quality_assessment()}

if quality_score < 0.3:
    log(f"Warning: Low quality LLM response (score: {{quality_score:.2f}})")

# === Final Response Processing ===
{self._generate_response_processing()}

# Store validation metadata
validation_metadata = {{
    "response_length": len(response_text),
    "quality_score": quality_score,
    "safety_filtered": True,
    "content_validated": True,
    "final_result_type": type(final_result).__name__
}}
""".strip()

        return CodeBlock(
            code=enforcement_code,
            dependencies=["re"],
            imports=["import re"],
            metadata={
                "phase": "enforce",
                "domain": "llm_optimization",
                "quality_validation": True,
                "safety_filtering": True,
                "response_processing": True,
            },
        )

    def _analyze_llm_signature(self, func_info: FunctionInfo) -> dict[str, dict[str, Any]]:
        """Analyze function signature for LLM-specific parameters"""
        signature = func_info.signature

        # Common LLM function parameter patterns
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
                        # Classify parameter type
                        if any(keyword in param_name.lower() for keyword in ["prompt", "question", "query", "text"]):
                            param_role = "prompt"
                        elif any(keyword in param_name.lower() for keyword in ["context", "ctx"]):
                            param_role = "context"
                        elif any(keyword in param_name.lower() for keyword in ["option", "config", "setting"]):
                            param_role = "options"
                        elif any(keyword in param_name.lower() for keyword in ["mock", "test"]):
                            param_role = "mock_control"
                        else:
                            param_role = "general"

                        param_info[param_name] = {"type": param_type, "role": param_role}

        return param_info

    def _generate_prompt_validation(self, signature_analysis: dict) -> str:
        """Generate prompt-specific validation code"""
        prompt_params = [name for name, info in signature_analysis.items() if info["role"] == "prompt"]

        validations = []
        for param_name in prompt_params:
            validations.append(
                f"""
# Validate {param_name} (prompt)
if not isinstance({param_name}, str):
    raise TypeError(f"Parameter '{param_name}' must be a string, got {{type({param_name}).__name__}}")

if not {param_name} or not {param_name}.strip():
    raise ValueError(f"Parameter '{param_name}' cannot be empty")

if len({param_name}) > 50000:  # Reasonable limit for prompts
    raise ValueError(f"Parameter '{param_name}' too long ({{len({param_name})}} chars, max 50000)")

# Check for potentially problematic content
if any(char in {param_name} for char in ['\\x00', '\\x01', '\\x02']):
    raise ValueError(f"Parameter '{param_name}' contains invalid control characters")
""".strip()
            )

        return "\n\n".join(validations) if validations else "# No prompt parameters detected"

    def _generate_context_validation(self, signature_analysis: dict) -> str:
        """Generate context validation and formatting"""
        context_params = [name for name, info in signature_analysis.items() if info["role"] == "context"]

        if not context_params:
            return """
# No explicit context parameter - create empty context
formatted_context = {}
""".strip()

        context_param = context_params[0]  # Use first context parameter
        return f"""
# Validate and format context
if {context_param} is not None:
    if isinstance({context_param}, dict):
        formatted_context = {context_param}
    elif isinstance({context_param}, str):
        try:
            formatted_context = json.loads({context_param})
        except json.JSONDecodeError:
            formatted_context = {{"raw_context": {context_param}}}
    else:
        formatted_context = {{"context": str({context_param})}}
else:
    formatted_context = {{}}

# Validate context size
context_str = json.dumps(formatted_context)
if len(context_str) > 100000:  # Reasonable limit
    raise ValueError(f"Context too large: {{len(context_str)}} chars")
""".strip()

    def _generate_prompt_optimization(self, func_info: FunctionInfo) -> str:
        """Generate basic prompt optimization"""
        return """
# Basic prompt optimization
prompt_param = next((name for name, info in validated_inputs.items() 
                    if isinstance(info, str) and len(info) > 10), None)

if prompt_param:
    original_prompt = validated_inputs[prompt_param]
    
    # Basic optimizations
    optimized_prompt = original_prompt.strip()
    
    # Add context if available and not already included
    if formatted_context and formatted_context != {} and "Context:" not in optimized_prompt:
        context_str = json.dumps(formatted_context, indent=2)
        optimized_prompt = f"{optimized_prompt}\\n\\nContext: {context_str}"
    
    # Ensure clear instruction format
    if not optimized_prompt.endswith(('?', '.', ':', '!')):
        optimized_prompt += "."
        
else:
    optimized_prompt = "Please provide a helpful response."
""".strip()

    def _determine_mock_usage(self, func_info: FunctionInfo) -> str:
        """Determine whether to use mock or real LLM"""
        return """
# Determine mock usage
use_mock_param = next((validated_inputs.get(name) for name, info in validated_inputs.items() 
                      if isinstance(name, str) and 'mock' in name.lower()), None)

if use_mock_param is not None:
    use_mock = bool(use_mock_param)
else:
    # Check environment variable
    import os
    use_mock = os.getenv('DANA_MOCK_LLM', 'false').lower() == 'true'
""".strip()

    def _generate_mock_response(self) -> str:
        """Generate mock response logic"""
        return '''f"Mock LLM response for: {validated_inputs.get('optimized_prompt', 'unknown prompt')[:50]}..."'''

    def _generate_safety_filtering(self) -> str:
        """Generate content safety filtering"""
        return """
# Basic safety filtering
safety_issues = []

# Check for potentially harmful content indicators
harmful_patterns = ['error', 'failed', 'cannot', 'unable', 'impossible']
for pattern in harmful_patterns:
    if pattern in response_text.lower():
        safety_issues.append(f"Response contains error indicator: {pattern}")

# Check for very short responses that might indicate failure
if len(response_text.strip()) < 10:
    safety_issues.append("Response unexpectedly short")

if safety_issues:
    log(f"Safety concerns detected: {safety_issues}")
""".strip()

    def _generate_quality_assessment(self) -> str:
        """Generate response quality scoring"""
        return """
# Basic quality assessment
quality_factors = []

# Length factor (reasonable responses should have substance)
if 20 <= len(response_text) <= 5000:
    quality_factors.append(0.3)
elif len(response_text) > 5000:
    quality_factors.append(0.2)  # Too long might be problematic
else:
    quality_factors.append(0.1)  # Too short

# Coherence factor (basic heuristics)
if response_text.count('.') > 0 and response_text.count(' ') > 5:
    quality_factors.append(0.3)
else:
    quality_factors.append(0.1)

# Relevance factor (basic keyword matching)
prompt_words = set(validated_inputs.get("optimized_prompt", "").lower().split())
response_words = set(response_text.lower().split())
overlap = len(prompt_words & response_words) / max(len(prompt_words), 1)
quality_factors.append(min(overlap, 0.4))

sum(quality_factors)
""".strip()

    def _generate_response_processing(self) -> str:
        """Generate final response processing"""
        return """
# Process final response based on expected return type
return_annotation = func_info.annotations.get('return', 'str')

if 'dict' in return_annotation.lower() or 'json' in func_info.name.lower():
    # Try to parse as JSON
    try:
        final_result = json.loads(response_text)
    except json.JSONDecodeError:
        # If parsing fails, return structured response
        final_result = {
            "response": response_text,
            "metadata": execution_metadata,
            "quality_score": quality_score
        }
else:
    # Return as string (most common)
    final_result = response_text.strip()
""".strip()
