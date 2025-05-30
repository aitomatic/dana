#!/usr/bin/env python3
"""
Enhanced Prompts Demo

This demo focuses specifically on showing how IPV transforms raw prompts
into optimized versions, demonstrating the prompt enhancement capabilities.
"""

from prototype_ipv import IPVPromptOptimizer


def demo_prompt_transformations():
    """Show how IPV transforms raw prompts into optimized versions"""

    print("🎯 IPV Prompt Enhancement Demo")
    print("=" * 60)
    print("This demo shows how IPV automatically transforms simple prompts")
    print("into optimized versions based on expected return types.\n")

    # Create optimizer with verbose mode to show prompt transformations
    optimizer = IPVPromptOptimizer(verbose=True)

    # Demo 1: Float extraction
    print("🔢 DEMO 1: Price Extraction (float)")
    print("-" * 40)
    result = optimizer.reason("Get the price", expected_type=float)
    print(f"🎯 Final result: {result} (guaranteed {type(result).__name__})\n")

    # Demo 2: Boolean classification
    print("✅ DEMO 2: Urgency Detection (bool)")
    print("-" * 40)
    result = optimizer.reason("Is this urgent?", expected_type=bool)
    print(f"🎯 Final result: {result} (guaranteed {type(result).__name__})\n")

    # Demo 3: Clean text extraction
    print("📝 DEMO 3: Text Summarization (str)")
    print("-" * 40)
    result = optimizer.reason("Summarize this", expected_type=str)
    print(f"🎯 Final result: {result} (guaranteed {type(result).__name__})\n")

    # Demo 4: Structured data extraction
    print("📊 DEMO 4: Data Analysis (dict)")
    print("-" * 40)
    result = optimizer.reason("Analyze the feedback", expected_type=dict)
    print(f"🎯 Final result: {result} (guaranteed {type(result).__name__})\n")

    # Demo 5: Show profile-based optimization
    print("💰 DEMO 5: Financial Analysis with Profile")
    print("-" * 40)
    result = optimizer.reason("Calculate revenue", expected_type=float, config={"profile": "financial"})
    print(f"🎯 Final result: {result} (guaranteed {type(result).__name__})\n")

    print("=" * 60)
    print("🎉 Demo Complete!")
    print(f"📊 Total LLM calls: {optimizer.llm.call_count}")
    print("\n💡 Key Insights:")
    print("• Raw prompts are automatically enhanced based on expected type")
    print("• Format requirements and examples are added automatically")
    print("• LLM responses are parsed liberally but validated conservatively")
    print("• Type compliance is guaranteed regardless of LLM response format")


def show_prompt_comparison():
    """Show side-by-side comparison of raw vs enhanced prompts"""

    print("\n" + "=" * 80)
    print("📋 PROMPT TRANSFORMATION EXAMPLES")
    print("=" * 80)

    examples = [
        {
            "raw": "Get the price",
            "type": "float",
            "enhanced": """Get the price

Requirements:
- Return ONLY the numeric value as a decimal (e.g., 29.99)
- No currency symbols ($, €, etc.)
- No text or explanations
- If no value found, return 0.0

Examples of correct format:
- 29.99
- 1250.00
- 0.99

Context: This is financial data requiring high precision and accuracy.""",
        },
        {
            "raw": "Is this urgent?",
            "type": "bool",
            "enhanced": """Is this urgent?

Requirements:
- Return ONLY true or false
- No explanations or additional text
- Consider urgency indicators like deadlines, emergency language

Examples of correct format:
- true
- false

Context: This requires a clear yes/no decision.""",
        },
        {
            "raw": "Analyze the feedback",
            "type": "dict",
            "enhanced": """Analyze the feedback

Requirements:
- Return ONLY valid JSON format
- Include key analysis dimensions
- No explanations before or after the JSON
- Use consistent key names

Examples of correct format:
- {"sentiment": "positive", "confidence": 0.85}
- {"category": "complaint", "priority": "high"}

Context: This requires structured data analysis.""",
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n📝 EXAMPLE {i}: {example['type']} extraction")
        print("-" * 50)
        print(f"🔸 Raw prompt: '{example['raw']}'")
        print(f"🔹 Expected type: {example['type']}")
        print("⚡ Enhanced prompt:")
        print("┌" + "─" * 48 + "┐")
        for line in example["enhanced"].split("\n"):
            print(f"│ {line:<46} │")
        print("└" + "─" * 48 + "┘")


if __name__ == "__main__":
    demo_prompt_transformations()

    show_comparison = input("\n🤔 Show detailed prompt comparisons? (y/n): ")
    if show_comparison.lower() == "y":
        show_prompt_comparison()
