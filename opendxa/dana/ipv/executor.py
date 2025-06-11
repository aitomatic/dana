"""
IPV Executor - Base class and specialized implementations for IPV pattern.

This module provides the IPVExecutor inheritance hierarchy that implements
the Infer-Process-Validate pattern for different types of intelligent operations.
"""

import time
from abc import ABC, abstractmethod
from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.queryable import QueryStrategy
from opendxa.common.utils.logging import DXA_LOGGER

from .base import IPVConfig, IPVExecutionError


class IPVExecutor(ABC, Loggable):
    """
    Base IPV executor that implements the standard IPV control loop.

    This class provides the core IPV pattern implementation:
    1. INFER: Liberal input acceptance and context collection
    2. PROCESS: Generous transformation and execution
    3. VALIDATE: Conservative output guarantee

    Subclasses implement the specific logic for each phase.
    """

    def __init__(self):
        """Initialize the IPV executor."""
        super().__init__()
        self._debug_mode = False
        self._execution_history: list[dict[str, Any]] = []

    def execute(self, intent: str, context: Any = None, **kwargs) -> Any:
        """
        Execute the IPV pipeline for the given intent.

        Args:
            intent: What the user wants to accomplish
            context: Execution context (e.g., SandboxContext for Dana)
            **kwargs: Additional arguments (data, options, etc.)

        Returns:
            The validated result of the intelligent operation

        Raises:
            IPVExecutionError: If the pipeline fails
        """
        # Extract configuration from kwargs
        config = kwargs.pop("config", None) or kwargs.pop("options", None) or {}
        if isinstance(config, dict):
            config = IPVConfig.from_dict(config)
        elif not isinstance(config, IPVConfig):
            config = IPVConfig()

        if config.debug_mode:
            self.set_debug_mode(True)

        start_time = time.time()
        execution_id = f"ipv_{int(start_time * 1000)}"

        self.debug(f"Starting IPV execution {execution_id}")

        # Track execution for debugging and learning
        execution_record = {
            "execution_id": execution_id,
            "start_time": start_time,
            "intent": intent,
            "config": config.to_dict(),
            "phases": {},
            "iterations": 0,
            "success": False,
            "final_result": None,
            "total_time": 0,
            "errors": [],
        }

        try:
            # Execute with potential iterations
            final_result = self._execute_with_iterations(intent, context, config, execution_record, **kwargs)

            execution_record["success"] = True
            execution_record["final_result"] = final_result
            execution_record["total_time"] = time.time() - start_time

            self._execution_history.append(execution_record)

            self.debug(f"IPV execution {execution_id} completed successfully in {execution_record['total_time']:.3f}s")

            return final_result

        except Exception as e:
            execution_record["success"] = False
            execution_record["total_time"] = time.time() - start_time
            execution_record["errors"].append(str(e))

            self._execution_history.append(execution_record)

            self.debug(f"IPV execution {execution_id} failed: {e}")

            raise IPVExecutionError(f"IPV execution failed: {e}", original_error=e)

    def _execute_with_iterations(self, intent: str, context: Any, config: IPVConfig, execution_record: dict[str, Any], **kwargs) -> Any:
        """Execute IPV pipeline with iteration support."""
        max_iterations = config.max_iterations
        last_error = None

        for iteration in range(max_iterations):
            execution_record["iterations"] = iteration + 1

            self.debug(f"Starting iteration {iteration + 1}/{max_iterations}")

            try:
                # Execute single iteration
                result = self._execute_single_iteration(intent, context, config, iteration, execution_record, **kwargs)

                self.debug(f"Iteration {iteration + 1} succeeded")
                return result

            except Exception as e:
                last_error = e
                self.debug(f"Iteration {iteration + 1} failed: {e}")

                # For now, don't retry - just fail
                # In a full implementation, we would analyze the error
                # and potentially modify the approach for the next iteration
                break

        # All iterations failed
        error_msg = f"IPV execution failed after {execution_record['iterations']} iterations"
        if last_error:
            error_msg += f": {last_error}"
        raise IPVExecutionError(error_msg, original_error=last_error)

    def _execute_single_iteration(
        self, intent: str, context: Any, config: IPVConfig, iteration: int, execution_record: dict[str, Any], **kwargs
    ) -> Any:
        """Execute a single iteration of the IPV pipeline."""
        iteration_record = {"iteration": iteration, "phases": {}, "success": False, "error": None}

        try:
            # Phase 1: INFER
            self.debug("Executing INFER phase")
            start_time = time.time()
            infer_result = self.infer_phase(intent, context, **kwargs)
            infer_time = time.time() - start_time

            iteration_record["phases"]["infer"] = {
                "success": True,
                "execution_time": infer_time,
                "error": None,
            }

            # Phase 2: PROCESS
            self.debug("Executing PROCESS phase")
            if 'context' not in kwargs:
                kwargs['context'] = context
            start_time = time.time()
            process_result = self.process_phase(intent, infer_result, **kwargs)
            process_time = time.time() - start_time

            iteration_record["phases"]["process"] = {
                "success": True,
                "execution_time": process_time,
                "error": None,
            }

            # Phase 3: VALIDATE
            self.debug("Executing VALIDATE phase")
            start_time = time.time()
            validate_result = self.validate_phase(process_result, infer_result, **kwargs)
            validate_time = time.time() - start_time

            iteration_record["phases"]["validate"] = {
                "success": True,
                "execution_time": validate_time,
                "error": None,
            }

            # All phases succeeded
            iteration_record["success"] = True
            execution_record["phases"][f"iteration_{iteration}"] = iteration_record

            return validate_result

        except Exception as e:
            iteration_record["success"] = False
            iteration_record["error"] = str(e)
            execution_record["phases"][f"iteration_{iteration}"] = iteration_record
            raise

    @abstractmethod
    def infer_phase(self, intent: str, context: Any, **kwargs) -> dict[str, Any]:
        """
        INFER phase: Understand what the operation needs.

        Args:
            intent: What the user wants to accomplish
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Enhanced context dictionary with inferred requirements
        """
        pass

    @abstractmethod
    def process_phase(self, intent: str, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """
        PROCESS phase: Execute the operation with strategy.

        Args:
            intent: What the user wants to accomplish
            enhanced_context: Output from the INFER phase
            **kwargs: Additional arguments

        Returns:
            Raw result from the processing operation
        """
        pass

    @abstractmethod
    def validate_phase(self, result: Any, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """
        VALIDATE phase: Ensure output meets requirements.

        Args:
            result: Output from the PROCESS phase
            enhanced_context: Output from the INFER phase
            **kwargs: Additional arguments

        Returns:
            Validated, cleaned result that meets requirements
        """
        pass

    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug mode."""
        self._debug_mode = enabled

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get the execution history for debugging and analysis."""
        return self._execution_history.copy()

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics from execution history."""
        if not self._execution_history:
            return {"total_executions": 0}

        total_executions = len(self._execution_history)
        successful_executions = sum(1 for record in self._execution_history if record["success"])
        total_time = sum(record["total_time"] for record in self._execution_history)
        avg_time = total_time / total_executions if total_executions > 0 else 0

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "total_time": total_time,
            "average_time": avg_time,
        }


class IPVReason(IPVExecutor):
    """
    IPV executor specialized for prompt optimization and LLM interactions.

    This executor implements the IPV pattern specifically for AI prompt
    optimization, handling type-driven optimization, domain detection,
    and LLM response validation.
    """

    def __init__(self):
        """Initialize the IPVReason executor."""
        super().__init__()

    def infer_phase(self, intent: str, context: Any, **kwargs) -> dict[str, Any]:
        """
        INFER phase for prompt optimization.

        Analyzes the intent and context to determine:
        - Domain and task type (delegated to LLM for intelligent analysis)
        - Expected output type from assignment context
        - Prompt optimization strategy based on type hints
        - Code context from comments and surrounding code
        """
        self.debug(f"Starting INFER phase for prompt: {intent}")

        # Get expected type from context if available
        expected_type = None
        try:
            if context and hasattr(context, "get_assignment_target_type"):
                expected_type = context.get_assignment_target_type()
        except Exception as e:
            self.debug(f"Could not extract assignment target type: {e}")

        # Extract code context from comments and surrounding code
        variable_name = kwargs.get("variable_name")
        code_context = None
        optimization_hints = []
        context_analyzer = None  # Initialize here to ensure it's in scope

        try:
            from opendxa.dana.ipv.context_analyzer import CodeContextAnalyzer

            context_analyzer = CodeContextAnalyzer()
            code_context = context_analyzer.analyze_context(context, variable_name)

            if code_context and code_context.has_context():
                self.debug(f"Code context extracted: {code_context.get_context_summary()}")
            else:
                self.debug("No additional code context found")

        except ImportError:
            self.debug("CodeContextAnalyzer not available")
        except Exception as e:
            self.debug(f"Error extracting code context: {e}")

        # Get optimization hints from reliable type information
        try:
            if context_analyzer and code_context:
                optimization_hints = context_analyzer.get_optimization_hints_from_types(expected_type, code_context)
        except Exception as e:
            self.debug(f"Error getting optimization hints: {e}")

         # Get resources from context and filter by included_resources
        try:
            resources = context.get_resources(kwargs.get("llm_options", {}).get("resources", None)) if context is not None else {}
        except Exception as e:
            self.warning(f"Error getting resources from context: {e}")
            resources = {}

        # Build enhanced context with raw information
        # The LLM will handle domain/intent detection in the PROCESS phase
        enhanced_context = {
            "operation_type": "llm_prompt",
            "original_intent": intent,
            "expected_type": expected_type,
            "code_context": code_context,
            "optimization_hints": optimization_hints,
            "use_llm_analysis": True,  # Flag to use LLM for context analysis
            "resources": resources,
        }

        self.debug(f"INFER phase completed: basic context with {len(optimization_hints)} type hints")
        return enhanced_context

    def process_phase(self, intent: str, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """
        PROCESS phase for prompt optimization using meta-prompting:
        1. Provide a simple initial example prompt (no CoT/confidence loop) as a starting point.
        2. Ask the LLM to design the best possible prompt for itself, simulate answering, self-evaluate, and iterate up to N times.
        3. Output is a JSON object with steps (each with designed_prompt, simulated_answer, reasoning, confidence, revision_plan), and final_prompt, final_answer, final_confidence.
        """
        self.debug("Starting PROCESS phase with LLM meta-prompting (self-prompting loop)")

        # Get LLM options and mocking settings from kwargs
        llm_options = kwargs.get("llm_options", {})
        use_mock = kwargs.get("use_mock")
        context = kwargs.get("context") if "context" in kwargs else None

        # Get code context and type information
        code_context = enhanced_context.get("code_context")
        expected_type = enhanced_context.get("expected_type")
        optimization_hints = enhanced_context.get("optimization_hints", [])
        resources = enhanced_context.get("resources", {})

        # Determine max steps (N)
        max_steps = llm_options.get("max_meta_steps") or llm_options.get("max_iterations") or kwargs.get("max_meta_steps") or 3

        # Build the initial example prompt (no CoT/confidence loop)
        prompt_sections = []
        prompt_sections.append(f"Request:\n{intent}")

        # Add Type hint section if present and valid
        type_name = None
        if expected_type and hasattr(expected_type, "__name__"):
            type_name = expected_type.__name__
            prompt_sections.append(f"Type hint:\n{type_name}")

        try:
            if resources:
                # NOTE : NEED HELP WITH PROMPTING SO PROCESS PHASE CAN PERFORM TOOL CALLS
                import json
                resource_dict_str = {}
                for resource_name, resource in resources.items():
                    resource_dict_str[resource_name] = resource.list_openai_functions()
                prompt_sections.append(f"Resources and tools:\n{json.dumps(resource_dict_str, indent=2)}")
        except Exception as e:
            self.warning(f"Error getting resources from context: {e}")

        # Add Code context section if present and non-empty
        context_lines = None
        current_line = None
        current_line_number = None
        if code_context and hasattr(code_context, "has_context") and code_context.has_context():
            # Use actual code lines if available
            if hasattr(code_context, "surrounding_code") and code_context.surrounding_code:
                if hasattr(code_context, "surrounding_code_line_numbers") and code_context.surrounding_code_line_numbers:
                    context_lines = "\n".join(
                        f"{ln}: {line}" for ln, line in zip(code_context.surrounding_code_line_numbers, code_context.surrounding_code, strict=False)
                    )
                else:
                    context_lines = "\n".join(code_context.surrounding_code)
            if hasattr(code_context, "get_current_line"):
                current_line = code_context.get_current_line()
            if hasattr(code_context, "get_current_line_number"):
                current_line_number = code_context.get_current_line_number()
        if context_lines:
            prompt_sections.append(f"Code context (surrounding lines):\n{context_lines}")
        if current_line:
            if current_line_number is not None:
                prompt_sections.append(
                    f"Current line being executed:\n{current_line_number}: {current_line}\n(This is the specific line of code currently being run. Use this to better understand the user's intent and context.)"
                )
            else:
                prompt_sections.append(
                    f"Current line being executed:\n{current_line}\n(This is the specific line of code currently being run. Use this to better understand the user's intent and context.)"
                )

        # The initial example prompt is just the basic context and request
        initial_example_prompt = "\n\n".join(prompt_sections)

        # Build the meta-prompt
        meta_prompt = f"""
You are an expert AI agent and prompt engineer. Your task is to design the best possible prompt for yourself to answer the user's request, given the code context and requirements.

Here is an initial example prompt you may use as a starting point:
---
{initial_example_prompt}
---

Your process:
1. Review the initial example prompt and the user's request/context.
2. Design a new or improved prompt for yourself to best answer the user's request.
3. Simulate answering the user's request using your new prompt.
4. Evaluate whether your simulated answer fully meets the user's intent and objective.
5. If not, revise your prompt and repeat the process.

Repeat this process up to {max_steps} times, or until you are 100% confident that your answer fully meets the user's intent.

At each step, output:
- The prompt you designed
- The simulated answer
- Your reasoning and confidence (0-100%) that the answer meets the user's intent
- If confidence < 100%, explain what is missing and how you will revise the prompt

At the end, output the best prompt, the final answer, and your confidence.

Format your output as JSON:
{{
  "steps": [
    {{
      "designed_prompt": "...",
      "simulated_answer": "...",
      "reasoning": "...",
      "confidence": ...,
      "revision_plan": "..."
    }},
    ...
  ],
  "final_prompt": "...",
  "final_answer": "...",
  "final_confidence": ...
}}
"""

        # Make the LLM call with the meta-prompt
        try:
            raw_result = self._execute_llm_call(meta_prompt, context, llm_options, use_mock)
        except Exception as e:
            self.debug(f"LLM call failed: {e}")
            # Fallback to simple response for robustness
            return {"final_answer": f"LLM Response to: {intent}", "final_confidence": 0, "steps": []}

        # Parse the JSON result
        import json

        parsed = None
        if isinstance(raw_result, dict):
            parsed = raw_result
        elif isinstance(raw_result, str):
            try:
                start = raw_result.find("{")
                end = raw_result.rfind("}") + 1
                if start != -1 and end != -1:
                    json_str = raw_result[start:end]
                    parsed = json.loads(json_str)
            except Exception as e:
                self.debug(f"Could not parse LLM JSON output: {e}")
        if not parsed:
            return {"final_answer": raw_result, "final_confidence": 0, "steps": []}

        self.debug(f"PROCESS phase completed with final_confidence: {parsed.get('final_confidence')}")
        return parsed

    def validate_phase(self, result: Any, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """
        VALIDATE phase for prompt optimization.

        Validates and cleans the LLM response to ensure it meets
        the expected type and quality requirements.
        """
        self.debug(f"Starting VALIDATE phase with result type: {type(result)}")

        expected_type = enhanced_context.get("expected_type")

        # If result is a dict with 'final_answer', extract it for validation/cleaning
        if isinstance(result, dict) and "final_answer" in result:
            answer = result["final_answer"]
            validated_result = self._validate_and_clean_result(answer, expected_type, enhanced_context)
            self.debug(f"VALIDATE phase completed with validated type: {type(validated_result)} (from final_answer)")
            return validated_result

        # Otherwise, apply type-specific validation and cleaning as before
        validated_result = self._validate_and_clean_result(result, expected_type, enhanced_context)
        self.debug(f"VALIDATE phase completed with validated type: {type(validated_result)}")
        return validated_result

    def _validate_and_clean_result(self, result: Any, expected_type: Any, enhanced_context: dict[str, Any]) -> Any:
        """Validate and clean the result based on expected type."""
        # This is a simplified validation - real implementation would use the validation.py module

        if expected_type == float:
            # Try to extract a float from the result
            if isinstance(result, str):
                import re

                # Look for decimal numbers first (more specific), but skip numbered list markers
                decimal_numbers = re.findall(r"(?<!\d\.)\d+\.\d+", result)
                if decimal_numbers:
                    return float(decimal_numbers[0])

                # Then look for any numbers (including integers), but skip list markers like "1.", "2.", etc.
                # Use negative lookbehind to avoid list markers and negative lookahead to avoid standalone periods
                numbers = re.findall(r"(?<!\d\.)\d+(?!\.\s)", result)
                if numbers:
                    return float(numbers[0])
            return 0.0

        elif expected_type == int:
            # Try to extract an integer from the result
            if isinstance(result, str):
                import re

                # Skip numbered list markers like "1.", "2.", etc. by using negative lookahead
                numbers = re.findall(r"\d+(?!\.\s)", result)
                if numbers:
                    return int(numbers[0])
            return 0

        elif expected_type == bool:
            # Try to extract a boolean from the result
            if isinstance(result, str):
                result_lower = result.lower()
                if any(word in result_lower for word in ["yes", "true", "approved", "positive"]):
                    return True
                elif any(word in result_lower for word in ["no", "false", "rejected", "negative"]):
                    return False
            return False

        elif expected_type == str:
            # Clean markdown and formatting from string results
            if isinstance(result, str):
                # Remove common markdown formatting
                import re

                cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", result)  # Remove **bold**
                cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)  # Remove *italic*
                cleaned = re.sub(r"`(.*?)`", r"\1", cleaned)  # Remove `code`
                return cleaned.strip()
            return str(result)

        elif expected_type == dict:
            # Try to extract or parse a dictionary from the result
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                import json
                import re

                # Try to parse as JSON first
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    pass

                # Try to extract key-value pairs from natural language
                # Look for patterns like "name=John, age=30" or "key: value, key2: value2"
                try:
                    parsed_dict = {}
                    # Match patterns like "key=value" or "key: value"
                    pairs = re.findall(r"(\w+)[:=]\s*([^,]+)", result)
                    for key, value in pairs:
                        # Try to parse value as number or boolean
                        value = value.strip()
                        if value.lower() in ["true", "yes"]:
                            parsed_dict[key] = True
                        elif value.lower() in ["false", "no"]:
                            parsed_dict[key] = False
                        elif value.isdigit():
                            parsed_dict[key] = int(value)
                        elif "." in value and value.replace(".", "").isdigit():
                            parsed_dict[key] = float(value)
                        else:
                            parsed_dict[key] = value

                    if parsed_dict:
                        return parsed_dict
                except Exception:
                    pass

                # Fallback: return a dict with the result as a message
                return {"result": result, "type": "text_response"}

            # Default empty dict
            return {}

        elif expected_type == list:
            # Try to extract or parse a list from the result
            if isinstance(result, list):
                return result
            elif isinstance(result, str):
                import json
                import re

                # Try to parse as JSON array first
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    pass

                # Try to extract comma-separated values
                try:
                    # Look for patterns like "red, blue, green" or "1, 2, 3, 4"
                    if "," in result:
                        items = [item.strip() for item in result.split(",")]
                        # Try to convert to appropriate types
                        converted_items = []
                        for item in items:
                            if item.isdigit():
                                converted_items.append(int(item))
                            elif "." in item and item.replace(".", "").isdigit():
                                converted_items.append(float(item))
                            elif item.lower() in ["true", "yes"]:
                                converted_items.append(True)
                            elif item.lower() in ["false", "no"]:
                                converted_items.append(False)
                            else:
                                converted_items.append(item)
                        return converted_items

                    # Look for bullet points or numbered lists
                    lines = result.split("\n")
                    list_items = []
                    for line in lines:
                        line = line.strip()
                        # Match bullet points (•, *, -, 1., 2., etc.)
                        if re.match(r"^[•*-]|\d+\.", line):
                            item = re.sub(r"^[•*-]|\d+\.", "", line).strip()
                            if item:
                                list_items.append(item)

                    if list_items:
                        return list_items
                except Exception:
                    pass

                # Fallback: return single-item list
                return [result]

            # Default empty list
            return []

        # For other types or no expected type, return as-is
        return result

    def _execute_llm_call(self, prompt: str, context: Any, options: dict[str, Any], use_mock: bool | None = None) -> Any:
        """Execute LLM call using the same infrastructure as original reason_function."""
        import json
        import os

        from opendxa.common.resource.llm_resource import LLMResource
        from opendxa.common.types import BaseRequest
        from opendxa.dana.common.exceptions import SandboxError

        logger = DXA_LOGGER.getLogger("opendxa.dana.reason.llm")

        # Check if we should use mock responses
        should_mock = use_mock if use_mock is not None else os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"

        # Get LLM resource from context
        if hasattr(context, "llm_resource") and context.llm_resource:
            llm_resource = context.llm_resource
        else:
            # Try to get from system.llm_resource
            try:
                llm_resource = context.get("system.llm_resource") if context else None
                if not llm_resource:
                    llm_resource = LLMResource()
            except Exception:
                llm_resource = LLMResource()

        # Apply mocking if needed
        if should_mock:
            self.debug(f"Using mock LLM for enhanced prompt: {prompt[:50]}...")
            llm_resource = llm_resource.with_mock_llm_call(True)

        # Prepare system message
        system_message = options.get("system_message", "You are a helpful AI assistant. Respond concisely and accurately.")

        # Set up the messages
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]

        # Log the LLM prompt using DXA_LOGGER
        logger.debug("=" * 80)
        logger.debug("LLM CONVERSATION:")
        logger.debug("SYSTEM MESSAGE:\n%s", system_message)
        logger.debug("USER PROMPT:\n%s", prompt)
        logger.debug("-" * 40)

        # Log the conversation if debug mode is enabled
        if self._debug_mode:
            self.debug("=" * 80)
            self.debug("LLM CONVERSATION:")
            self.debug("=" * 80)
            self.debug(f"SYSTEM MESSAGE:\n{system_message}")
            self.debug("-" * 40)
            self.debug(f"USER PROMPT:\n{prompt}")
            self.debug("-" * 40)

        # Prepare LLM parameters and execute the query
        request_params = {
            "messages": messages,
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", None),
        }

        # Get resources from context and filter by included_resources
        try:
            resources = context.get_resources(options.get("resources", None)) if context is not None else {}
        except Exception as e:
            self.warning(f"Error getting resources from context: {e}")
            resources = {}

        # Set query strategy and max iterations to iterative and 5 respectively to ultilize tools calls
        previous_query_strategy = llm_resource._query_strategy
        previous_query_max_iterations = llm_resource._query_max_iterations
        if resources:
            request_params["available_resources"] = resources
            llm_resource._query_strategy = QueryStrategy.ITERATIVE
            llm_resource._query_max_iterations = options.get("max_iterations", 5)

        request = BaseRequest(arguments=request_params)
        response = llm_resource.query_sync(request)

        # Reset query strategy and max iterations
        llm_resource._query_strategy = previous_query_strategy
        llm_resource._query_max_iterations = previous_query_max_iterations

        if not response.success:
            raise SandboxError(f"LLM reasoning failed: {response.error}")

        # Process the response (similar to original reason_function)
        result = response.content

        # Extract just the text content from the response
        if isinstance(result, dict):
            # Handle different LLM response structures
            if "choices" in result and result["choices"] and isinstance(result["choices"], list):
                # OpenAI/Anthropic style response
                first_choice = result["choices"][0]
                if hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                    result = first_choice.message.content
                elif isinstance(first_choice, dict):
                    if "message" in first_choice:
                        message = first_choice["message"]
                        if isinstance(message, dict) and "content" in message:
                            result = message["content"]
                        elif hasattr(message, "content"):
                            result = message.content
                    elif "text" in first_choice:
                        result = first_choice["text"]
            elif "content" in result:
                result = result["content"]
            else:
                # For mock responses that don't follow standard format,
                # use a default mock response
                self.debug(f"Unexpected response format: {result}")
                result = "Mock LLM response for enhanced prompt"

        # If result is still a complex object, convert to string
        if not isinstance(result, (str, int, float, bool, list, dict)) and hasattr(result, "__str__"):
            result = str(result)

        # Log the LLM response using DXA_LOGGER
        logger.debug("LLM RESPONSE:\n%s", result)
        logger.debug("=" * 80)

        # Log the LLM response if debug mode is enabled
        if self._debug_mode:
            self.debug(f"LLM RESPONSE:\n{result}")
            self.debug("=" * 80)

        # Handle format conversion if needed
        format_type = options.get("format", "text")
        if format_type == "json" and isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                self.debug(f"Could not parse LLM response as JSON: {result[:100]}")

        return result


class IPVDataProcessor(IPVExecutor):
    """
    IPV executor for data analysis and processing operations.

    This executor implements the IPV pattern for intelligent data
    processing, analysis, and transformation tasks.
    """

    def infer_phase(self, intent: str, context: Any, **kwargs) -> dict[str, Any]:
        """INFER phase for data processing."""
        data = kwargs.get("data")

        return {
            "operation_type": "data_processing",
            "data_format": self._detect_data_format(data),
            "analysis_type": self._infer_analysis_type(intent),
            "data_size": len(data) if data is not None and hasattr(data, "__len__") else None,
            "quality_requirements": self._infer_quality_needs(intent),
        }

    def process_phase(self, intent: str, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """PROCESS phase for data processing."""
        # Placeholder for data processing logic
        data = kwargs.get("data")
        analysis_type = enhanced_context.get("analysis_type")

        # Simulate data processing
        return f"Processed data analysis ({analysis_type}): {data}"

    def validate_phase(self, result: Any, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """VALIDATE phase for data processing."""
        # Placeholder for data validation logic
        return result

    def _detect_data_format(self, data: Any) -> str:
        """Detect the format of the input data."""
        if isinstance(data, dict):
            return "dictionary"
        elif isinstance(data, list):
            return "list"
        elif isinstance(data, str):
            return "string"
        else:
            return "unknown"

    def _infer_analysis_type(self, intent: str) -> str:
        """Infer the type of analysis from the intent."""
        intent_lower = intent.lower()
        if "pattern" in intent_lower:
            return "pattern_analysis"
        elif "trend" in intent_lower:
            return "trend_analysis"
        elif "summary" in intent_lower:
            return "summary_analysis"
        else:
            return "general_analysis"

    def _infer_quality_needs(self, intent: str) -> dict[str, Any]:
        """Infer quality requirements from the intent."""
        return {"accuracy": "high", "completeness": "required", "consistency": "enforced"}


class IPVAPIIntegrator(IPVExecutor):
    """
    IPV executor for API calls and integrations.

    This executor implements the IPV pattern for intelligent API
    integration, handling endpoint discovery, authentication,
    and response processing.
    """

    def infer_phase(self, intent: str, context: Any, **kwargs) -> dict[str, Any]:
        """INFER phase for API integration."""
        return {
            "operation_type": "api_integration",
            "endpoint": self._infer_endpoint(intent, context),
            "auth_method": self._detect_auth_requirements(context),
            "retry_strategy": self._determine_retry_needs(intent),
            "response_format": "json",
        }

    def process_phase(self, intent: str, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """PROCESS phase for API integration."""
        # Placeholder for API call logic
        endpoint = enhanced_context.get("endpoint")

        # Simulate API call
        return f'API response from {endpoint}: {{"status": "success", "data": "..."}}'

    def validate_phase(self, result: Any, enhanced_context: dict[str, Any], **kwargs) -> Any:
        """VALIDATE phase for API integration."""
        # Placeholder for API response validation
        return result

    def _infer_endpoint(self, intent: str, context: Any) -> str:
        """Infer the API endpoint from the intent."""
        if "user" in intent.lower():
            return "/api/users"
        elif "data" in intent.lower():
            return "/api/data"
        else:
            return "/api/general"

    def _detect_auth_requirements(self, context: Any) -> str:
        """Detect authentication requirements."""
        return "bearer_token"  # Placeholder

    def _determine_retry_needs(self, intent: str) -> dict[str, Any]:
        """Determine retry strategy needs."""
        return {"max_retries": 3, "backoff_strategy": "exponential", "retry_on": ["timeout", "5xx_errors"]}
