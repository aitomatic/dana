#!/usr/bin/env python3
"""
Tutorial 02: DANA vs Traditional Python LLM Setup

🎯 LEARNING OBJECTIVES:
- See the dramatic difference in code complexity
- Understand setup time: minutes vs seconds
- Compare error handling approaches

⚡ QUICK START:
Run this to see side-by-side comparison!

💡 WHY THIS MATTERS:
DANA eliminates 90% of LLM integration complexity
"""

from pathlib import Path
import sys


# Add Dana to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana_lang.dana import dana


def show_traditional_approach():
    """Show what traditional Python LLM setup looks like"""
    print("❌ TRADITIONAL PYTHON APPROACH")
    print("=" * 40)
    print()

    print("📝 Setup Required (15+ lines):")
    print("""
    import openai
    import os
    from typing import Optional
    import time

    # Setup client
    client = openai.OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    def analyze_data(data: dict) -> Optional[str]:
        try:
            prompt = f"Analyze: {data}"
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except openai.APIError as e:
            print(f"API Error: {e}")
            return None
        except openai.RateLimitError:
            time.sleep(60)  # Wait and retry
            return analyze_data(data)
        except Exception as e:
            print(f"Unknown error: {e}")
            return None

    # Finally use it:
    result = analyze_data({"sales": 100000})
    """)

    print("🚨 Problems:")
    print("  • API key management")
    print("  • Error handling complexity")
    print("  • Rate limiting logic")
    print("  • Model configuration")
    print("  • Response parsing")
    print("  • Retry mechanisms")
    print()


def show_dana_approach():
    """Show DANA's simple approach"""
    print("✅ DANA APPROACH")
    print("=" * 40)
    print()

    print("📝 Setup Required (1 line):")
    print("""
    from dana_lang.dana import dana

    # That's it! Use immediately:
    result = dana.reason("Analyze: {sales: 100000}")
    """)

    print("✨ Benefits:")
    print("  • Zero setup time")
    print("  • Built-in error handling")
    print("  • Automatic retries")
    print("  • No API key exposure")
    print("  • Works immediately")
    print("  • Consistent responses")
    print()


def live_comparison():
    """Show both approaches working on same problem"""
    print("🔥 LIVE COMPARISON")
    print("=" * 40)
    print()

    # Same business problem
    business_data = {"revenue": 75000, "expenses": 60000, "growth": "12%"}

    print(f"📊 Problem: Analyze {business_data}")
    print()

    print("❌ Traditional: Would require 15+ lines of setup...")
    print("   (API keys, error handling, client config, etc.)")
    print()

    print("✅ DANA: One line solution:")
    print("   dana.reason(f'Analyze business: {business_data}')")
    print()

    # Actually run DANA version
    print("🚀 DANA Result:")
    result = dana.reason(f"Analyze business performance: {business_data}. Give brief assessment.")
    print(f"   {result}")
    print()


def complexity_breakdown():
    """Show complexity comparison"""
    print("📊 COMPLEXITY BREAKDOWN")
    print("=" * 40)
    print()

    comparison = [
        ("Setup Time", "5-10 minutes", "5 seconds"),
        ("Lines of Code", "15-25 lines", "1 line"),
        ("Dependencies", "openai, typing, os", "dana.dana"),
        ("Error Handling", "Manual try/catch", "Built-in"),
        ("API Keys", "Manual management", "Automatic"),
        ("Rate Limits", "Manual retry logic", "Handled automatically"),
        ("Getting Started", "Read docs, setup", "Just use it"),
    ]

    print(f"{'Aspect':<15} {'Traditional':<20} {'DANA':<15}")
    print("-" * 50)
    for aspect, traditional, dana_val in comparison:
        print(f"{aspect:<15} {traditional:<20} {dana_val:<15}")
    print()


def main():
    """Run the comparison"""
    print("⚡ DANA vs Traditional Python LLM Setup")
    print("=" * 50)
    print()

    show_traditional_approach()
    show_dana_approach()
    live_comparison()
    complexity_breakdown()

    print("🎯 CONCLUSION:")
    print("  DANA reduces LLM integration from 15+ lines to 1 line")
    print("  From 10 minutes setup to instant use")
    print("  From complex error handling to zero-config")
    print()
    print("🎯 NEXT: Try 03_importing_dana_modules.py to learn module imports!")


if __name__ == "__main__":
    main()
