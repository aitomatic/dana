"""
Demo script for Study Review Application.

This demonstrates the simplified multi-agent study session with:
1. CoordinatorAgent orchestrates the conversation directly
2. FileSearchResource loads study materials
3. QuizMasterAgent generates quizzes

Usage:
    python demo.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.coordinator_agent import CoordinatorAgent


# Disable LLM debug logging
import logging
import structlog

# Configure logging to suppress debug messages
logging.basicConfig(level=logging.WARNING, format="%(message)s")

# Configure structlog to suppress debug logs
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
)


def main():
    # Initialize coordinator (which initializes all specialist agents)
    coordinator = CoordinatorAgent(agent_id="study-coordinator", llm_provider="openai")

    try:
        # Start the interactive conversation
        coordinator.converse(initial_message="Help me study the refrigerator design materials")
        # coordinator.converse()

    except KeyboardInterrupt:
        print("\n\n👋 Study session interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Study session failed: {str(e)}")
        print("💡 Make sure you have the required dependencies installed:")
        print("   pip install -e ../../../dana_agent")
        print("   export OPENAI_API_KEY=your_api_key")


if __name__ == "__main__":
    main()
