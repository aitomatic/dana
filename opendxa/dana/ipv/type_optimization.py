"""
Type-driven optimization system for IPV.

This module provides the TypeOptimizationRegistry that manages optimization
rules and automatic profile selection based on inferred types.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from .base import ContextLevel, IPVConfig, PrecisionLevel, ReliabilityLevel, SafetyLevel, StructureLevel
from .type_inference import TypeInferenceEngine


class TypeOptimizationRule:
    """
    A rule that defines how to optimize IPV for a specific type.
    """

    def __init__(
        self,
        target_type: Type,
        name: str,
        description: str,
        config_overrides: Dict[str, Any],
        infer_customizations: Optional[Dict[str, Any]] = None,
        process_customizations: Optional[Dict[str, Any]] = None,
        validate_customizations: Optional[Dict[str, Any]] = None,
        priority: int = 100,
    ):
        """
        Initialize a type optimization rule.

        Args:
            target_type: The type this rule applies to
            name: Human-readable name for the rule
            description: Description of what this rule does
            config_overrides: IPV config values to override
            infer_customizations: Custom settings for INFER phase
            process_customizations: Custom settings for PROCESS phase
            validate_customizations: Custom settings for VALIDATE phase
            priority: Priority for rule application (lower = higher priority)
        """
        self.target_type = target_type
        self.name = name
        self.description = description
        self.config_overrides = config_overrides
        self.infer_customizations = infer_customizations or {}
        self.process_customizations = process_customizations or {}
        self.validate_customizations = validate_customizations or {}
        self.priority = priority

    def applies_to(self, type_obj: Type) -> bool:
        """Check if this rule applies to the given type."""
        return type_obj == self.target_type

    def apply_to_config(self, config: IPVConfig) -> IPVConfig:
        """Apply this rule's optimizations to an IPV config."""
        # Create a copy of the config
        optimized_config = IPVConfig(
            reliability=config.reliability,
            precision=config.precision,
            safety=config.safety,
            structure=config.structure,
            context=config.context,
            infer_config=config.infer_config.copy(),
            process_config=config.process_config.copy(),
            validate_config=config.validate_config.copy(),
            infer_function=config.infer_function,
            process_function=config.process_function,
            validate_function=config.validate_function,
            max_iterations=config.max_iterations,
            timeout_seconds=config.timeout_seconds,
            debug_mode=config.debug_mode,
        )

        # Apply config overrides
        for key, value in self.config_overrides.items():
            if hasattr(optimized_config, key):
                setattr(optimized_config, key, value)

        # Apply phase-specific customizations
        optimized_config.infer_config.update(self.infer_customizations)
        optimized_config.process_config.update(self.process_customizations)
        optimized_config.validate_config.update(self.validate_customizations)

        return optimized_config


class TypeOptimizationRegistry:
    """
    Registry for type-driven optimization rules and automatic profile selection.
    """

    def __init__(self):
        self.type_inference = TypeInferenceEngine()
        self._rules: List[TypeOptimizationRule] = []
        self._type_profiles: Dict[Type, str] = {}
        self._custom_optimizers: Dict[Type, Callable[[IPVConfig], IPVConfig]] = {}

        # Initialize with default type optimization rules
        self._register_default_rules()

    def register_rule(self, rule: TypeOptimizationRule) -> None:
        """Register a new type optimization rule."""
        self._rules.append(rule)
        # Sort by priority (lower priority number = higher precedence)
        self._rules.sort(key=lambda r: r.priority)

    def register_custom_optimizer(self, target_type: Type, optimizer_func: Callable[[IPVConfig], IPVConfig]) -> None:
        """Register a custom optimization function for a specific type."""
        self._custom_optimizers[target_type] = optimizer_func

    def optimize_config_for_type(self, config: IPVConfig, target_type: Type) -> IPVConfig:
        """
        Optimize an IPV config for a specific target type.

        Args:
            config: Base IPV configuration
            target_type: The expected output type

        Returns:
            Optimized IPV configuration
        """
        optimized_config = config

        # Apply custom optimizer if available
        if target_type in self._custom_optimizers:
            optimized_config = self._custom_optimizers[target_type](optimized_config)

        # Apply matching rules in priority order
        for rule in self._rules:
            if rule.applies_to(target_type):
                optimized_config = rule.apply_to_config(optimized_config)

        return optimized_config

    def get_profile_for_type(self, target_type: Type) -> Optional[str]:
        """Get the recommended profile name for a specific type."""
        return self._type_profiles.get(target_type)

    def infer_and_optimize(self, config: IPVConfig, context: Any = None, variable_name: Optional[str] = None) -> IPVConfig:
        """
        Infer the target type from context and optimize the config accordingly.

        Args:
            config: Base IPV configuration
            context: Execution context for type inference
            variable_name: Variable name for type inference

        Returns:
            Type-optimized IPV configuration
        """
        # Try to infer the target type
        inferred_type = self.type_inference.infer_type_from_context(context, variable_name)

        if inferred_type:
            # Optimize config for the inferred type
            return self.optimize_config_for_type(config, inferred_type)
        else:
            # No type inferred, return original config
            return config

    def get_type_specific_settings(self, target_type: Type) -> Dict[str, Any]:
        """Get all type-specific settings for a given type."""
        return self.type_inference.get_type_defaults(target_type)

    def list_rules_for_type(self, target_type: Type) -> List[TypeOptimizationRule]:
        """Get all rules that apply to a specific type."""
        return [rule for rule in self._rules if rule.applies_to(target_type)]

    def _register_default_rules(self) -> None:
        """Register default type optimization rules based on the design document."""

        # Float optimization rule
        float_rule = TypeOptimizationRule(
            target_type=float,
            name="Float Precision Optimization",
            description="Optimizes for exact numeric extraction with currency handling",
            config_overrides={
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
            },
            process_customizations={
                "numeric_extraction": True,
                "currency_symbol_handling": True,
                "decimal_precision": "preserve",
                "fallback_value": 0.0,
            },
            validate_customizations={
                "type_enforcement": "strict",
                "numeric_validation": True,
                "range_checking": False,  # Can be enabled per use case
                "format_cleaning": ["remove_currency", "extract_decimal"],
            },
            priority=10,
        )
        self.register_rule(float_rule)
        self._type_profiles[float] = "financial"

        # Integer optimization rule
        int_rule = TypeOptimizationRule(
            target_type=int,
            name="Integer Precision Optimization",
            description="Optimizes for exact integer extraction with text number handling",
            config_overrides={
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.HIGH,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
            },
            process_customizations={
                "integer_extraction": True,
                "text_number_parsing": True,
                "decimal_truncation": "round",
                "fallback_value": 0,
            },
            validate_customizations={
                "type_enforcement": "strict",
                "integer_validation": True,
                "no_decimal_places": True,
                "format_cleaning": ["extract_integer", "handle_text_numbers"],
            },
            priority=10,
        )
        self.register_rule(int_rule)
        self._type_profiles[int] = "production"

        # Boolean optimization rule
        bool_rule = TypeOptimizationRule(
            target_type=bool,
            name="Boolean Classification Optimization",
            description="Optimizes for unambiguous true/false classification",
            config_overrides={
                "reliability": ReliabilityLevel.MAXIMUM,
                "precision": PrecisionLevel.EXACT,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.MINIMAL,
            },
            process_customizations={
                "boolean_classification": True,
                "yes_no_parsing": True,
                "approval_parsing": True,
                "conservative_fallback": False,  # Default to False when ambiguous
            },
            validate_customizations={
                "type_enforcement": "strict",
                "boolean_validation": True,
                "ambiguity_detection": True,
                "format_cleaning": ["parse_yes_no", "parse_true_false", "parse_approval"],
            },
            priority=10,
        )
        self.register_rule(bool_rule)
        self._type_profiles[bool] = "production"

        # String optimization rule
        str_rule = TypeOptimizationRule(
            target_type=str,
            name="String Formatting Optimization",
            description="Optimizes for clean text with markdown removal",
            config_overrides={
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.ORGANIZED,
                "context": ContextLevel.STANDARD,
            },
            process_customizations={
                "text_processing": True,
                "markdown_awareness": True,
                "formatting_preservation": "minimal",
            },
            validate_customizations={
                "type_enforcement": "lenient",
                "markdown_removal": True,
                "whitespace_normalization": True,
                "format_cleaning": ["remove_markdown", "clean_bullets", "normalize_whitespace"],
            },
            priority=20,
        )
        self.register_rule(str_rule)
        self._type_profiles[str] = "general"

        # Dictionary optimization rule
        dict_rule = TypeOptimizationRule(
            target_type=dict,
            name="Dictionary Structure Optimization",
            description="Optimizes for valid JSON with error correction",
            config_overrides={
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.STRICT,
                "context": ContextLevel.DETAILED,
            },
            process_customizations={
                "json_processing": True,
                "structure_validation": True,
                "error_correction": "aggressive",
            },
            validate_customizations={
                "type_enforcement": "strict",
                "json_validation": True,
                "structure_consistency": True,
                "format_cleaning": ["validate_json", "fix_syntax_errors", "normalize_keys"],
            },
            priority=20,
        )
        self.register_rule(dict_rule)
        self._type_profiles[dict] = "structured"

        # List optimization rule
        list_rule = TypeOptimizationRule(
            target_type=list,
            name="List Structure Optimization",
            description="Optimizes for consistent array format with item parsing",
            config_overrides={
                "reliability": ReliabilityLevel.HIGH,
                "precision": PrecisionLevel.SPECIFIC,
                "safety": SafetyLevel.MEDIUM,
                "structure": StructureLevel.FORMATTED,
                "context": ContextLevel.STANDARD,
            },
            process_customizations={
                "array_processing": True,
                "bullet_point_parsing": True,
                "item_consistency": True,
            },
            validate_customizations={
                "type_enforcement": "lenient",
                "array_validation": True,
                "item_type_consistency": False,  # Allow mixed types by default
                "format_cleaning": ["parse_arrays", "handle_bullet_points", "normalize_items"],
            },
            priority=20,
        )
        self.register_rule(list_rule)
        self._type_profiles[list] = "structured"


class TypeOptimizationProfile:
    """
    A named collection of type optimization settings.
    """

    def __init__(self, name: str, description: str, type_rules: Dict[Type, Dict[str, Any]]):
        """
        Initialize a type optimization profile.

        Args:
            name: Profile name
            description: Profile description
            type_rules: Dictionary mapping types to their optimization settings
        """
        self.name = name
        self.description = description
        self.type_rules = type_rules

    def get_config_for_type(self, target_type: Type, base_config: IPVConfig) -> IPVConfig:
        """Get optimized config for a specific type using this profile."""
        if target_type not in self.type_rules:
            return base_config

        rule_settings = self.type_rules[target_type]

        # Create optimized config
        optimized_config = IPVConfig(
            reliability=rule_settings.get("reliability", base_config.reliability),
            precision=rule_settings.get("precision", base_config.precision),
            safety=rule_settings.get("safety", base_config.safety),
            structure=rule_settings.get("structure", base_config.structure),
            context=rule_settings.get("context", base_config.context),
            infer_config={**base_config.infer_config, **rule_settings.get("infer_config", {})},
            process_config={**base_config.process_config, **rule_settings.get("process_config", {})},
            validate_config={**base_config.validate_config, **rule_settings.get("validate_config", {})},
            max_iterations=rule_settings.get("max_iterations", base_config.max_iterations),
            timeout_seconds=rule_settings.get("timeout_seconds", base_config.timeout_seconds),
            debug_mode=rule_settings.get("debug_mode", base_config.debug_mode),
        )

        return optimized_config


# Pre-defined optimization profiles
FINANCIAL_PROFILE = TypeOptimizationProfile(
    name="financial",
    description="Optimized for financial data with maximum precision and safety",
    type_rules={
        float: {
            "reliability": ReliabilityLevel.MAXIMUM,
            "precision": PrecisionLevel.EXACT,
            "safety": SafetyLevel.MAXIMUM,
            "structure": StructureLevel.STRICT,
            "process_config": {"currency_handling": True, "decimal_precision": "exact"},
            "validate_config": {"financial_validation": True, "range_checking": True},
        },
        int: {
            "reliability": ReliabilityLevel.MAXIMUM,
            "precision": PrecisionLevel.EXACT,
            "safety": SafetyLevel.HIGH,
            "structure": StructureLevel.STRICT,
        },
        str: {
            "reliability": ReliabilityLevel.HIGH,
            "precision": PrecisionLevel.SPECIFIC,
            "safety": SafetyLevel.HIGH,
            "validate_config": {"financial_disclaimer": True},
        },
    },
)

CREATIVE_PROFILE = TypeOptimizationProfile(
    name="creative",
    description="Optimized for creative content with flexibility and variation",
    type_rules={
        str: {
            "reliability": ReliabilityLevel.LOW,
            "precision": PrecisionLevel.LOOSE,
            "safety": SafetyLevel.LOW,
            "structure": StructureLevel.FREE,
            "context": ContextLevel.DETAILED,
            "process_config": {"creativity_boost": True, "variation_encouraged": True},
            "validate_config": {"minimal_constraints": True},
        },
        list: {
            "reliability": ReliabilityLevel.MEDIUM,
            "precision": PrecisionLevel.GENERAL,
            "structure": StructureLevel.ORGANIZED,
            "process_config": {"creative_lists": True},
        },
    },
)

PRODUCTION_PROFILE = TypeOptimizationProfile(
    name="production",
    description="Optimized for production use with maximum reliability",
    type_rules={
        float: {
            "reliability": ReliabilityLevel.MAXIMUM,
            "precision": PrecisionLevel.EXACT,
            "safety": SafetyLevel.HIGH,
            "structure": StructureLevel.STRICT,
        },
        int: {
            "reliability": ReliabilityLevel.MAXIMUM,
            "precision": PrecisionLevel.EXACT,
            "safety": SafetyLevel.HIGH,
            "structure": StructureLevel.STRICT,
        },
        bool: {
            "reliability": ReliabilityLevel.MAXIMUM,
            "precision": PrecisionLevel.EXACT,
            "safety": SafetyLevel.MEDIUM,
            "structure": StructureLevel.STRICT,
        },
        str: {
            "reliability": ReliabilityLevel.HIGH,
            "precision": PrecisionLevel.SPECIFIC,
            "safety": SafetyLevel.MEDIUM,
            "structure": StructureLevel.ORGANIZED,
        },
        dict: {
            "reliability": ReliabilityLevel.HIGH,
            "precision": PrecisionLevel.SPECIFIC,
            "safety": SafetyLevel.MEDIUM,
            "structure": StructureLevel.STRICT,
        },
        list: {
            "reliability": ReliabilityLevel.HIGH,
            "precision": PrecisionLevel.SPECIFIC,
            "safety": SafetyLevel.MEDIUM,
            "structure": StructureLevel.FORMATTED,
        },
    },
)
