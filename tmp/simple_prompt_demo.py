#!/usr/bin/env python3
"""
Simple Enhanced Prompt Demo

This shows exactly what enhanced prompts look like.
"""

from prototype_ipv import IPVPromptOptimizer, SandboxContext


def show_enhanced_prompts():
    """Show the actual enhanced prompts that IPV generates"""

    print("=" * 80)
    print("ENHANCED PROMPT EXAMPLES")
    print("=" * 80)

    optimizer = IPVPromptOptimizer()

    test_cases = [("Get the price", float), ("Is this urgent?", bool), ("Find the email", str), ("Analyze the data", dict)]

    for prompt, expected_type in test_cases:
        print("\n" + "=" * 60)
        print(f"PROMPT: '{prompt}' → {expected_type.__name__}")
        print("=" * 60)

        # Create context
        context = SandboxContext(function_name="demo_function")
        options = {"expected_type": expected_type}

        # Run INFER phase to get enhanced context
        enhanced_context = optimizer.default_infer(prompt, context, options)

        # Generate enhanced prompt
        enhanced_prompt = optimizer._generate_enhanced_prompt(prompt, enhanced_context)

        print("\n📝 ORIGINAL:")
        print(f"   '{prompt}'")

        print("\n🧠 CONTEXT DETECTED:")
        print(f"   Domain: {enhanced_context.domain}")
        print(f"   Type: {enhanced_context.expected_type.__name__}")
        print(f"   Reliability: {enhanced_context.reliability.value}")
        print(f"   Precision: {enhanced_context.precision.value}")
        if enhanced_context.examples:
            print(f"   Examples: {enhanced_context.examples}")

        print("\n🚀 ENHANCED PROMPT:")
        print("-" * 50)
        print(enhanced_prompt)
        print("-" * 50)


if __name__ == "__main__":
    print("🔍 IPV Enhanced Prompt Analysis")
    show_enhanced_prompts()
