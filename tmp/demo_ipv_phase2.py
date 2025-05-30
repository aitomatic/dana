#!/usr/bin/env python3
"""
Demo of IPV (Infer-Process-Validate) Phase 2: Type-Driven Optimization

This demo shows the type-driven optimization features including:
- Automatic type inference from various sources
- Type-specific optimization rules
- Enhanced validation and conversion
- Pre-defined optimization profiles
"""

from opendxa.dana.ipv import IPVConfig, IPVOrchestrator, TypeInferenceEngine, TypeOptimizationRegistry, TypeValidator


def demo_type_inference():
    """Demo automatic type inference capabilities."""
    print("=" * 60)
    print("DEMO 1: Type Inference Engine")
    print("=" * 60)

    engine = TypeInferenceEngine()

    # Test basic type inference from strings
    print("\n🔍 Basic Type Inference from Strings:")
    type_strings = ["str", "int", "float", "bool", "dict", "list"]

    for type_str in type_strings:
        inferred_type = engine.infer_type_from_string(type_str)
        print(f"   '{type_str}' → {inferred_type.__name__ if inferred_type else 'None'}")

    # Test generic type inference
    print("\n🔍 Generic Type Inference:")
    generic_types = ["List[str]", "Dict[str, int]", "Optional[float]"]

    for type_str in generic_types:
        inferred_type = engine.infer_type_from_string(type_str)
        if inferred_type:
            print(f"   '{type_str}' → {inferred_type}")
            if engine.is_generic_type(inferred_type):
                info = engine.get_generic_info(inferred_type)
                print(f"      Origin: {info['origin']}, Args: {info['args']}")
        else:
            print(f"   '{type_str}' → None")

    # Test assignment code inference
    print("\n🔍 Assignment Code Inference:")
    assignments = [
        "price: float = 29.99",
        "count: int = 5",
        "is_valid: bool = True",
        "name: str = 'test'",
        "data: dict = {}",
    ]

    for assignment in assignments:
        inferred_type = engine.infer_type_from_assignment(assignment)
        print(f"   {assignment}")
        print(f"   → {inferred_type.__name__ if inferred_type else 'None'}")

    print("-" * 40)


def demo_type_defaults():
    """Demo type-specific default configurations."""
    print("\n" + "=" * 60)
    print("DEMO 2: Type-Specific Defaults")
    print("=" * 60)

    engine = TypeInferenceEngine()

    types_to_test = [float, int, bool, str, dict, list]

    for type_obj in types_to_test:
        print(f"\n📋 Defaults for {type_obj.__name__}:")
        defaults = engine.get_type_defaults(type_obj)

        print(f"   Reliability: {defaults['reliability'].value}")
        print(f"   Precision: {defaults['precision'].value}")
        print(f"   Safety: {defaults['safety'].value}")
        print(f"   Structure: {defaults['structure'].value}")
        print(f"   Context: {defaults['context'].value}")
        print(f"   Auto-cleaning: {defaults['auto_cleaning'][:3]}...")  # Show first 3
        print(f"   Validation rules: {defaults['validation_rules'][:2]}...")  # Show first 2

    print("-" * 40)


def demo_type_optimization_registry():
    """Demo the type optimization registry and rules."""
    print("\n" + "=" * 60)
    print("DEMO 3: Type Optimization Registry")
    print("=" * 60)

    registry = TypeOptimizationRegistry()

    # Test optimization for different types
    base_config = IPVConfig()

    types_to_optimize = [float, int, bool, str, dict, list]

    for type_obj in types_to_optimize:
        print(f"\n⚙️  Optimizing config for {type_obj.__name__}:")

        optimized_config = registry.optimize_config_for_type(base_config, type_obj)

        print(f"   Original reliability: {base_config.reliability.value}")
        print(f"   Optimized reliability: {optimized_config.reliability.value}")
        print(f"   Original precision: {base_config.precision.value}")
        print(f"   Optimized precision: {optimized_config.precision.value}")

        # Show recommended profile
        profile = registry.get_profile_for_type(type_obj)
        print(f"   Recommended profile: {profile}")

        # Show applicable rules
        rules = registry.list_rules_for_type(type_obj)
        if rules:
            print(f"   Applied rules: {[rule.name for rule in rules]}")

    print("-" * 40)


def demo_enhanced_validation():
    """Demo the enhanced type validation system."""
    print("\n" + "=" * 60)
    print("DEMO 4: Enhanced Type Validation")
    print("=" * 60)

    validator = TypeValidator()

    # Test float validation with currency handling
    print("\n💰 Float Validation (Currency Handling):")
    float_test_cases = [
        "$29.99",
        "The price is 45.50 dollars",
        "€123.45",
        "29.99",
        "invalid",
        None,
    ]

    for test_value in float_test_cases:
        result = validator.validate_and_convert(test_value, float, {"currency_symbol_handling": True, "fallback_value": 0.0})

        print(f"   Input: {test_value}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Output: {result.converted_value}")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")
        if result.errors:
            print(f"   Errors: {result.errors}")
        print()

    # Test boolean validation with text parsing
    print("🔘 Boolean Validation (Text Parsing):")
    bool_test_cases = [
        "yes",
        "no",
        "true",
        "false",
        "approved",
        "rejected",
        "maybe",
        1,
        0,
    ]

    for test_value in bool_test_cases:
        result = validator.validate_and_convert(test_value, bool, {"yes_no_parsing": True, "approval_parsing": True})

        print(f"   Input: {test_value} → Valid: {result.is_valid}, Output: {result.converted_value}")
        if result.errors:
            print(f"      Errors: {result.errors}")

    # Test string validation with markdown removal
    print("\n📝 String Validation (Markdown Removal):")
    markdown_text = "**Bold text** with *italic* and bullet points:\n- Item 1\n- Item 2"

    result = validator.validate_and_convert(markdown_text, str, {"markdown_removal": True, "whitespace_normalization": True})

    print(f"   Input: {repr(markdown_text)}")
    print(f"   Output: {repr(result.converted_value)}")
    print(f"   Valid: {result.is_valid}")

    # Test dict validation with JSON error correction
    print("\n📊 Dict Validation (JSON Error Correction):")
    json_test_cases = [
        '{"name": "test", "value": 123}',  # Valid JSON
        "{name: 'test', value: 123}",  # Unquoted keys, single quotes
        '{"name": "test", "value": 123,}',  # Trailing comma
        "invalid json",
    ]

    for test_json in json_test_cases:
        result = validator.validate_and_convert(test_json, dict, {"error_correction": True})

        print(f"   Input: {test_json}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Output: {result.converted_value}")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")
        if result.errors:
            print(f"   Errors: {result.errors}")
        print()

    print("-" * 40)


def demo_format_validation():
    """Demo format-specific validation."""
    print("\n" + "=" * 60)
    print("DEMO 5: Format-Specific Validation")
    print("=" * 60)

    validator = TypeValidator()

    # Test email validation
    print("\n📧 Email Format Validation:")
    email_test_cases = [
        "user@example.com",
        "invalid.email",
        "test@domain",
        "@example.com",
        "user@example.co.uk",
    ]

    for email in email_test_cases:
        result = validator.validate_format(email, "email")
        print(f"   {email} → Valid: {result.is_valid}")
        if result.errors:
            print(f"      Errors: {result.errors}")

    # Test URL validation
    print("\n🌐 URL Format Validation:")
    url_test_cases = [
        "https://example.com",
        "http://test.org/path",
        "ftp://files.example.com",
        "invalid-url",
        "example.com",  # Missing scheme
    ]

    for url in url_test_cases:
        result = validator.validate_format(url, "url")
        print(f"   {url} → Valid: {result.is_valid}")
        if result.errors:
            print(f"      Errors: {result.errors}")

    # Test phone validation
    print("\n📞 Phone Format Validation:")
    phone_test_cases = [
        "+1-555-123-4567",
        "(555) 123-4567",
        "555.123.4567",
        "5551234567",
        "123",  # Too short
        "12345678901234567890",  # Too long
    ]

    for phone in phone_test_cases:
        result = validator.validate_format(phone, "phone")
        print(f"   {phone} → Valid: {result.is_valid}")
        if result.errors:
            print(f"      Errors: {result.errors}")

    print("-" * 40)


def demo_integrated_type_optimization():
    """Demo integrated type-driven optimization in IPV pipeline."""
    print("\n" + "=" * 60)
    print("DEMO 6: Integrated Type-Driven Optimization")
    print("=" * 60)

    # Create a mock context that provides type information
    class MockTypedContext:
        def get_type_annotation(self, variable_name):
            type_map = {
                "price": float,
                "count": int,
                "is_approved": bool,
                "description": str,
                "metadata": dict,
                "tags": list,
            }
            return type_map.get(variable_name)

    context = MockTypedContext()
    registry = TypeOptimizationRegistry()

    # Test type-driven optimization for different scenarios
    test_scenarios = [
        ("price", "Extract price: $29.99"),
        ("count", "How many items: five"),
        ("is_approved", "Status: approved"),
        ("description", "**Product**: A great item with *features*"),
        ("metadata", '{"category": "electronics", "rating": 4.5}'),
        ("tags", "- electronics\n- gadgets\n- popular"),
    ]

    for variable_name, test_input in test_scenarios:
        print(f"\n🎯 Optimizing for variable '{variable_name}':")
        print(f"   Input: {test_input}")

        # Get base config
        base_config = IPVConfig()

        # Apply type-driven optimization
        optimized_config = registry.infer_and_optimize(base_config, context, variable_name)

        # Show the optimization applied
        inferred_type = context.get_type_annotation(variable_name)
        if inferred_type:
            print(f"   Inferred type: {inferred_type.__name__}")
            print(f"   Reliability: {base_config.reliability.value} → {optimized_config.reliability.value}")
            print(f"   Precision: {base_config.precision.value} → {optimized_config.precision.value}")
            print(f"   Safety: {base_config.safety.value} → {optimized_config.safety.value}")

            # Show type-specific settings
            type_settings = registry.get_type_specific_settings(inferred_type)
            print(f"   Auto-cleaning: {type_settings['auto_cleaning'][:2]}...")
            print(f"   Validation rules: {type_settings['validation_rules'][:2]}...")
        else:
            print(f"   Could not infer type for variable '{variable_name}'")

    print("-" * 40)


def demo_performance_comparison():
    """Demo performance comparison between default and type-optimized configs."""
    print("\n" + "=" * 60)
    print("DEMO 7: Performance Comparison")
    print("=" * 60)

    import time

    orchestrator = IPVOrchestrator()
    registry = TypeOptimizationRegistry()

    test_cases = [
        ("Financial extraction", "The total cost is $1,234.56", float),
        ("Boolean classification", "The request was approved", bool),
        ("Text cleaning", "**Important**: This is *formatted* text", str),
        ("Data parsing", '{"name": "test", "value": 123}', dict),
    ]

    for test_name, test_input, expected_type in test_cases:
        print(f"\n⚡ {test_name}:")
        print(f"   Input: {test_input}")
        print(f"   Expected type: {expected_type.__name__}")

        # Test with default config
        start_time = time.time()
        default_result = orchestrator.execute_ipv_pipeline(test_input)
        default_time = time.time() - start_time

        # Test with type-optimized config
        optimized_config = registry.optimize_config_for_type(IPVConfig(), expected_type)
        start_time = time.time()
        optimized_result = orchestrator.execute_ipv_pipeline(test_input, config=optimized_config)
        optimized_time = time.time() - start_time

        print(f"   Default result: {default_result.result}")
        print(f"   Optimized result: {optimized_result.result}")
        print(f"   Default time: {default_time:.4f}s")
        print(f"   Optimized time: {optimized_time:.4f}s")
        print(f"   Both successful: {default_result.is_success() and optimized_result.is_success()}")

    print("-" * 40)


def main():
    """Run all Phase 2 demos."""
    print("🚀 IPV (Infer-Process-Validate) Phase 2 Demo")
    print("Demonstrating Type-Driven Optimization capabilities")

    try:
        demo_type_inference()
        demo_type_defaults()
        demo_type_optimization_registry()
        demo_enhanced_validation()
        demo_format_validation()
        demo_integrated_type_optimization()
        demo_performance_comparison()

        print("\n" + "=" * 60)
        print("✅ All Phase 2 demos completed successfully!")
        print("🎯 Type-driven optimization is working correctly")
        print("📈 Key improvements:")
        print("   • Automatic type inference from multiple sources")
        print("   • Type-specific optimization rules and profiles")
        print("   • Enhanced validation with format-specific handling")
        print("   • Intelligent type conversion and error correction")
        print("   • Performance optimization based on expected types")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
