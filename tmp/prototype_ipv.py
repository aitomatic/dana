#!/usr/bin/env python3
"""
IPV (Infer-Process-Validate) Prompt Optimization Prototype

This prototype demonstrates the core IPV pattern for intelligent prompt optimization.
It shows how the system can automatically enhance prompts based on type annotations
and context, while providing progressive levels of control for users.
"""

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ReliabilityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class PrecisionLevel(Enum):
    LOOSE = "loose"
    GENERAL = "general"
    SPECIFIC = "specific"
    EXACT = "exact"


class SafetyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class StructureLevel(Enum):
    FREE = "free"
    ORGANIZED = "organized"
    FORMATTED = "formatted"
    STRICT = "strict"


class ContextLevel(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    MAXIMUM = "maximum"


@dataclass
class IPVConfig:
    """Configuration for each IPV phase"""

    strategy: Optional[str] = None
    context_collection: Optional[str] = None
    max_iterations: int = 3
    quality_threshold: str = "medium"
    error_handling: str = "liberal"
    type_enforcement: str = "strict"


@dataclass
class SandboxContext:
    """Simplified Dana sandbox context"""

    function_name: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    user_location: str = "San Francisco, CA"
    user_timezone: str = "PST"
    current_time: Optional[str] = None
    domain: Optional[str] = None

    def __post_init__(self):
        if self.current_time is None:
            self.current_time = time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class EnhancedContext:
    """Context enhanced by the INFER phase"""

    original_prompt: str
    expected_type: type
    domain: str
    reliability: ReliabilityLevel
    precision: PrecisionLevel
    safety: SafetyLevel
    structure: StructureLevel
    context_level: ContextLevel
    validation_rules: List[str]
    format_requirements: List[str]
    examples: List[str]
    enhanced_prompt: str


class MockLLM:
    """Mock LLM for demonstration - returns realistic but predictable responses"""

    def __init__(self):
        self.call_count = 0

    def call(self, prompt: str) -> str:
        self.call_count += 1

        # Simulate different response formats based on prompt content
        if "price" in prompt.lower():
            if "only numeric" in prompt.lower() or "decimal" in prompt.lower():
                return "29.99"
            else:
                return "The total price is $29.99 (including tax and shipping)"

        elif "email" in prompt.lower():
            if "format" in prompt.lower() or "valid" in prompt.lower():
                return "john.doe@example.com"
            else:
                return "You can reach out to john.doe@example.com for more information."

        elif "urgent" in prompt.lower():
            if "true/false" in prompt.lower() or "yes/no" in prompt.lower():
                return "true"
            else:
                return "Yes, this message appears to be urgent based on the language used."

        elif "analyze" in prompt.lower() and "json" in prompt.lower():
            return '{"sentiment": "positive", "confidence": 0.85, "key_themes": ["growth", "opportunity"]}'

        elif "analyze" in prompt.lower():
            return (
                "**Analysis Results:**\n\n• **Sentiment**: Positive\n• **Key Themes**: Growth and opportunity\n• **Confidence**: High (85%)"
            )

        else:
            return f"Response to: {prompt[:50]}..."


# IPV Function Type Definitions
IPVInferFunction = Callable[[str, SandboxContext, Dict], EnhancedContext]
IPVProcessFunction = Callable[[str, EnhancedContext, Dict], Any]
IPVValidateFunction = Callable[[Any, EnhancedContext, Dict], Any]


class IPVPromptOptimizer:
    """Core IPV Prompt Optimization Engine"""

    def __init__(self, llm=None, verbose=False):
        self.llm = llm or MockLLM()
        self.verbose = verbose  # Add verbose flag for prompt debugging
        self.type_defaults = self._setup_type_defaults()
        self.profiles = self._setup_profiles()

    def _setup_type_defaults(self) -> Dict[type, Dict]:
        """Type-driven default optimization settings"""
        return {
            float: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.MINIMAL,
                "validation_rules": ["numeric_only", "decimal_format"],
                "format_requirements": ["no_currency_symbols", "no_text"],
                "cleaning_rules": ["extract_numbers", "handle_currency"],
            },
            int: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.MINIMAL,
                "validation_rules": ["integer_only"],
                "format_requirements": ["no_decimals", "no_text"],
                "cleaning_rules": ["extract_integers", "handle_text_numbers"],
            },
            bool: {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.MINIMAL,
                "validation_rules": ["boolean_only"],
                "format_requirements": ["true_false_only"],
                "cleaning_rules": ["parse_yes_no", "parse_boolean_text"],
            },
            str: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.ORGANIZED,
                "context_level": ContextLevel.STANDARD,
                "validation_rules": ["string_format"],
                "format_requirements": ["clean_text"],
                "cleaning_rules": ["remove_markdown", "clean_whitespace", "remove_bullets"],
            },
            dict: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.DETAILED,
                "validation_rules": ["valid_json", "consistent_structure"],
                "format_requirements": ["json_format"],
                "cleaning_rules": ["validate_json", "fix_json_syntax"],
            },
            list: {
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.FORMATTED,
                "context_level": ContextLevel.STANDARD,
                "validation_rules": ["array_format", "consistent_items"],
                "format_requirements": ["list_format"],
                "cleaning_rules": ["parse_arrays", "handle_bullet_points"],
            },
        }

    def _setup_profiles(self) -> Dict[str, Dict]:
        """Built-in optimization profiles"""
        return {
            "default": {
                "reliability": ReliabilityLevel.MEDIUM,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.ORGANIZED,
                "context_level": ContextLevel.STANDARD,
            },
            "production": {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.STANDARD,
            },
            "creative": {
                "reliability": ReliabilityLevel.LOW,
                "precision": PrecisionLevel.LOOSE,
                "safety": SafetyLevel.LOW,
                "structure": StructureLevel.FREE,
                "context_level": ContextLevel.DETAILED,
            },
            "financial": {
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.MAXIMUM,
                "structure": StructureLevel.STRICT,
                "context_level": ContextLevel.DETAILED,
            },
            "fast": {
                "reliability": ReliabilityLevel.MEDIUM,
                "precision": PrecisionLevel.GENERAL,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.ORGANIZED,
                "context_level": ContextLevel.MINIMAL,
            },
        }

    def default_infer(self, prompt: str, context: SandboxContext, options: Dict, expected_type: type = str) -> EnhancedContext:
        """Default INFER function: Understand requirements and optimize prompt"""

        # Use expected_type parameter if provided, otherwise get from options
        target_type = expected_type if expected_type != str else options.get("expected_type", str)

        # Get type-driven defaults
        type_config = self.type_defaults.get(target_type, self.type_defaults[str])

        # Apply profile if specified
        profile_name = options.get("profile", "default")
        profile_config = self.profiles.get(profile_name, self.profiles["default"])

        # Detect domain from prompt and context
        domain = self._detect_domain(prompt, context)

        # Create enhanced context
        enhanced_context = EnhancedContext(
            original_prompt=prompt,
            expected_type=target_type,
            domain=domain,
            reliability=profile_config.get("reliability", type_config["reliability"]),
            precision=profile_config.get("precision", type_config["precision"]),
            safety=profile_config.get("safety", type_config["safety"]),
            structure=profile_config.get("structure", type_config["structure"]),
            context_level=profile_config.get("context_level", type_config["context_level"]),
            validation_rules=type_config["validation_rules"],
            format_requirements=type_config["format_requirements"],
            examples=[],
            enhanced_prompt="",
        )

        # Add examples based on type and domain
        enhanced_context.examples = self._generate_examples(target_type, domain)

        # Generate enhanced prompt
        enhanced_context.enhanced_prompt = self._generate_enhanced_prompt(prompt, enhanced_context)

        return enhanced_context

    def default_process(self, prompt: str, enhanced_context: EnhancedContext, options: Dict) -> Any:
        """Default PROCESS function: Execute with liberal acceptance"""

        # Get the enhanced prompt from the context (already generated in INFER phase)
        enhanced_prompt = enhanced_context.enhanced_prompt

        # Get max iterations from config
        max_iterations = options.get("process", {}).get("config", {}).get("max_iterations", 3)

        # Try multiple iterations if needed
        for attempt in range(max_iterations):
            try:
                # Call LLM with enhanced prompt
                raw_response = self.llm.call(enhanced_prompt)

                # Liberal parsing - try to extract meaning
                parsed_response = self._liberal_parse(raw_response, enhanced_context)

                return parsed_response

            except Exception as e:
                if attempt == max_iterations - 1:
                    raise e

                # Enhance prompt based on failure
                enhanced_prompt = self._enhance_prompt_from_failure(enhanced_prompt, str(e), enhanced_context)

        raise Exception("Failed to get valid response after maximum iterations")

    def default_validate(self, result: Any, enhanced_context: EnhancedContext, options: Dict) -> Any:
        """Default VALIDATE function: Ensure conservative output"""

        # Apply type-specific cleaning
        cleaned_result = self._apply_type_cleaning(result, enhanced_context)

        # Validate type compliance
        validated_result = self._validate_type_compliance(cleaned_result, enhanced_context)

        # Apply format validation
        final_result = self._apply_format_validation(validated_result, enhanced_context)

        return final_result

    def _detect_domain(self, prompt: str, context: SandboxContext) -> str:
        """Detect domain from prompt content and context"""
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["price", "cost", "money", "dollar", "revenue", "profit"]):
            return "financial"
        elif any(word in prompt_lower for word in ["analyze", "data", "metrics", "performance"]):
            return "analytical"
        elif any(word in prompt_lower for word in ["email", "contact", "address"]):
            return "communication"
        elif any(word in prompt_lower for word in ["urgent", "priority", "important"]):
            return "classification"
        else:
            return "general"

    def _generate_examples(self, expected_type: type, domain: str) -> List[str]:
        """Generate examples based on type and domain"""
        if expected_type == float and domain == "financial":
            return ["29.99", "1250.00", "0.99"]
        elif expected_type == bool:
            return ["true", "false"]
        elif expected_type == str and domain == "communication":
            return ["john.doe@example.com", "Clean, readable text without formatting"]
        else:
            return []

    def _generate_enhanced_prompt(self, original_prompt: str, enhanced_context: EnhancedContext) -> str:
        """Generate enhanced prompt based on context"""

        enhanced_prompt = original_prompt

        # Add type-specific requirements
        if enhanced_context.expected_type == float:
            enhanced_prompt += "\n\nRequirements:\n- Return ONLY the numeric value as a decimal (e.g., 29.99)\n- No currency symbols ($, €, etc.)\n- No text or explanations\n- If no value found, return 0.0"

        elif enhanced_context.expected_type == bool:
            enhanced_prompt += (
                "\n\nRequirements:\n- Return ONLY 'true' or 'false'\n- No explanations or additional text\n- Use lowercase boolean values"
            )

        elif enhanced_context.expected_type == str:
            enhanced_prompt += "\n\nRequirements:\n- Return clean, readable text\n- No markdown formatting (**bold**, *italic*, etc.)\n- No bullet points or special characters\n- Plain text only"

        elif enhanced_context.expected_type == dict:
            enhanced_prompt += "\n\nRequirements:\n- Return valid JSON object\n- Use proper JSON syntax with double quotes\n- No trailing commas\n- No comments or explanations outside the JSON"

        # Add examples if available
        if enhanced_context.examples:
            enhanced_prompt += "\n\nExamples of correct format:\n"
            for example in enhanced_context.examples[:3]:  # Limit to 3 examples
                enhanced_prompt += f"- {example}\n"

        # Add domain-specific context
        if enhanced_context.domain == "financial":
            enhanced_prompt += "\n\nContext: This is financial data requiring high precision and accuracy."

        return enhanced_prompt

    def _liberal_parse(self, response: str, enhanced_context: EnhancedContext) -> Any:
        """Liberal parsing - extract meaning from any response format"""

        if enhanced_context.expected_type == float:
            # Extract numbers from text
            numbers = re.findall(r"\d+\.?\d*", response.replace("$", "").replace(",", ""))
            if numbers:
                return float(numbers[0])
            return 0.0

        elif enhanced_context.expected_type == int:
            # Extract integers from text
            numbers = re.findall(r"\d+", response)
            if numbers:
                return int(numbers[0])
            return 0

        elif enhanced_context.expected_type == bool:
            # Parse various boolean representations
            response_lower = response.lower().strip()
            if any(word in response_lower for word in ["true", "yes", "approved", "urgent", "important"]):
                return True
            elif any(word in response_lower for word in ["false", "no", "rejected", "not urgent", "normal"]):
                return False
            return False

        elif enhanced_context.expected_type == dict:
            # Try to extract JSON from response
            try:
                # Look for JSON-like content
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback: create simple dict from response
                    return {"content": response.strip()}
            except:
                return {"content": response.strip()}

        else:  # str or other types
            return response.strip()

    def _apply_type_cleaning(self, result: Any, enhanced_context: EnhancedContext) -> Any:
        """Apply type-specific cleaning rules"""

        if enhanced_context.expected_type == str and isinstance(result, str):
            # Remove markdown formatting
            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", result)  # Remove **bold**
            cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)  # Remove *italic*
            cleaned = re.sub(r"^\s*[•\-\*]\s*", "", cleaned, flags=re.MULTILINE)  # Remove bullets
            cleaned = re.sub(r"\n\s*\n", "\n", cleaned)  # Clean extra whitespace
            return cleaned.strip()

        return result

    def _validate_type_compliance(self, result: Any, enhanced_context: EnhancedContext) -> Any:
        """Validate that result matches expected type"""

        expected_type = enhanced_context.expected_type

        if not isinstance(result, expected_type):
            # Try to convert
            try:
                if expected_type == float:
                    return float(result)
                elif expected_type == int:
                    return int(float(result))  # Handle "29.0" -> 29
                elif expected_type == bool:
                    if isinstance(result, str):
                        return result.lower() in ["true", "yes", "1", "approved"]
                    return bool(result)
                elif expected_type == str:
                    return str(result)
                elif expected_type == dict:
                    if isinstance(result, str):
                        return json.loads(result)
                    return dict(result)
                elif expected_type == list:
                    if isinstance(result, str):
                        # Try to parse as JSON array, or split by lines/commas
                        try:
                            return json.loads(result)
                        except:
                            return [item.strip() for item in result.split("\n") if item.strip()]
                    return list(result)
            except:
                pass

        return result

    def _apply_format_validation(self, result: Any, enhanced_context: EnhancedContext) -> Any:
        """Apply final format validation and guarantees"""

        # Ensure we have the exact type we promised
        if not isinstance(result, enhanced_context.expected_type):
            # Last resort: provide safe default
            if enhanced_context.expected_type == float:
                return 0.0
            elif enhanced_context.expected_type == int:
                return 0
            elif enhanced_context.expected_type == bool:
                return False
            elif enhanced_context.expected_type == str:
                return ""
            elif enhanced_context.expected_type == dict:
                return {}
            elif enhanced_context.expected_type == list:
                return []

        return result

    def _enhance_prompt_from_failure(self, prompt: str, error: str, enhanced_context: EnhancedContext) -> str:
        """Enhance prompt based on previous failure"""

        if "json" in error.lower() and enhanced_context.expected_type == dict:
            return prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No explanations before or after."

        elif enhanced_context.expected_type in [float, int]:
            return prompt + "\n\nIMPORTANT: Return ONLY the number. No text, symbols, or explanations."

        return prompt + "\n\nPlease follow the format requirements exactly."

    def reason(self, prompt: str, expected_type: type = str, config: Optional[dict] = None) -> Any:
        """
        Main IPV reasoning function with optional prompt debugging
        """
        if config is None:
            config = {}

        # Add expected_type to config for compatibility
        config["expected_type"] = expected_type

        # Create context (in real Dana, this would come from the runtime)
        context = SandboxContext(function_name="demo_function", domain=config.get("domain"))
        context.variables["user_data"] = "sample"

        # Get IPV functions (custom or default)
        infer_func = config.get("infer", {}).get("function", self.default_infer)
        process_func = config.get("process", {}).get("function", self.default_process)
        validate_func = config.get("validate", {}).get("function", self.default_validate)

        # INFER: Understand requirements and optimize prompt
        enhanced_context = infer_func(prompt, context, config, expected_type)

        # Print prompts if verbose mode is enabled
        if self.verbose:
            print("\n🔍 PROMPT DEBUGGING:")
            print(f"📝 Raw prompt: '{prompt}'")
            print(f"⚡ Optimized prompt:\n{'-' * 40}")
            print(enhanced_context.enhanced_prompt)
            print("-" * 40)

        # PROCESS: Get LLM response
        raw_response = process_func(prompt, enhanced_context, config)

        if self.verbose:
            print(f"🤖 LLM response: '{raw_response}'")

        # VALIDATE: Parse and validate response
        validated_result = validate_func(raw_response, enhanced_context, config)

        if self.verbose:
            print(f"✅ Final result: {validated_result} (type: {type(validated_result).__name__})")
            print()

        return validated_result


def demo_ipv_system():
    """Demonstrate the IPV system in action"""

    print("=" * 80)
    print("IPV (Infer-Process-Validate) Prompt Optimization Demo")
    print("=" * 80)

    optimizer = IPVPromptOptimizer(verbose=True)

    # Demo 1: Type-driven optimization
    print("\n" + "=" * 50)
    print("DEMO 1: Type-Driven Automatic Optimization")
    print("=" * 50)

    print("\n1. Extract price as float:")
    price = optimizer.reason("Get the price from this invoice", expected_type=float)
    assert isinstance(price, float), f"Expected float, got {type(price)}"

    print("\n2. Extract email as string:")
    email = optimizer.reason("Find the email address", expected_type=str)
    assert isinstance(email, str), f"Expected str, got {type(email)}"

    print("\n3. Check if urgent as boolean:")
    is_urgent = optimizer.reason("Is this message urgent?", expected_type=bool)
    assert isinstance(is_urgent, bool), f"Expected bool, got {type(is_urgent)}"

    print("\n4. Analyze data as dict:")
    analysis = optimizer.reason("Analyze this customer feedback", expected_type=dict)
    assert isinstance(analysis, dict), f"Expected dict, got {type(analysis)}"

    # Demo 2: Profile-based optimization
    print("\n" + "=" * 50)
    print("DEMO 2: Profile-Based Optimization")
    print("=" * 50)

    print("\n1. Financial analysis with 'financial' profile:")
    financial_result = optimizer.reason("Calculate the quarterly revenue", expected_type=float, config={"profile": "financial"})

    print("\n2. Creative content with 'creative' profile:")
    creative_result = optimizer.reason("Write a short story", expected_type=str, config={"profile": "creative"})

    # Demo 3: Advanced configuration
    print("\n" + "=" * 50)
    print("DEMO 3: Advanced Configuration")
    print("=" * 50)

    print("\n1. High-precision analysis:")
    precise_result = optimizer.reason(
        "Analyze the data thoroughly",
        expected_type=dict,
        config={
            "infer": {"config": {"context_collection": "comprehensive"}},
            "process": {"config": {"max_iterations": 5}},
            "validate": {"config": {"quality_threshold": "high"}},
        },
    )

    print("\n" + "=" * 50)
    print("DEMO COMPLETE - All type guarantees maintained!")
    print("=" * 50)

    # Show LLM call efficiency
    print(f"\nTotal LLM calls made: {optimizer.llm.call_count}")
    print("IPV automatically handled format variations and ensured type compliance!")


if __name__ == "__main__":
    demo_ipv_system()
