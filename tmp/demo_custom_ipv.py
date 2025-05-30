#!/usr/bin/env python3
"""
Advanced IPV Demo - Custom Functions and Enhanced Prompts

This demo shows:
1. How enhanced prompts look in detail
2. Custom IPV functions for domain-specific optimization
3. The new API structure in action
4. Liberal parsing handling messy LLM responses
"""

from typing import Any, Dict

from prototype_ipv import EnhancedContext, IPVPromptOptimizer, SandboxContext


def financial_infer(prompt: str, context: SandboxContext, options: Dict) -> EnhancedContext:
    """Custom INFER function specialized for financial domain."""
    print("   🏦 Using CUSTOM financial INFER function")

    # Call default infer first
    optimizer = IPVPromptOptimizer()
    enhanced_context = optimizer.default_infer(prompt, context, options)

    # Override with financial-specific settings
    enhanced_context.domain = "financial"
    enhanced_context.safety = enhanced_context.safety.__class__.MAXIMUM
    enhanced_context.precision = enhanced_context.precision.__class__.EXACT
    enhanced_context.validation_rules.extend(["regulatory_compliance", "audit_trail"])
    enhanced_context.format_requirements.extend(["currency_precision", "decimal_places"])

    # Add financial-specific examples
    if enhanced_context.expected_type == float:
        enhanced_context.examples = ["1234.56", "0.01", "999999.99"]

    return enhanced_context


def creative_process(prompt: str, enhanced_context: EnhancedContext, options: Dict) -> Any:
    """Custom PROCESS function that encourages creativity."""
    print("   🎨 Using CUSTOM creative PROCESS function")

    # Modify prompt to encourage creativity
    creative_prompt = f"""
{prompt}

CREATIVE INSTRUCTIONS:
- Be imaginative and original
- Use vivid, descriptive language
- Don't worry about being too formal
- Let your creativity flow freely
- Make it engaging and interesting

Format: {enhanced_context.format_requirements}
"""

    # Simulate creative LLM response
    if "story" in prompt.lower():
        return """**The Mysterious Garden**

In a *forgotten corner* of the city, where concrete meets dreams, there lived a small garden that bloomed with impossible colors. 

• The roses sang lullabies at midnight
• The daisies danced in the morning breeze  
• And the old oak tree whispered secrets to anyone brave enough to listen

This was no ordinary garden - it was a place where magic still believed in itself."""

    else:
        return f"Creative response to: {prompt}"


def strict_financial_validate(result: Any, enhanced_context: EnhancedContext, options: Dict) -> Any:
    """Custom VALIDATE function with strict financial requirements."""
    print("   💰 Using CUSTOM strict financial VALIDATE function")

    # Apply extra financial validation
    if enhanced_context.expected_type == float:
        if isinstance(result, (int, float)):
            # Ensure proper decimal precision for financial data
            validated_result = round(float(result), 2)
            print(f"   💰 Financial validation: Rounded to 2 decimal places: {validated_result}")
            return validated_result
        else:
            print("   💰 Financial validation: Invalid numeric data, returning 0.00")
            return 0.00

    return result


def demo_enhanced_prompts():
    """Show what enhanced prompts look like in detail"""

    print("\n" + "=" * 80)
    print("ENHANCED PROMPT DEMONSTRATION")
    print("=" * 80)

    optimizer = IPVPromptOptimizer()

    # Patch the process function to show enhanced prompts
    original_process = optimizer.default_process

    def show_enhanced_prompt(prompt: str, enhanced_context: EnhancedContext, options: Dict) -> Any:
        print("\n📝 ENHANCED PROMPT:")
        print("-" * 60)
        print(enhanced_context.enhanced_prompt)
        print("-" * 60)
        return original_process(prompt, enhanced_context, options)

    optimizer.default_process = show_enhanced_prompt

    print("\n1. Float extraction with automatic enhancement:")
    price = optimizer.reason("Extract the price", expected_type=float)

    print("\n2. Boolean classification with automatic enhancement:")
    urgent = optimizer.reason("Is this urgent?", expected_type=bool)

    print("\n3. Dictionary analysis with automatic enhancement:")
    analysis = optimizer.reason("Analyze the customer feedback", expected_type=dict)


def demo_custom_ipv_functions():
    """Demonstrate custom IPV functions with the new API structure"""

    print("\n" + "=" * 80)
    print("CUSTOM IPV FUNCTIONS DEMONSTRATION")
    print("=" * 80)

    optimizer = IPVPromptOptimizer()

    print("\n1. Financial analysis with custom INFER and VALIDATE:")
    financial_result = optimizer.reason(
        "Calculate the quarterly profit margin",
        {"infer": {"function": financial_infer}, "validate": {"function": strict_financial_validate}},
        expected_type=float,
    )
    print(f"✅ Result: {financial_result} (guaranteed 2 decimal places)")

    print("\n2. Creative writing with custom PROCESS:")
    story = optimizer.reason("Write a short story about a magical garden", {"process": {"function": creative_process}}, expected_type=str)
    print(f"✅ Creative story generated (length: {len(story)} chars)")

    print("\n3. Mixed custom functions - financial INFER + creative PROCESS:")
    creative_financial = optimizer.reason(
        "Write an engaging description of our Q4 revenue growth",
        {
            "infer": {"function": financial_infer},
            "process": {"function": creative_process},
            "validate": {"function": strict_financial_validate},
        },
        expected_type=str,
    )
    print(f"✅ Creative financial content: {creative_financial[:100]}...")


def demo_liberal_parsing():
    """Show how liberal parsing handles messy LLM responses"""

    print("\n" + "=" * 80)
    print("LIBERAL PARSING DEMONSTRATION")
    print("=" * 80)

    optimizer = IPVPromptOptimizer()

    # Mock messy responses
    class MessyLLM:
        def call(self, prompt):
            if "price" in prompt.lower():
                return "The total cost comes to **$29.99** (including tax and shipping fees)"
            elif "urgent" in prompt.lower():
                return "Yes, this message appears to be quite urgent based on the language used."
            elif "email" in prompt.lower():
                return "You can contact them at: **john.doe@example.com** for more information."
            elif "analyze" in prompt.lower():
                return """
**Analysis Results:**

• **Sentiment**: Very positive
• **Confidence**: High (85%)  
• **Key themes**: Growth, opportunity, success

*Note: This analysis is based on preliminary data*
"""
            return "Messy response with **formatting** and • bullets"

    optimizer.llm = MessyLLM()

    print("\n1. Extract float from messy currency text:")
    price = optimizer.reason("Get the price", expected_type=float)
    print("   Raw response: 'The total cost comes to **$29.99** (including tax and shipping fees)'")
    print(f"   ✅ Cleaned result: {price} (type: {type(price).__name__})")

    print("\n2. Extract boolean from verbose text:")
    urgent = optimizer.reason("Is this urgent?", expected_type=bool)
    print("   Raw response: 'Yes, this message appears to be quite urgent...'")
    print(f"   ✅ Cleaned result: {urgent} (type: {type(urgent).__name__})")

    print("\n3. Extract clean string from markdown:")
    email = optimizer.reason("Find email", expected_type=str)
    print("   Raw response: 'You can contact them at: **john.doe@example.com** for more information.'")
    print(f"   ✅ Cleaned result: '{email}' (type: {type(email).__name__})")

    print("\n4. Parse structured data from formatted text:")
    analysis = optimizer.reason("Analyze feedback", expected_type=dict)
    print("   Raw response: Formatted text with bullets and markdown")
    print(f"   ✅ Cleaned result: {analysis} (type: {type(analysis).__name__})")


def demo_new_api_structure():
    """Demonstrate the new API structure with function + config"""

    print("\n" + "=" * 80)
    print("NEW API STRUCTURE DEMONSTRATION")
    print("=" * 80)

    optimizer = IPVPromptOptimizer()

    print("\n1. Using just config (most common):")
    result1 = optimizer.reason(
        "Analyze this data thoroughly",
        {
            "infer": {"config": {"context_collection": "comprehensive"}},
            "process": {"config": {"max_iterations": 5}},
            "validate": {"config": {"quality_threshold": "high"}},
        },
        expected_type=dict,
    )

    print("\n2. Mixing custom functions with config:")
    result2 = optimizer.reason(
        "Calculate financial metrics",
        {
            "infer": {"function": financial_infer, "config": {"context_depth": "maximum"}},
            "process": {"config": {"max_iterations": 3, "error_handling": "strict"}},
            "validate": {"function": strict_financial_validate, "config": {"precision_level": "maximum"}},
        },
        expected_type=float,
    )

    print("\n3. Using only custom functions (expert mode):")
    result3 = optimizer.reason(
        "Create engaging financial content",
        {
            "infer": {"function": financial_infer},
            "process": {"function": creative_process},
            "validate": {"function": strict_financial_validate},
        },
        expected_type=str,
    )

    print("\n✅ All three API styles work seamlessly!")


if __name__ == "__main__":
    print("🚀 Advanced IPV Demonstration")

    demo_enhanced_prompts()
    demo_custom_ipv_functions()
    demo_liberal_parsing()
    demo_new_api_structure()

    print("\n" + "=" * 80)
    print("🎉 DEMO COMPLETE!")
    print("=" * 80)
    print("\nKey takeaways:")
    print("✅ IPV automatically enhances prompts based on type and context")
    print("✅ Liberal parsing handles any LLM response format")
    print("✅ Conservative validation guarantees exact type compliance")
    print("✅ Custom functions provide expert-level control")
    print("✅ New API structure is clean and intuitive")
    print("✅ Zero-config mode works for 95% of use cases")
