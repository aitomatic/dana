| [← REPL](./repl.md) | [Type System and Casting →](./type_system_and_casting.md) |
|---|---|

# IPV (Infer-Process-Validate) Architecture for Dana Functions

## 1. Overview

Dana introduces **IPV (Infer-Process-Validate)** as a foundational pattern for intelligent and robust function execution. IPV applies **Postel's Law**: "be liberal in what you accept from the caller and the environment, be conservative in what you produce as a result."

**Core Philosophy**: IPV makes Dana functions smarter, more reliable, and more user-friendly by systematically handling the complexity of context inference, adaptive processing, and strict validation. While initially conceived for LLM-interactions like the `reason()` function, the IPV pattern is generalizable to any Dana function that can benefit from enhanced context awareness and adaptive execution.

## 2. The IPV Pattern

IPV is a three-phase pattern that underpins the execution of an IPV-enabled Dana function:

### 2.1. INFER (Liberal Input & Context Acceptance)
-   **Collect Function Call Details**: Gather the function name and the explicit arguments passed by the caller.
-   **Gather Code-Site Context**: Analyze the Dana source code at the call site to extract comments, surrounding variable names and types, and other local code structures (via `CodeContextAnalyzer`).
-   **Gather Ambient System Context**: Retrieve relevant `system:__...` variables from the `SandboxContext` (e.g., `__dana_desired_type`, `__dana_ipv_profile`, `__current_task_id`, `__user_id`, etc.).
-   **Perform Executor-Specific Inference**: Based on all collected information, the specific `IPVExecutor` for the function determines the optimal processing strategy, infers missing details, or identifies the nature of the task. For example, `IPVReason` might infer the domain and task type for an LLM call.
-   **Output**: Produces a standardized `IPVCallContext` dictionary containing all gathered and inferred information.

### 2.2. PROCESS (Generous & Adaptive Transformation)
-   **Input**: Receives the `IPVCallContext` from the `infer_phase`.
-   **Execute Core Logic**: Performs the function's main task, using the rich information in `IPVCallContext` to adapt its behavior. This might involve:
    *   Formatting and dispatching calls to LLMs (e.g., `IPVReason`).
    *   Performing complex data transformations.
    *   Interacting with external services or capabilities.
    *   Applying dynamic algorithms based on inferred context.
-   **Iterate if Necessary**: May include retry logic or iterative refinement based on intermediate results and IPV profile settings.

### 2.3. VALIDATE (Conservative Output Guarantee)
-   **Input**: Receives the raw result from the `process_phase` and the `IPVCallContext`.
-   **Enforce `dana_desired_type`**: Validates and, if possible, coerces the result to match the `IPVCallContext.dana_desired_type`.
-   **Apply Quality Checks**: Performs other integrity, consistency, or business rule checks based on `IPVCallContext.ambient_system_context` (e.g., IPV profile) or `IPVCallContext.executor_specific_details`.
-   **Clean and Normalize**: Strips extraneous information, standardizes format, and ensures the output is clean and reliable.

### Example: IPV-enabled `reason()` function
```dana
# User provides minimal prompt with context
# Extract total price from medical invoice
private:price: float = reason("get price")

# INFER phase for reason():
# - Gathers function_name="reason", arguments={"get price"}
# - Gathers system:__dana_desired_type=float, system:__dana_ipv_profile="default"
# - Analyzes code comments ("# Extract total price..."), surrounding code.
# - IPVReason infers domain=medical/financial, task=extraction.
# - Produces IPVCallContext.
# PROCESS phase for reason():
# - Uses IPVCallContext to build a detailed prompt for the LLM.
# - LLM returns a response.
# VALIDATE phase for reason():
# - Ensures LLM response is parsable to a float.
# - Cleans "$29.99" to 29.99.
# - Returns float(29.99).
```

## 3. Standardized IPV Call Context Payload

The `IPVCallContext` is a dictionary produced by the `infer_phase` and consumed by subsequent phases. It standardizes the information flow within an IPV execution.

```python
# Conceptual structure of the IPVCallContext dictionary
IPVCallContext = {
    # === Information about the original Dana function call ===
    "function_name": str,              # Name of the IPV-enabled Dana function being called.
    "arguments": Dict[str, Any],       # Original arguments (name: value) passed to the Dana function.

    # === Context derived by the IPV system during the INFER phase ===
    "dana_desired_type": Any,          # From system:__dana_desired_type (caller's desired return type).
    
    "code_site_context": Optional[dict], # Analysis of the call site from CodeContextAnalyzer.
                                         # Example: {"comments": [], "surrounding_vars": {}, ...}
    
    "ambient_system_context": Dict[str, Any],  # Snapshot of relevant system:__... variables.
                                               # Example: {"__dana_ipv_profile": "default", 
                                               #          "__current_task_id": "task123", ...}
                                               
    "optimization_hints": List[str],   # Derived from type system, comments, or annotations.

    # === Executor-specific inferred details ===
    "executor_type": str,              # Class name of the IPVExecutor (e.g., "IPVReason").
    "inferred_operation_details": Dict[str, Any] # Details inferred by this specific executor.
                                                 # e.g., for IPVReason: {"inferred_domain": "finance"}
}
```

## 4. Enabling IPV for Functions

Not all Dana functions require IPV. It's an opt-in mechanism for functions that benefit from contextual intelligence.

*   **Built-in (Python) Functions**: Can be associated with an `IPVExecutor` class, potentially via a registration mechanism or a decorator in their Python definition.
*   **User-Defined Dana Functions**: A Dana-level annotation or a specific function property could mark them as IPV-enabled and link them to an `IPVExecutor` configuration.

When the Dana interpreter encounters a call to an IPV-enabled function, it will delegate the execution to the function's designated `IPVExecutor` rather than calling the function directly.

## 5. Context Sources for IPV

### 5.1. Code-Site Context (`CodeContextAnalyzer`)
The `CodeContextAnalyzer` (implementation TBD) is responsible for parsing the Dana source code around the function call to extract:

```python
# Conceptual structure of the output from CodeContextAnalyzer (becomes IPVCallContext.code_site_context)
CodeContext = {
    "comments": List[str],              # Block comments preceding the call.
    "inline_comments": List[str],       # Inline comments on the same line or preceding lines.
    "variable_context": Dict[str, Any], # Nearby variables and their (inferred or hinted) types.
    "type_hints_at_call": Dict[str, str],# Type hints used in the assignment if the call is on the RHS.
    "surrounding_code_lines": List[str],# A few lines of code before and after the call.
    "parent_function_name": Optional[str] # Name of the Dana function enclosing this call, if any.
}
```

### 5.2. Ambient System Context (from `SandboxContext` `system:` scope)
These variables provide broader operational context and are read from `SandboxContext.get("system:__variable_name")` by the `infer_phase`.

*   `system:__dana_desired_type`: The explicit return type desired by the caller.
*   `system:__dana_ipv_profile`: (Optional) Active IPV profile (e.g., "default", "production", "creative").
*   `system:__dana_ipv_settings_override`: (Optional) Dictionary of IPV dimension overrides.
*   `system:__current_task_id`: (Optional) Current agent task ID.
*   `system:__current_task_description`: (Optional) Description of the current task.
*   `system:__session_id`: (Optional) Current session ID.
*   `system:__user_id`: (Optional) Current user ID.
*   `system:__locale`: (Optional) Preferred locale (e.g., "en-US").
*   `system:__active_domains`: (Optional) List of active domain knowledge areas (e.g., `["finance"]`).

### 5.3. LLM-Driven Analysis (Example: `IPVReason`)
Specialized executors like `IPVReason` use the collected code-site and ambient context to further refine their understanding, often by querying an LLM as part of their `infer_phase` or at the beginning of their `process_phase`.

```python
# Example snippet within IPVReason.process_phase, using a formatted prompt
# self.format_context_for_llm is defined in section 6.2
enhanced_prompt = self.format_context_for_llm(
    original_intent=ipv_call_context["arguments"].get("prompt"), # Assuming 'prompt' is an arg to reason()
    code_site_context=ipv_call_context["code_site_context"],
    ambient_system_context=ipv_call_context["ambient_system_context"],
    dana_desired_type=ipv_call_context["dana_desired_type"]
)
# ... then call LLM with enhanced_prompt ...
```

## 6. IPV Executor Design

### 6.1. Base Class: `IPVExecutor`
```python
class IPVExecutor: # Defined in Python
    """Base IPV control loop for any IPV-enabled Dana function."""

    def execute(self, function_name: str, sandbox_context: SandboxContext, args: Dict[str, Any]) -> Any:
        # Standard IPV pipeline with iteration support (iteration logic TBD)
        # args is a dictionary of arguments passed to the Dana function

        ipv_call_context = self.infer_phase(function_name, sandbox_context, args)
        
        # Ensure essential keys are present from infer_phase
        assert "function_name" in ipv_call_context
        assert "arguments" in ipv_call_context
        assert "dana_desired_type" in ipv_call_context # Should be filled even if with 'any'
        assert "ambient_system_context" in ipv_call_context
        assert "executor_type" in ipv_call_context
        assert "inferred_operation_details" in ipv_call_context

        processed_result = self.process_phase(ipv_call_context)
        final_result = self.validate_phase(processed_result, ipv_call_context)
        return final_result

    def infer_phase(self, function_name: str, sandbox_context: SandboxContext, args: Dict[str, Any]) -> Dict[str, Any]:
        """Collects all context and performs executor-specific inference.
           MUST return a dictionary conforming to IPVCallContext structure.
        """
        # Implementation populates the IPVCallContext dictionary
        desired_type = sandbox_context.get("system:__dana_desired_type", "any")
        
        # Simplified CodeContextAnalyzer interaction for example
        code_site_ctx = CodeContextAnalyzer().analyze(sandbox_context, function_name, args) 

        ambient_ctx = {
            "__dana_ipv_profile": sandbox_context.get("system:__dana_ipv_profile"),
            "__dana_ipv_settings_override": sandbox_context.get("system:__dana_ipv_settings_override"),
            "__current_task_id": sandbox_context.get("system:__current_task_id"),
            # ... gather all other system:__... variables ...
        }
        ambient_ctx = {k: v for k, v in ambient_ctx.items() if v is not None}

        # Base infer_phase gathers common context.
        # Subclasses will add/override executor_type and inferred_operation_details.
        base_ipv_context = {
            "function_name": function_name,
            "arguments": args,
            "dana_desired_type": desired_type,
            "code_site_context": code_site_ctx, # Placeholder
            "ambient_system_context": ambient_ctx, # Placeholder
            "optimization_hints": [], # Placeholder, could be populated by CodeContextAnalyzer
            "executor_type": self.__class__.__name__,
            "inferred_operation_details": {} # Subclasses should populate this
        }
        return base_ipv_context

    def process_phase(self, ipv_call_context: Dict[str, Any]) -> Any:
        """Executes the core logic of the function using IPVCallContext."""
        raise NotImplementedError("Subclasses must implement process_phase")

    def validate_phase(self, raw_result: Any, ipv_call_context: Dict[str, Any]) -> Any:
        """Validates and cleans the result, ensuring it matches dana_desired_type."""
        raise NotImplementedError("Subclasses must implement validate_phase")

```

### 6.2. Specialized Executor Example: `IPVReason` (for `reason()` function)
This executor specializes in handling LLM interactions for the `reason()` function.

```python
class IPVReason(IPVExecutor):
    """IPVExecutor for the reason() Dana function."""

    def infer_phase(self, function_name: str, sandbox_context: SandboxContext, args: Dict[str, Any]) -> Dict[str, Any]:
        # Start with base context
        ipv_call_context = super().infer_phase(function_name, sandbox_context, args)

        # IPVReason specific inference
        # Example: Infer domain based on code comments or desired type
        inferred_domain = "general" # Default
        if ipv_call_context["code_site_context"] and "comments" in ipv_call_context["code_site_context"]:
            if any("financial" in c.lower() for c in ipv_call_context["code_site_context"]["comments"]):
                inferred_domain = "finance"
            elif any("medical" in c.lower() for c in ipv_call_context["code_site_context"]["comments"]):
                inferred_domain = "medical"
        
        # Store executor-specific inferred details
        ipv_call_context["inferred_operation_details"] = {
            "llm_task_type": "question_answering", # Could be classification, generation, etc.
            "inferred_domain": inferred_domain,
            "model_preference": sandbox_context.get("system:__llm_model_preference") 
                                or self._get_default_model_for_domain(inferred_domain)
        }
        return ipv_call_context

    def process_phase(self, ipv_call_context: Dict[str, Any]) -> Any:
        """Formats prompt, calls LLM, and returns raw LLM output."""
        original_intent = ipv_call_context["arguments"].get("prompt", "") # Assuming 'prompt' is an arg
        
        # Format the prompt for the LLM using all available context
        enhanced_prompt = self._format_context_for_llm(
            original_intent=original_intent,
            code_site_context=ipv_call_context["code_site_context"],
            ambient_system_context=ipv_call_context["ambient_system_context"],
            dana_desired_type=ipv_call_context["dana_desired_type"],
            inferred_details=ipv_call_context["inferred_operation_details"]
        )
        
        # Actual LLM call (simplified)
        # llm_resource = LLMResourceProvider.get_resource(ipv_call_context["inferred_operation_details"]["model_preference"])
        # raw_llm_response = llm_resource.query(enhanced_prompt)
        # return raw_llm_response
        return f"LLM_RESPONSE_FOR[{enhanced_prompt[:100]}...]" # Placeholder for actual LLM call

    def validate_phase(self, raw_llm_response: Any, ipv_call_context: Dict[str, Any]) -> Any:
        """Validates LLM output, cleans it, and coerces to dana_desired_type."""
        desired_type = ipv_call_context["dana_desired_type"]
        
        # Basic validation and cleaning (example)
        if not isinstance(raw_llm_response, str):
            # raise IPVValidationError("LLM response was not a string.")
            raw_llm_response = str(raw_llm_response) # Attempt coercion

        cleaned_response = raw_llm_response.strip()

        # Type coercion (very simplified example)
        try:
            if desired_type == float:
                # More robust parsing needed here, e.g. handle currency symbols, commas
                return float(cleaned_response.replace("$","").replace(",",""))
            elif desired_type == int:
                return int(float(cleaned_response.replace("$","").replace(",",""))) # Handle potential float string
            elif desired_type == bool:
                return cleaned_response.lower() in ["true", "yes", "1"]
            elif desired_type == str:
                return cleaned_response
            elif desired_type == "any" or desired_type is None:
                 return cleaned_response # Or attempt to parse JSON/structured data
            else:
                # Attempt a generic conversion or raise error if not possible
                # For a custom struct type, this might involve JSON parsing + validation
                # raise IPVValidationError(f"Cannot coerce LLM output to desired type: {desired_type}")
                return cleaned_response # Fallback for this example
        except ValueError as e:
            # raise IPVValidationError(f"Error coercing LLM output '{cleaned_response}' to {desired_type}: {e}")
            return cleaned_response # Fallback

        return cleaned_response # Fallback for unhandled types

    def _format_context_for_llm(self, original_intent: str, code_site_context: Optional[dict], 
                                ambient_system_context: Dict[str, Any], dana_desired_type: Any, 
                                inferred_details: Dict[str, Any]) -> str:
        """
        Constructs a rich prompt for the LLM by combining all available context.
        This is a critical part of IPVReason.
        """
        prompt_parts = []
        prompt_parts.append(f"User Intent: {original_intent}")

        if dana_desired_type and dana_desired_type != "any":
            prompt_parts.append(f"Desired Output Type: {str(dana_desired_type)}")

        if inferred_details:
            if "inferred_domain" in inferred_details and inferred_details["inferred_domain"] != "general":
                prompt_parts.append(f"Contextual Domain: {inferred_details['inferred_domain']}")
            if "llm_task_type" in inferred_details:
                 prompt_parts.append(f"Assumed Task Type: {inferred_details['llm_task_type']}")
        
        # Add code site context
        if code_site_context:
            if code_site_context.get("comments"):
                prompt_parts.append("Code Comments for Context:")
                for comment in code_site_context["comments"]:
                    prompt_parts.append(f"- {comment}")
            # Could add surrounding_vars, parent_function_name etc.

        # Add ambient system context
        if ambient_system_context:
            prompt_parts.append("System Context:")
            for key, value in ambient_system_context.items():
                if value: # Only include if value is present
                    prompt_parts.append(f"- {key.replace('__dana_', '')}: {value}")
        
        # Add instructions for the LLM
        prompt_parts.append("
Based on the above, provide a concise and direct answer.")
        if dana_desired_type and dana_desired_type != "any":
             prompt_parts.append(f"Ensure your answer can be directly parsed as a {str(dana_desired_type)}.")

        return "
".join(prompt_parts)

    def _get_default_model_for_domain(self, domain: str) -> Optional[str]:
        # Example logic, can be expanded
        if domain == "finance":
            return "gpt-4-turbo" # Example model preference
        return None


## 7. `CodeContextAnalyzer` (Conceptual)

This component is responsible for static analysis of Dana code at the call site.
- **Input**: `SandboxContext` (to access current code, AST if available), `function_name`, `args`.
- **Output**: `CodeContext` dictionary (see section 5.1).
- **Implementation**: Could involve regex, AST traversal if the full script AST is available, or simpler heuristics. Its complexity can evolve. For initial versions, it might only extract preceding comments.

## 8. Future Considerations

-   **IPV Profiles**: Allow defining named IPV profiles (`system:__dana_ipv_profile`) that tune the behavior of all three phases (e.g., "strict_validation_profile", "creative_inference_profile").
-   **Iterative Refinement**: The `PROCESS` phase could involve loops where results are internally validated and re-processed until criteria are met or a timeout occurs.
-   **Extensibility**: Clear plugin model for custom `IPVExecutor` implementations and `CodeContextAnalyzer` strategies.
-   **Async IPV**: How IPV pattern adapts to asynchronous Dana functions.

---
*Self-reflection: This document outlines a comprehensive IPV architecture. The `CodeContextAnalyzer` is a key dependency that needs further design. The example `IPVReason` shows how specific executors would customize each phase. The `SandboxContext` is central for passing `system:__...` variables. The interaction with the actual LLM resource and type system for coercion needs robust implementation details in respective components.* 