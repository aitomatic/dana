"""
Concrete implementations of IPV phases.

This module provides the standard implementations of the three IPV phases:
- InferPhase: Liberal input acceptance and context collection
- ProcessPhase: Generous transformation and execution
- ValidatePhase: Conservative output guarantee
"""

import time
from typing import Any

from .base import IPVConfig, IPVExecutionError, IPVPhase, IPVPhaseType, IPVResult, IPVValidationError


class InferPhase(IPVPhase):
    """
    INFER phase: Liberal input acceptance and context collection.

    This phase is responsible for:
    - Accepting minimal, ambiguous, or messy input
    - Applying intelligent inference to understand intent
    - Collecting relevant context automatically
    - Determining optimal processing strategy
    """

    def __init__(self):
        super().__init__(IPVPhaseType.INFER)

    def execute(self, input_data: Any, context: Any, config: IPVConfig) -> IPVResult:
        """
        Execute the INFER phase.

        Args:
            input_data: The original user input (e.g., prompt)
            context: Execution context (e.g., SandboxContext)
            config: IPV configuration

        Returns:
            IPVResult containing enhanced context and strategy
        """
        start_time = time.time()

        try:
            self.validate_config(config)
            phase_config = self.get_phase_config(config)

            self._log_debug(f"Starting INFER phase with input: {input_data}")

            # Enhanced context will be built up through inference
            enhanced_context = {
                "original_input": input_data,
                "config": config.to_dict(),
                "phase_config": phase_config,
                "inferred_strategy": {},
                "collected_context": {},
                "metadata": {},
            }

            # Step 1: Analyze input to understand intent
            enhanced_context["inferred_strategy"] = self._infer_strategy(input_data, context, config)

            # Step 2: Collect relevant context
            enhanced_context["collected_context"] = self._collect_context(input_data, context, config)

            # Step 3: Determine processing approach
            enhanced_context["processing_approach"] = self._determine_processing_approach(input_data, context, config, enhanced_context)

            execution_time = time.time() - start_time
            self._log_debug(f"INFER phase completed in {execution_time:.3f}s")

            return IPVResult(
                success=True,
                result=enhanced_context,
                execution_time=execution_time,
                metadata={"phase": "infer", "strategy": enhanced_context["inferred_strategy"]},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._log_debug(f"INFER phase failed: {e}")

            return IPVResult(
                success=False,
                result=None,
                error=IPVExecutionError(f"INFER phase failed: {e}", IPVPhaseType.INFER, e),
                execution_time=execution_time,
            )

    def _infer_strategy(self, input_data: Any, context: Any, config: IPVConfig) -> dict[str, Any]:
        """Infer the optimal strategy based on input and context."""
        strategy = {
            "domain": "general",
            "task_type": "unknown",
            "complexity": "medium",
            "expected_output_type": "string",
            "optimization_focus": [],
        }

        # Basic strategy inference based on input
        if isinstance(input_data, str):
            input_lower = input_data.lower()

            # Domain detection
            if any(word in input_lower for word in ["price", "cost", "money", "dollar", "$"]):
                strategy["domain"] = "financial"
                strategy["optimization_focus"].append("precision")
            elif any(word in input_lower for word in ["analyze", "analysis", "data"]):
                strategy["domain"] = "analytical"
                strategy["task_type"] = "analysis"
            elif any(word in input_lower for word in ["create", "write", "generate"]):
                strategy["task_type"] = "generation"
                strategy["optimization_focus"].append("creativity")
            elif any(word in input_lower for word in ["extract", "find", "get"]):
                strategy["task_type"] = "extraction"
                strategy["optimization_focus"].append("precision")

        # Adjust strategy based on config
        if config.precision.value in ["exact", "specific"]:
            strategy["optimization_focus"].append("precision")
        if config.reliability.value in ["high", "maximum"]:
            strategy["optimization_focus"].append("consistency")
        if config.safety.value in ["high", "maximum"]:
            strategy["optimization_focus"].append("safety")

        return strategy

    def _collect_context(self, input_data: Any, context: Any, config: IPVConfig) -> dict[str, Any]:
        """Collect relevant context for optimization."""
        collected = {"execution_context": {}, "user_context": {}, "code_context": {}, "domain_context": {}}

        # Collect execution context
        collected["execution_context"] = {"timestamp": time.time(), "config_level": config.context.value, "debug_mode": config.debug_mode}

        # If we have a Dana SandboxContext, collect from it
        if hasattr(context, "state"):
            collected["code_context"]["has_state"] = True
            # We'll expand this when we integrate with Dana's context system
        else:
            collected["code_context"]["has_state"] = False

        return collected

    def _determine_processing_approach(
        self, input_data: Any, context: Any, config: IPVConfig, enhanced_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Determine the best processing approach based on inferred strategy."""
        strategy = enhanced_context["inferred_strategy"]

        approach = {
            "method": "standard",
            "iterations": config.max_iterations,
            "validation_strict": config.reliability.value in ["high", "maximum"],
            "error_handling": "graceful",
            "fallback_strategy": "conservative",
        }

        # Adjust approach based on strategy
        if strategy["task_type"] == "extraction":
            approach["method"] = "extraction_focused"
            approach["validation_strict"] = True
        elif strategy["task_type"] == "generation":
            approach["method"] = "generation_focused"
            approach["validation_strict"] = False
        elif strategy["domain"] == "financial":
            approach["validation_strict"] = True
            approach["error_handling"] = "strict"

        return approach


class ProcessPhase(IPVPhase):
    """
    PROCESS phase: Generous transformation and execution.

    This phase is responsible for:
    - Handling multiple input formats liberally
    - Applying adaptive processing strategies
    - Retrying and iterating when needed
    - Extracting meaning from complex or inconsistent data
    """

    def __init__(self):
        super().__init__(IPVPhaseType.PROCESS)

    def execute(self, input_data: Any, context: Any, config: IPVConfig) -> IPVResult:
        """
        Execute the PROCESS phase.

        Args:
            input_data: Enhanced context from INFER phase
            context: Execution context
            config: IPV configuration

        Returns:
            IPVResult containing processed output
        """
        start_time = time.time()

        try:
            self.validate_config(config)
            phase_config = self.get_phase_config(config)

            # input_data should be the enhanced context from INFER phase
            if not isinstance(input_data, dict) or "original_input" not in input_data:
                raise IPVExecutionError("PROCESS phase expects enhanced context from INFER phase")

            original_input = input_data["original_input"]
            strategy = input_data.get("inferred_strategy", {})
            approach = input_data.get("processing_approach", {})

            self._log_debug(f"Starting PROCESS phase with strategy: {strategy}")

            # Execute processing based on approach
            result = self._execute_processing(original_input, input_data, context, config, approach)

            execution_time = time.time() - start_time
            self._log_debug(f"PROCESS phase completed in {execution_time:.3f}s")

            return IPVResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"phase": "process", "strategy": strategy, "approach": approach},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._log_debug(f"PROCESS phase failed: {e}")

            return IPVResult(
                success=False,
                result=None,
                error=IPVExecutionError(f"PROCESS phase failed: {e}", IPVPhaseType.PROCESS, e),
                execution_time=execution_time,
            )

    def _execute_processing(
        self, original_input: Any, enhanced_context: dict[str, Any], context: Any, config: IPVConfig, approach: dict[str, Any]
    ) -> Any:
        """Execute the actual processing logic."""

        # For now, this is a placeholder that simulates processing
        # In the real implementation, this would:
        # 1. Generate enhanced prompts
        # 2. Call LLM APIs
        # 3. Handle retries and iterations
        # 4. Parse and transform responses

        strategy = enhanced_context.get("inferred_strategy", {})

        # Simulate different processing based on strategy
        if strategy.get("task_type") == "extraction":
            # Simulate extraction processing
            result = f"Extracted result from: {original_input}"
        elif strategy.get("task_type") == "generation":
            # Simulate generation processing
            result = f"Generated content based on: {original_input}"
        elif strategy.get("task_type") == "analysis":
            # Simulate analysis processing
            result = {"analysis": f"Analysis of: {original_input}", "confidence": 0.85}
        else:
            # Default processing
            result = f"Processed: {original_input}"

        return result


class ValidatePhase(IPVPhase):
    """
    VALIDATE phase: Conservative output guarantee.

    This phase is responsible for:
    - Applying strict validation to ensure quality
    - Cleaning and normalizing outputs
    - Guaranteeing type compliance and format consistency
    - Providing reliable, deterministic results
    """

    def __init__(self):
        super().__init__(IPVPhaseType.VALIDATE)

    def execute(self, input_data: Any, context: Any, config: IPVConfig) -> IPVResult:
        """
        Execute the VALIDATE phase.

        Args:
            input_data: Raw result from PROCESS phase
            context: Execution context (should include enhanced context)
            config: IPV configuration

        Returns:
            IPVResult containing validated and cleaned output
        """
        start_time = time.time()

        try:
            self.validate_config(config)
            phase_config = self.get_phase_config(config)

            self._log_debug(f"Starting VALIDATE phase with input: {input_data}")

            # Validate and clean the result
            validated_result = self._validate_and_clean(input_data, context, config)

            execution_time = time.time() - start_time
            self._log_debug(f"VALIDATE phase completed in {execution_time:.3f}s")

            return IPVResult(
                success=True,
                result=validated_result,
                execution_time=execution_time,
                metadata={"phase": "validate", "validation_applied": True},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._log_debug(f"VALIDATE phase failed: {e}")

            return IPVResult(
                success=False,
                result=None,
                error=IPVValidationError(f"VALIDATE phase failed: {e}", IPVPhaseType.VALIDATE, e),
                execution_time=execution_time,
            )

    def _validate_and_clean(self, result: Any, context: Any, config: IPVConfig) -> Any:
        """Validate and clean the result according to configuration."""

        # Basic validation and cleaning
        if isinstance(result, str):
            # Clean string results
            cleaned = result.strip()

            # Remove common LLM artifacts if structure is strict
            if config.structure.value == "strict":
                # Remove markdown formatting
                cleaned = self._remove_markdown(cleaned)

            return cleaned

        elif isinstance(result, dict):
            # Validate dict structure
            if config.structure.value in ["strict", "formatted"]:
                # Ensure dict has expected structure
                return self._validate_dict_structure(result, config)
            return result

        else:
            # For other types, return as-is for now
            return result

    def _remove_markdown(self, text: str) -> str:
        """Remove common markdown formatting from text."""
        import re

        # Remove bold/italic markers
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*

        # Remove bullet points
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple newlines
        text = text.strip()

        return text

    def _validate_dict_structure(self, data: dict, config: IPVConfig) -> dict:
        """Validate and clean dictionary structure."""
        # For now, just return the dict
        # In a full implementation, this would validate against schemas
        return data
