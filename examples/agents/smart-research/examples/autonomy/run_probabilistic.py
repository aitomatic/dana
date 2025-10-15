#!/usr/bin/env python3
"""
Interactive example for ProbabilisticResearchAgent using .converse()

Demonstrates:
- Interactive conversational interface
- Real-time STAR loop visibility
- Multi-turn conversation
- Follow-up questions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.probabilistic_research_agent import ProbabilisticResearchAgent


def main():
    """Run an interactive research session."""
    print("=" * 80)
    print("ProbabilisticResearchAgent - Interactive Research Session")
    print("=" * 80)
    print()
    print("This example uses .converse() for an interactive conversation with the agent.")
    print("You'll see the STAR loop in action as the agent researches your question.")
    print()
    print("Type your research question below, or try one of these:")
    print("  - What are the latest advances in quantum computing?")
    print("  - Explain transformer architecture")
    print("  - Compare React vs Vue.js")
    print("  - Tell me about machine learning")
    print()
    print("-" * 80)
    print()

    # Create agent
    agent = ProbabilisticResearchAgent()

    # Get user's initial question
    initial_message = input("Your research question: ").strip()

    if not initial_message:
        initial_message = "What are the latest advances in quantum computing?"
        print(f"Using default: {initial_message}")

    print()
    print("🔍 Starting interactive research session...")
    print("=" * 80)
    print()

    # Start conversational research
    # This will show the full STAR loop and allow multi-turn interaction
    agent.converse(initial_message=initial_message)

    print()
    print("=" * 80)
    print("✅ Interactive session complete!")
    print()
    print("💡 The .converse() method provides:")
    print("   - Full STAR loop visibility")
    print("   - Interactive multi-turn conversation")
    print("   - Real-time agent reasoning")
    print("   - Ability to ask follow-up questions")
    print()


if __name__ == "__main__":
    main()
