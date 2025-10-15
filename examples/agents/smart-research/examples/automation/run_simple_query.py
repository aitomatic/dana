#!/usr/bin/env python3
"""
Simple query example for SmartResearchAgent.

Demonstrates:
- Basic usage
- Magic function interface
- STAR loop visibility
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent


def main():
    """Run a simple research query."""
    print("=" * 80)
    print("SmartResearchAgent - Simple Query Example")
    print("=" * 80)
    print()

    # Create agent
    agent = SmartResearchAgent()

    print("Query: What is quantum computing?")
    print("-" * 80)
    print()

    # Method 1: Programmatic interface
    print("Using programmatic interface (query method):")
    result = agent.query(caller_message="What is quantum computing?")

    # Display results
    print("\n📊 Research Results:")
    print("-" * 80)

    if "response" in result:
        print(f"\n{result['response']}")

    print("\n" + "=" * 80)
    print("✅ Simple query complete!")
    print()

    # Method 2: Magic function interface (commented - for interactive use)
    print("💡 Try the magic function interface:")
    print("   agent.what_is_quantum_computing()")
    print("   agent.explain_machine_learning()")
    print("   agent.compare_python_vs_javascript()")
    print()


if __name__ == "__main__":
    main()
