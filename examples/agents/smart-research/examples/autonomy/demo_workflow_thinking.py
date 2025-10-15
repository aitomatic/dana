#!/usr/bin/env python3
"""
Demonstration of workflow thinking progress with ThoughtLogger.

This shows how workflows broadcast their internal progress, making
complex multi-step processes completely transparent.
"""

import sys
import os
import logging
import structlog

# Suppress noisy logging
logging.basicConfig(level=logging.ERROR, force=True)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from dana.apps.dana.thought_logger import ThoughtLogger
from agents.smart_research_agent import SmartResearchAgent


def main():
    """Demonstrate workflow thinking progress."""
    print("=" * 80)
    print("WORKFLOW THINKING DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demo shows how workflows broadcast their internal progress.")
    print("Watch for these workflow phases:")
    print()
    print("  ResearchStrategyWorkflow:")
    print("    🔧 START      - Analyzing query...")
    print("    🔍 CLASSIFY   - Keyword matching or LLM classification")
    print("    ✅ COMPLETE   - Strategy selected with confidence")
    print()
    print("  SynthesisWorkflow:")
    print("    🔧 START      - Starting synthesis...")
    print("    📄 EXTRACT    - Extracting key findings")
    print("    🏷️  THEMES     - Identifying themes")
    print("    📝 OVERVIEW   - Generating overview")
    print("    🔍 GAPS       - Detecting knowledge gaps")
    print("    📊 CONFIDENCE - Calculating confidence scores")
    print("    ✅ COMPLETE   - Synthesis complete")
    print()
    print("All workflow thinking appears in faded gray - transparent reasoning!")
    print()
    print("=" * 80)
    print()

    # Create agent with ThoughtLogger
    agent = SmartResearchAgent()
    thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
    agent.with_notifiable(thought_logger)

    # Run a simple query to see workflow thinking
    query = "What is quantum computing?"
    print(f"Query: {query}")
    print("-" * 80)
    print()

    result = agent.query(caller_message=query)

    print()
    print("-" * 80)
    print()
    print("✅ Query complete!")
    print()
    print("WHAT YOU JUST SAW:")
    print("  - Agent STAR loop (SEE, THINK, ACT, REFLECT)")
    print("  - Workflow internal thinking at each step")
    print("  - Complete transparency into multi-step processes")
    print()
    print("This is how Dana makes AI transparent instead of a black box!")
    print()
    print("=" * 80)
    print()
    print("TRY MORE:")
    print("  python examples/autonomy/run_deterministic_with_thinking.py")
    print("  python examples/autonomy/demo_visible_thinking.py")
    print()


if __name__ == "__main__":
    main()
