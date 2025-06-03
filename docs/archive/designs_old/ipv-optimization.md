> **Note: This IPV (Infer-Process-Validate) document is archived.**
> The core concepts and goals described herein have been superseded and further developed under the **PAV (Perceive → Act → Validate) execution model**.
> For the current design, please refer to the [PAV Execution Model documentation](../../design/02_dana_runtime_and_execution/pav_execution_model.md).

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

    def validate_phase(self, result: Any, ipv_call_context: Dict[str, Any]) -> Any:
        """Validates, cleans, and coerces the result based on IPVCallContext."""
        # Basic validation: try to coerce to dana_desired_type
        # More sophisticated validation in subclasses or helper methods
        desired_type = ipv_call_context["dana_desired_type"]
        # ... (coercion/validation logic here, potentially using a type utility) ...
        return result # Return validated/coerced result
```

### 6.2. Specialized Executor: `IPVReason` (for LLM-based reasoning)
`IPVReason` is a specialization of `IPVExecutor` for functions like `reason()`.

```python
class IPVReason(IPVExecutor):
    def infer_phase(self, function_name: str, sandbox_context: SandboxContext, args: Dict[str, Any]) -> Dict[str, Any]:
        # Call super to get base IPVCallContext populated
        ipv_call_context = super().infer_phase(function_name, sandbox_context, args)

        # IPVReason specific inference (e.g., analyze prompt, determine if LLM analysis is needed for domain/task)
        # For simplicity, we assume it always decides LLM analysis is useful here.
        # It might call an LLM here to get refined domain/task if original prompt is too vague.
        inferred_details = {
            "llm_analysis_required_for_prompt_enhancement": True, # Example flag
            "inferred_domain_preliminary": "general", # Could be refined by an LLM call
            "inferred_task_type_preliminary": "general" # Could be refined
        }
        ipv_call_context["inferred_operation_details"].update(inferred_details)
        ipv_call_context["executor_type"] = "IPVReason"
        return ipv_call_context

    def process_phase(self, ipv_call_context: Dict[str, Any]) -> Any:
        original_prompt = ipv_call_context["arguments"].get("prompt") # Specific to reason()
        if not original_prompt:
            raise ValueError("'prompt' argument missing for IPVReason")

        # Format the full context for the LLM
        enhanced_prompt_str = self.format_context_for_llm(
            original_prompt=original_prompt,
            code_site_context=ipv_call_context.get("code_site_context"),
            ambient_system_context=ipv_call_context["ambient_system_context"],
            dana_desired_type=ipv_call_context["dana_desired_type"]
            # Potentially pass ipv_call_context["inferred_operation_details"] too
        )

        # Actual LLM call would happen here
        # llm_resource = get_llm_resource_from_somewhere(sandbox_context)
        # llm_response = llm_resource.query(enhanced_prompt_str, ...)
        # For now, returning the formatted prompt for illustration:
        llm_response = f"LLM_PROCESSED_PROMPT:\n{enhanced_prompt_str}"
        return llm_response

    def format_context_for_llm(
        self,
        original_prompt: str,
        code_site_context: Optional[dict],
        ambient_system_context: Dict[str, Any],
        dana_desired_type: Any
    ) -> str:
        """Formats all available context for an LLM prompt."""
        
        ipv_profile = ambient_system_context.get("__dana_ipv_profile", "default")
        task_desc = ambient_system_context.get("__current_task_description", "N/A")
        active_domains_list = ambient_system_context.get("__active_domains", [])
        active_domains = ", ".join(active_domains_list) if active_domains_list else "N/A"

        context_lines = [
            f"- Caller Desired Return Type: {str(dana_desired_type)}",
            f"- IPV Profile Hint: {ipv_profile}",
            f"- Agent Task Context: {task_desc}",
            f"- Prioritized Domains: {active_domains}",
        ]

        if code_site_context:
            comments = code_site_context.get("comments", [])
            if comments: context_lines.append(f"- Code Comments: {'; '.join(comments)}")
            # Add more details from code_site_context as needed...

        formatted_context_block = "\n".join([f"  {line}" for line in context_lines])

        enhanced_prompt = f"""Analyze the following request with the provided contextual information:

REQUEST: "{original_prompt}"

CONTEXTUAL INFORMATION:
{formatted_context_block}

Based on ALL the provided context and the request, please:
1.  Refine understanding of the domain and specific task.
2.  Generate a response that directly addresses the request, is optimized for the desired return type ({str(dana_desired_type)}), and aligns with the IPV profile ({ipv_profile}) and other contextual cues.
"""
        return enhanced_prompt

    def validate_phase(self, result: Any, ipv_call_context: Dict[str, Any]) -> Any:
        # Override for IPVReason specific validation (e.g., parsing LLM string to desired type)
        # This would involve robust parsing and type coercion logic.
        # For example, if dana_desired_type is a struct, attempt to parse `result` (LLM string) into that struct.
        return super().validate_phase(result, ipv_call_context) # Calls base validation too
```

## 7. Optimization Dimensions & Profiles (Summary)
(This section remains largely the same as previously discussed, referencing the 5 dimensions: Reliability, Precision, Safety, Structure, Context, and the concept of Profiles like "default", "production", etc. These are primarily consumed via `system:__dana_ipv_profile` and `system:__dana_ipv_settings_override` within the `IPVCallContext.ambient_system_context`.)

## 8. Type-Driven Optimization (Summary)
(This section also remains largely the same, detailing how `IPVCallContext.dana_desired_type` drives specific cleaning and validation steps in the `validate_phase`. The actual logic for this would live within the `validate_phase` implementations or helper utilities.)

This revised IPV architecture provides a more powerful and generalizable framework for building intelligent, context-aware, and robust Dana functions.