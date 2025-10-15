#!/usr/bin/env python3
"""
Run deterministic research agent with visible thinking progress.

This demonstrates the ThoughtLogger which shows the STAR loop in action:
- 👁️  SEE: Agent perceives the user's query
- 💭 THINK: Agent reasons and decides which workflows to call
- ⚡ ACT: Agent executes workflows
- 🔄 REFLECT: Agent learns from the interaction

All thinking is shown in faded color and updates in real-time.
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


def main():
    """Run interactive research session with visible thinking."""
    print("=" * 80)
    print("DETERMINISTIC RESEARCH AGENT - WITH VISIBLE THINKING")
    print("=" * 80)
    print()
    print("This demo shows the complete STAR loop in action:")
    print("  👁️  SEE    - Agent perceives your query and tool results")
    print("  💭 THINK  - Agent reasons about what to do (shown in gray)")
    print("  ⚡ ACT    - Agent executes workflows")
    print("  🔄 REFLECT - Agent learns from the interaction")
    print()
    print("Watch for multiple SEE phases - initial query and perceiving tool results!")
    print("The gray text shows the agent's internal thought process.")
    print("This makes the AI transparent - you can see exactly what it's doing!")
    print()
    print("Try queries like:")
    print("  - What is quantum computing?")
    print("  - Compare Python vs JavaScript")
    print("  - What are the main approaches to nuclear fusion?")
    print()
    print("=" * 80)
    print()

    # Create agent with ThoughtLogger
    agent = SmartResearchAgent()

    # Attach ThoughtLogger to show thinking in faded color
    thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
    agent.with_notifiable(thought_logger)

    # Start interactive conversation
    agent.converse()


if __name__ == "__main__":
    main()
