#!/usr/bin/env python3
"""
Technical deep-dive example for SmartResearchAgent.

Demonstrates:
- Technical query handling
- Multi-source gathering
- Confidence scoring
- Knowledge gap identification
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent


def main():
    """Run a technical deep-dive research query."""
    print("=" * 80)
    print("SmartResearchAgent - Technical Deep-Dive Example")
    print("=" * 80)
    print()

    # Create agent
    agent = SmartResearchAgent()

    query = "Explain transformer architecture in neural networks"
    print(f"Query: {query}")
    print("-" * 80)
    print()

    # Execute research
    print("🔍 Executing research with visible STAR loop...")
    print()

    result = agent.query(caller_message=query)

    # Display results
    print("\n📊 Research Results:")
    print("=" * 80)

    if "response" in result:
        print(f"\n{result['response']}")

    # Show what the agent would track
    print("\n📈 What SmartResearchAgent tracks:")
    print("-" * 80)
    print("• Strategy selected: TECHNICAL_DEEP_DIVE")
    print("• Sources searched: Academic papers, documentation, technical blogs")
    print("• Confidence dimensions: Verification, Recency, Completeness")
    print("• Knowledge gaps: Identified and explained")
    print("• Follow-up questions: Generated based on gaps")
    print()

    print("\n" + "=" * 80)
    print("✅ Technical research complete!")
    print()


if __name__ == "__main__":
    main()
