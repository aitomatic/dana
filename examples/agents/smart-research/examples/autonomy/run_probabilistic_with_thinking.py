#!/usr/bin/env python3
"""
Run probabilistic research agent with visible thinking progress.

This demonstrates:
1. The STAR loop in real-time (SEE → THINK → ACT → REFLECT)
2. How the LLM decides autonomously (vs workflow orchestration)
3. That thinking may vary each run (probabilistic behavior)

Compare this to run_deterministic_with_thinking.py to see the difference
between LLM autonomy and workflow control.
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
from agents.probabilistic_research_agent import ProbabilisticResearchAgent


def main():
    """Run interactive research session with visible thinking."""
    print("=" * 80)
    print("PROBABILISTIC RESEARCH AGENT - WITH VISIBLE THINKING")
    print("=" * 80)
    print()
    print("This demo shows the complete STAR loop with LLM autonomy:")
    print("  👁️  SEE    - Agent perceives your query and tool results")
    print("  💭 THINK  - LLM decides what to do (shown in gray)")
    print("  ⚡ ACT    - LLM may or may not use available resources")
    print("  🔄 REFLECT - Agent learns from the interaction")
    print()
    print("Watch for multiple SEE phases as the agent perceives and processes!")
    print()
    print("KEY DIFFERENCE from deterministic:")
    print("  🔧 Deterministic: Workflows CONTROL what happens")
    print("  🎲 Probabilistic: LLM DECIDES what to do")
    print()
    print("The LLM has resources available but chooses when/how to use them.")
    print("Run the same query multiple times - you may see different behavior!")
    print()
    print("Try queries like:")
    print("  - What is quantum computing?")
    print("  - Compare Python vs JavaScript")
    print()
    print("=" * 80)
    print()

    # Create agent with ThoughtLogger
    agent = ProbabilisticResearchAgent()

    # Attach ThoughtLogger to show thinking in faded color
    thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
    agent.with_notifiable(thought_logger)

    # Start interactive conversation
    agent.converse()


if __name__ == "__main__":
    main()
