"""
Example usage of WebResearchAgent - Prompt-Driven Architecture.

The agent is now configured entirely through system prompts and uses
natural language for all interactions.
"""

import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from dana.lib.agents.web_research import WebResearchAgent


def example_natural_language_query():
    """
    Example: Natural language query (the primary interface).

    The agent's LLM reads the system prompt and decides which workflow to use.
    """
    print("\n" + "=" * 60)
    print("Example 1: Natural Language Query")
    print("=" * 60)

    # Create agent
    agent = WebResearchAgent()

    # Natural language query - agent decides workflow
    # result = agent.query(message="What is this week's headline news in tech?")
    # result = agent.query(message="What’s the best price currently for a new Macbook Pro 14?")
    result = agent.query(message="Research China’s energy generation capacity 2020-2050. Provide a table of annual values.")

    # Check result
    if not result.get("trace_outputs", {}).get("EXIT_STAR_LOOP_FLAG"):
        print("\n❌ Query failed or incomplete")
        return

    response = result.get("trace_outputs", {}).get("response", "")
    print("\n✅ Query successful!")
    print("\nResponse preview (first 500 chars):")
    print(response[:500] + "..." if len(response) > 500 else response)


def example_url_analysis():
    """
    Example: URL analysis through natural language.

    The agent sees the URL in the message and calls single_source_deep_dive workflow.
    """
    print("\n" + "=" * 60)
    print("Example 2: URL Analysis")
    print("=" * 60)

    agent = WebResearchAgent()

    # Natural language with URL - agent extracts URL and calls appropriate workflow
    result = agent.query(message="Analyze this documentation page: https://docs.python.org/3/library/asyncio.html")

    if not result.get("trace_outputs", {}).get("EXIT_STAR_LOOP_FLAG"):
        print("\n❌ Query failed or incomplete")
        return

    response = result.get("trace_outputs", {}).get("response", "")
    print("\n✅ Analysis successful!")
    print("\nResponse preview (first 500 chars):")
    print(response[:500] + "..." if len(response) > 500 else response)


def example_structured_data():
    """
    Example: Structured data extraction through natural language.

    The agent detects "top N" pattern and calls structured_data_navigation workflow.
    """
    print("\n" + "=" * 60)
    print("Example 3: Structured Data Extraction")
    print("=" * 60)

    agent = WebResearchAgent()

    # Natural language "top N" pattern - agent calls structured_data_navigation
    result = agent.query(message="Find the top 5 most popular Python packages")

    if not result.get("trace_outputs", {}).get("EXIT_STAR_LOOP_FLAG"):
        print("\n❌ Query failed or incomplete")
        return

    response = result.get("trace_outputs", {}).get("response", "")
    print("\n✅ Data extraction successful!")
    print("\nResponse preview (first 500 chars):")
    print(response[:500] + "..." if len(response) > 500 else response)


def example_check_prompts():
    """
    Example: Inspect the agent's system prompts.

    Shows how the agent is configured through prompts, not code.
    """
    print("\n" + "=" * 60)
    print("Example 4: System Prompt Configuration")
    print("=" * 60)

    agent = WebResearchAgent()

    print("\nPublic Description (what users/agents see):")
    print("-" * 60)
    print(agent.public_description)

    print("\n\nPrivate Identity (first 300 chars):")
    print("-" * 60)
    print(agent.private_identity[:300] + "...")

    print("\n\nSystem Prompt Stats:")
    print("-" * 60)
    print(f"Total system prompt length: {len(agent.system_prompt)} characters")
    print(f"Contains workflow guidelines: {'<WORKFLOW_GUIDELINES>' in agent.system_prompt}")
    print(f"Contains response guidelines: {'<RESPONSE_GUIDELINES>' in agent.system_prompt}")


def main():
    """Run examples."""
    print("\n" + "=" * 70)
    print("WebResearchAgent - Prompt-Driven Examples")
    print("=" * 70)

    # Verify Google API credentials are set
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
        print("\n⚠️  WARNING: Google API credentials not set")
        print("Set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables")
        print("See README.md for setup instructions")
        print("\nSkipping live examples (will show system prompt example only)")
        print()
        example_check_prompts()
        return

    # Show prompt configuration first
    example_check_prompts()

    print("\n" + "=" * 70)
    print("NOTE: The following examples require network and LLM access")
    print("=" * 70)

    # Run live examples
    try:
        example_natural_language_query()
        # example_url_analysis()
        # example_structured_data()
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("1. Agent is configured entirely through system prompts (docstring)")
    print("2. Single natural language interface: agent.query(message=...)")
    print("3. LLM reads prompts and decides which workflow to call")
    print("4. Minimal Python code (~200 lines vs ~450 before)")
    print("5. Easy to modify behavior by editing prompts, not code")
    print("=" * 70)


if __name__ == "__main__":
    main()
