#!/usr/bin/env python3
"""
Tutorial 07: DANA AI Reasoning Guide
====================================

Learn how to use DANA's AI reasoning through imported modules.
Perfect for AI Engineers who want to encapsulate AI logic in reusable functions.

📖 What You'll Learn:
- Use reason() inside DANA functions
- Import AI-powered functions from DANA modules
- Build reusable AI components
- Compare module approach vs direct dana.reason()

⚡ Quick Start: Run this file to see AI reasoning in action!
"""

import sys
from pathlib import Path

# Add the OpenDXA path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from opendxa.dana import dana


def demo_sentiment_analysis():
    """Demo 1: AI sentiment analysis through imported DANA function."""
    print("📋 Demo 1: Sentiment Analysis")
    print("-" * 40)

    dana.enable_module_imports()
    try:
        import ai_reasoning

        # ✅ Test different sentiment examples
        test_texts = [
            "I absolutely love this new product!",
            "This is terrible, worst experience ever.",
            "It's okay, nothing special but works fine.",
        ]

        print("🧠 AI Sentiment Analysis:")
        for text in test_texts:
            sentiment = ai_reasoning.analyze_sentiment(text)
            print(f"   Text: '{text}'")
            print(f"   Sentiment: {sentiment}\n")

    finally:
        dana.disable_module_imports()

    print("✅ Sentiment analysis works great!\n")


def demo_intelligent_recommendations():
    """Demo 2: AI-powered personalized recommendations."""
    print("📋 Demo 2: Intelligent Recommendations")
    print("-" * 40)

    dana.enable_module_imports()
    try:
        import ai_reasoning

        # ✅ Different user profiles for testing
        user_profiles = [
            {"age": 25, "interests": ["tech", "gaming"], "experience": "beginner"},
            {"age": 35, "interests": ["business", "finance"], "experience": "expert"},
            {"age": 28, "interests": ["health", "fitness"], "experience": "intermediate"},
        ]

        print("🎯 Personalized Recommendations:")
        for i, profile in enumerate(user_profiles, 1):
            recommendations = ai_reasoning.intelligent_recommendation(profile)

            print(f"   User {i}: {profile}")
            print(f"   Recommendations: {recommendations['recommendations']}")
            print(f"   Confidence: {recommendations['confidence_score']}\n")

    finally:
        dana.disable_module_imports()

    print("✅ AI recommendations are personalized!\n")


def compare_approaches():
    """Demo 3: Compare module approach vs direct dana.reason()."""
    print("📋 Demo 3: Module vs Direct Approach")
    print("-" * 40)

    text = "This product is amazing, highly recommended!"

    # ✅ Approach 1: Through DANA module (encapsulated)
    print("🔧 Approach 1: Through DANA Module")
    dana.enable_module_imports()
    try:
        import ai_reasoning

        module_result = ai_reasoning.analyze_sentiment(text)
        print(f"   Module result: {module_result}")
    finally:
        dana.disable_module_imports()

    # ✅ Approach 2: Direct dana.reason() call
    print("\n🔧 Approach 2: Direct dana.reason()")
    prompt = f"Analyze the sentiment of this text: '{text}'. Respond with just: positive, negative, or neutral"
    direct_result = dana.reason(prompt)
    print(f"   Direct result: {direct_result}")

    print("\n💡 Both approaches work, but modules are more reusable!")


def benefits_explanation():
    """Explain why DANA module-based AI reasoning is valuable."""
    print("💡 Why Module-Based AI Reasoning Matters")
    print("-" * 50)

    print("""
🎯 Key Benefits:

1. **Reusability**: Write AI logic once, use everywhere
   - Define reason() functions in DANA modules
   - Import and use across multiple Python scripts
   - Share AI components across teams

2. **Encapsulation**: Hide complexity behind clean APIs
   - Complex prompts hidden in DANA functions
   - Simple function calls from Python
   - Easier to test and maintain

3. **Type Safety**: Strong typing for AI functions
   - Input/output types clearly defined
   - Catch errors at import time
    """)


def quick_reference():
    """Quick reference for module-based AI reasoning."""
    print("📚 Quick Reference")
    print("-" * 20)

    print("""
🔧 Module-Based AI Pattern:

# In DANA module (ai_utils.na):
def analyze_text(text: str) -> str:
    return reason(f"Analyze this: {text}")

export analyze_text

# In Python script:
dana.enable_module_imports()
import ai_utils
result = ai_utils.analyze_text("Hello world")

# vs Direct approach:
result = dana.reason("Analyze this: Hello world")
    """)


def main():
    """Run the complete AI reasoning tutorial."""
    print("🧠 DANA AI Reasoning Tutorial")
    print("=" * 50)
    print("Learn how to use AI through imported DANA modules\n")

    # Run demos
    demo_sentiment_analysis()
    demo_intelligent_recommendations()
    compare_approaches()
    benefits_explanation()
    quick_reference()

    print("🎉 Tutorial Complete!")
    print("\n📖 What You Learned:")
    print("  ✅ Using reason() inside DANA functions")
    print("  ✅ Importing AI-powered functions from modules")
    print("  ✅ Building reusable AI components")
    print("  ✅ Module approach vs direct dana.reason()")

    print("\n🔗 Next Steps:")
    print("  📝 Create your own AI reasoning modules")
    print("  🧠 Build domain-specific AI functions")


if __name__ == "__main__":
    main()
