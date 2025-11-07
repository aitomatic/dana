#!/usr/bin/env python3
"""Minimal Honeywell Agent - Uses STAR execution pattern."""

import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "dana_agent")
)

from dana.core.agent.star_agent import STARAgent  # noqa: E402


class HoneywellAgent(STARAgent):
    """Honeywell Systems Expert Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            agent_id="honeywell-agent",
            llm_provider="openai",
            model="gpt-4.1-mini",
            **kwargs
        )


if __name__ == "__main__":
    agent = HoneywellAgent()
    result = agent.query(caller_message="What is your name?")

    # Extract the final response from timeline
    if result and "response" in result:
        print(result["response"])
    elif result and "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("No response generated")
