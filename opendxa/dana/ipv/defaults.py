"""
Default IPV implementations.

This module provides default implementations of IPV phases that can be used
out-of-the-box or as base classes for custom implementations.
"""

from typing import Any, Dict

from .base import IPVConfig
from .phases import InferPhase, ProcessPhase, ValidatePhase


class DefaultInferPhase(InferPhase):
    """
    Default implementation of the INFER phase.

    Provides basic context collection and strategy inference suitable
    for most use cases.
    """

    def __init__(self):
        super().__init__()

    def _infer_strategy(self, input_data: Any, context: Any, config: IPVConfig) -> Dict[str, Any]:
        """Enhanced strategy inference with more sophisticated logic."""
        strategy = super()._infer_strategy(input_data, context, config)

        # Add more sophisticated domain detection
        if isinstance(input_data, str):
            input_lower = input_data.lower()

            # Enhanced financial domain detection
            financial_keywords = [
                "price",
                "cost",
                "money",
                "dollar",
                "$",
                "€",
                "£",
                "¥",
                "revenue",
                "profit",
                "loss",
                "budget",
                "expense",
                "income",
                "investment",
                "roi",
                "financial",
                "accounting",
                "tax",
            ]
            if any(word in input_lower for word in financial_keywords):
                strategy["domain"] = "financial"
                strategy["safety_requirements"] = "high"
                strategy["precision_requirements"] = "exact"

            # Medical domain detection
            medical_keywords = [
                "symptom",
                "diagnosis",
                "treatment",
                "medicine",
                "drug",
                "patient",
                "doctor",
                "hospital",
                "medical",
                "health",
                "disease",
                "condition",
                "therapy",
            ]
            if any(word in input_lower for word in medical_keywords):
                strategy["domain"] = "medical"
                strategy["safety_requirements"] = "maximum"
                strategy["precision_requirements"] = "exact"

            # Legal domain detection
            legal_keywords = [
                "law",
                "legal",
                "contract",
                "agreement",
                "court",
                "judge",
                "attorney",
                "lawyer",
                "regulation",
                "compliance",
                "liability",
            ]
            if any(word in input_lower for word in legal_keywords):
                strategy["domain"] = "legal"
                strategy["safety_requirements"] = "maximum"
                strategy["precision_requirements"] = "exact"

            # Creative domain detection
            creative_keywords = [
                "story",
                "creative",
                "write",
                "poem",
                "novel",
                "character",
                "plot",
                "narrative",
                "fiction",
                "imagine",
                "brainstorm",
            ]
            if any(word in input_lower for word in creative_keywords):
                strategy["domain"] = "creative"
                strategy["safety_requirements"] = "low"
                strategy["precision_requirements"] = "loose"
                strategy["creativity_encouraged"] = True

        return strategy

    def _collect_context(self, input_data: Any, context: Any, config: IPVConfig) -> Dict[str, Any]:
        """Enhanced context collection with more comprehensive gathering."""
        collected = super()._collect_context(input_data, context, config)

        # Enhanced execution context
        collected["execution_context"].update(
            {
                "input_type": type(input_data).__name__,
                "input_length": len(str(input_data)) if input_data else 0,
                "config_reliability": config.reliability.value,
                "config_precision": config.precision.value,
                "config_safety": config.safety.value,
            }
        )

        # Try to collect more context if available
        if hasattr(context, "__dict__"):
            # Generic context collection for any object with attributes
            context_attrs = {}
            for attr_name in dir(context):
                if not attr_name.startswith("_"):
                    try:
                        attr_value = getattr(context, attr_name)
                        if not callable(attr_value):
                            context_attrs[attr_name] = str(attr_value)[:100]  # Limit length
                    except:
                        pass  # Skip attributes that can't be accessed

            collected["code_context"]["available_attributes"] = list(context_attrs.keys())

        return collected


class DefaultProcessPhase(ProcessPhase):
    """
    Default implementation of the PROCESS phase.

    Provides basic processing logic that can handle common scenarios
    and serves as a foundation for more specialized implementations.
    """

    def __init__(self):
        super().__init__()

    def _execute_processing(
        self, original_input: Any, enhanced_context: Dict[str, Any], context: Any, config: IPVConfig, approach: Dict[str, Any]
    ) -> Any:
        """Enhanced processing with more sophisticated logic."""

        strategy = enhanced_context.get("inferred_strategy", {})
        domain = strategy.get("domain", "general")
        task_type = strategy.get("task_type", "unknown")

        # Domain-specific processing
        if domain == "financial":
            return self._process_financial(original_input, enhanced_context, config)
        elif domain == "medical":
            return self._process_medical(original_input, enhanced_context, config)
        elif domain == "creative":
            return self._process_creative(original_input, enhanced_context, config)
        elif task_type == "extraction":
            return self._process_extraction(original_input, enhanced_context, config)
        elif task_type == "analysis":
            return self._process_analysis(original_input, enhanced_context, config)
        else:
            return self._process_general(original_input, enhanced_context, config)

    def _process_financial(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process financial-domain requests with high precision."""
        # Simulate financial processing with high precision requirements
        if isinstance(input_data, str) and any(word in input_data.lower() for word in ["price", "cost", "$"]):
            # Simulate extracting a price
            import re

            price_match = re.search(r"\$?(\d+\.?\d*)", str(input_data))
            if price_match:
                return float(price_match.group(1))
            else:
                return 0.0  # Conservative fallback

        return f"Financial analysis: {input_data}"

    def _process_medical(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process medical-domain requests with maximum safety."""
        # Medical processing requires maximum safety
        return {
            "response": f"Medical information regarding: {input_data}",
            "disclaimer": "This is not medical advice. Consult a healthcare professional.",
            "safety_level": "maximum",
        }

    def _process_creative(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process creative requests with flexibility."""
        # Creative processing allows more variation
        return f"Creative response to: {input_data} (with creative variation)"

    def _process_extraction(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process extraction requests with precision focus."""
        # Extraction processing focuses on precision
        return f"Extracted: {input_data}"

    def _process_analysis(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process analysis requests with structured output."""
        # Analysis processing returns structured data
        return {"input": str(input_data), "analysis": f"Analysis of {input_data}", "confidence": 0.85, "methodology": "default_analysis"}

    def _process_general(self, input_data: Any, context: Dict[str, Any], config: IPVConfig) -> Any:
        """Process general requests with balanced approach."""
        return f"Processed: {input_data}"


class DefaultValidatePhase(ValidatePhase):
    """
    Default implementation of the VALIDATE phase.

    Provides comprehensive validation and cleaning suitable for most use cases.
    """

    def __init__(self):
        super().__init__()

    def _validate_and_clean(self, result: Any, context: Any, config: IPVConfig) -> Any:
        """Enhanced validation and cleaning with more comprehensive logic."""

        # Get enhanced context if available
        enhanced_context = {}
        if isinstance(context, dict) and "inferred_strategy" in context:
            enhanced_context = context

        strategy = enhanced_context.get("inferred_strategy", {})
        domain = strategy.get("domain", "general")

        # Domain-specific validation
        if domain == "financial":
            return self._validate_financial(result, config)
        elif domain == "medical":
            return self._validate_medical(result, config)
        elif domain == "creative":
            return self._validate_creative(result, config)
        else:
            return self._validate_general(result, config)

    def _validate_financial(self, result: Any, config: IPVConfig) -> Any:
        """Validate financial results with strict requirements."""
        if isinstance(result, str):
            # Try to extract and validate numbers
            import re

            # Remove currency symbols and extract number
            cleaned = re.sub(r"[^\d\.]", "", result)
            try:
                return float(cleaned) if cleaned else 0.0
            except ValueError:
                return 0.0  # Conservative fallback

        elif isinstance(result, (int, float)):
            # Ensure proper formatting
            return float(result)

        return result

    def _validate_medical(self, result: Any, config: IPVConfig) -> Any:
        """Validate medical results with maximum safety."""
        if isinstance(result, dict):
            # Ensure medical disclaimer is present
            if "disclaimer" not in result:
                result["disclaimer"] = "This is not medical advice. Consult a healthcare professional."
            return result

        elif isinstance(result, str):
            # Add disclaimer to string responses
            return {"response": result, "disclaimer": "This is not medical advice. Consult a healthcare professional."}

        return result

    def _validate_creative(self, result: Any, config: IPVConfig) -> Any:
        """Validate creative results with minimal constraints."""
        # Creative content has minimal validation
        if isinstance(result, str):
            # Just clean up basic formatting
            return result.strip()

        return result

    def _validate_general(self, result: Any, config: IPVConfig) -> Any:
        """Validate general results with standard cleaning."""
        return super()._validate_and_clean(result, None, config)
