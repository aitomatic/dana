#!/usr/bin/env python3
"""
Comparative analysis example for SmartResearchAgent.

Demonstrates:
- Comparative query handling
- Multi-perspective gathering
- Synthesis across sources
- Balanced analysis
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent


def main():
    """Run a comparative analysis research query."""
    print("=" * 80)
    print("SmartResearchAgent - Comparative Analysis Example")
    print("=" * 80)
    print()

    # Create agent
    agent = SmartResearchAgent()

    query = "Compare React vs Vue.js in 2024"
    print(f"Query: {query}")
    print("-" * 80)
    print()

    # Execute research
    print("🔍 Executing comparative research...")
    print()
    print("Strategy selected: COMPARATIVE_ANALYSIS")
    print("Gathering from: Reviews, benchmarks, documentation")
    print()

    result = agent.query(caller_message=query)

    # Display results
    print("\n📊 Comparative Analysis Results:")
    print("=" * 80)

    if "response" in result:
        print(f"\n{result['response']}")

    # Show comparative analysis features
    print("\n💡 Comparative Analysis Features:")
    print("-" * 80)
    print("• Multi-perspective gathering (both React and Vue sources)")
    print("• Cross-referenced benchmarks and performance metrics")
    print("• Community sentiment analysis")
    print("• Use case recommendations")
    print("• Confidence per dimension (performance, ecosystem, learning curve)")
    print()

    print("\n" + "=" * 80)
    print("✅ Comparative analysis complete!")
    print()


if __name__ == "__main__":
    main()
