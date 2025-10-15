#!/usr/bin/env python3
"""
Demonstration of visible thinking with ThoughtLogger.

This shows how to make agent thinking transparent using the Notifiable pattern.
You'll see the STAR loop in action - every phase of agent reasoning.

Key insight: This is what makes Dana agents transparent instead of black-box AI.
"""

import sys
import os
import logging
import structlog

# Suppress noisy logging
logging.basicConfig(level=logging.ERROR, force=True)
logging.getLogger().setLevel(logging.ERROR)

# Suppress structlog as well
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from dana.apps.dana.thought_logger import ThoughtLogger
from agents.smart_research_agent import SmartResearchAgent


def demo_with_visible_thinking():
    """Run a query with visible thinking enabled."""
    print("=" * 80)
    print("VISIBLE THINKING DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demo shows the complete STAR loop in real-time:")
    print()
    print("  👁️  SEE     - Agent perceives the user's query AND tool results")
    print("  💭 THINK   - Agent reasons about what to do (shown in gray)")
    print("  ⚡ ACT     - Agent executes workflows and resources")
    print("  🔄 REFLECT - Agent learns from the interaction")
    print()
    print("Notice the SEE phase appears multiple times:")
    print("  - First: When perceiving your query")
    print("  - Then: When perceiving each tool result")
    print()
    print("The faded gray text shows the agent's internal thinking.")
    print("This transparency is a key feature of the Dana framework!")
    print()
    print("=" * 80)
    print()

    # Create agent
    agent = SmartResearchAgent()

    # Attach ThoughtLogger to show thinking in faded color
    thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
    agent.with_notifiable(thought_logger)

    # Test query
    query = "What is quantum computing?"
    print(f"Query: {query}")
    print("-" * 80)
    print()

    # Run the query - you'll see thinking progress in gray
    result = agent.query(caller_message=query)

    print()
    print("-" * 80)
    print()
    print("✅ Query complete!")
    print()
    print("WHAT YOU JUST SAW:")
    print("  - Every STAR loop phase was visible")
    print("  - Workflow calls were shown in real-time")
    print("  - Agent thinking was transparent (not a black box)")
    print()
    print("TRY IT YOURSELF:")
    print("  python examples/autonomy/run_deterministic_with_thinking.py")
    print()


def demo_without_visible_thinking():
    """Run a query without visible thinking for comparison."""
    print()
    print("=" * 80)
    print("COMPARISON: WITHOUT VISIBLE THINKING")
    print("=" * 80)
    print()
    print("Now running the SAME query WITHOUT ThoughtLogger.")
    print("Notice the difference - you only see the final result.")
    print()
    print("=" * 80)
    print()

    # Create agent WITHOUT ThoughtLogger
    agent = SmartResearchAgent()

    # Test query
    query = "What is quantum computing?"
    print(f"Query: {query}")
    print("-" * 80)
    print()

    # Run the query - no thinking visible
    result = agent.query(caller_message=query)

    print()
    print("-" * 80)
    print()
    print("KEY DIFFERENCE:")
    print("  ❌ Without ThoughtLogger: Black box - you only see final output")
    print("  ✅ With ThoughtLogger: Transparent - you see every reasoning step")
    print()


def main():
    """Run the demonstration."""
    # First demo: with visible thinking
    demo_with_visible_thinking()

    # Ask user if they want to see the comparison
    print()
    user_input = input("Press Enter to see comparison without visible thinking (or 'q' to quit)...")
    if user_input.lower() != 'q':
        demo_without_visible_thinking()

    print()
    print("=" * 80)
    print("LEARN MORE:")
    print("  - Try: python examples/autonomy/run_deterministic_with_thinking.py")
    print("  - Try: python examples/autonomy/run_probabilistic_with_thinking.py")
    print("  - Read: examples/autonomy/README.md (Visible Thinking section)")
    print("=" * 80)


if __name__ == "__main__":
    main()
