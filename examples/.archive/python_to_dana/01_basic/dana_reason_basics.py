#!/usr/bin/env python3
"""
Tutorial 01: DANA reason() Basics - Your First AI Integration

🎯 LEARNING OBJECTIVES:
- Use dana.reason() for instant AI capabilities
- Understand the one-line AI integration approach
- See practical examples for real-world scenarios

⚡ QUICK START:
Just run this file to see AI integration in action!

💡 WHY THIS MATTERS:
Traditional Python LLM setup = 15+ lines of boilerplate
DANA approach = 1 line, zero setup
"""

import sys
from pathlib import Path

# Add Dana to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana.dana import dana


def example_1_simple_question():
    """Example 1: Ask AI a simple question"""
    print("📝 Example 1: Simple AI Question")
    print("Code: dana.reason('What is 15% of 200?')")

    # One line - that's it!
    answer = dana.reason("What is 15% of 200?")
    print(f"Result: {answer}")
    print()


def example_2_data_analysis():
    """Example 2: Analyze data with AI"""
    print("📊 Example 2: Data Analysis")

    # Your data
    data = {"revenue": 50000, "costs": 35000, "month": "January"}

    print(f"Data: {data}")
    print("Code: dana.reason(f'Analyze this business data: {data}. Is this good?')")

    # AI analyzes your data
    analysis = dana.reason(f"Analyze this business data: {data}. Is this good?")
    print(f"AI Analysis: {analysis}")
    print()


def example_3_decision_making():
    """Example 3: AI-powered decision making"""
    print("🤔 Example 3: Decision Making")

    # Real scenario
    situation = {"team_size": 5, "deadline": "2 weeks", "complexity": "high", "budget": "limited"}

    print(f"Situation: {situation}")
    print("Code: dana.reason(f'Given {situation}, should we hire more developers? Yes/no with reason.')")

    # Get AI recommendation
    decision = dana.reason(f"Given {situation}, should we hire more developers? Yes/no with reason.")
    print(f"AI Decision: {decision}")
    print()


def example_4_classification():
    """Example 4: Smart classification"""
    print("🏷️ Example 4: Smart Classification")

    # Items to categorize
    items = ["laptop", "coffee", "notebook", "headphones", "pen"]

    print(f"Items: {items}")
    print("Code: dana.reason(f'Group these items: {items}. Return categories.')")

    # AI categorizes automatically
    categories = dana.reason(f"Group these items: {items}. Return categories.")
    print(f"AI Categories: {categories}")
    print()


def main():
    """Run all examples"""
    print("🚀 DANA reason() Tutorial - AI in One Line!")
    print("=" * 50)
    print()

    # Run examples
    example_1_simple_question()
    example_2_data_analysis()
    example_3_decision_making()
    example_4_classification()

    print("✨ KEY TAKEAWAYS:")
    print("  ✅ No LLM client setup needed")
    print("  ✅ No API keys in your code")
    print("  ✅ No error handling boilerplate")
    print("  ✅ Works with any data type")
    print("  ✅ Instant AI capabilities in Python")
    print()
    print("🎯 NEXT: Try 02_reason_vs_traditional.py to see the comparison!")


if __name__ == "__main__":
    main()
