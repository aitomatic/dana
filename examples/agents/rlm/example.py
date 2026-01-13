#!/usr/bin/env python3
"""
RLM (Recursive Language Model) Example

Demonstrates querying large documents using the RLM pattern where the LLM
writes Python code to explore the document programmatically.

Usage:
    cd dana_agent
    uv run python ../examples/agents/rlm/example.py
"""

from pathlib import Path

from dana.common.resource import RLMResource


def main():
    """Run RLM resource demo."""
    print("=" * 60)
    print("RLM (Recursive Language Model) Demo")
    print("=" * 60)
    print()

    # Get path to sample context
    example_dir = Path(__file__).parent
    sample_context = example_dir / "sample_context.md"

    # Create RLM resource with a temporary context file
    # Default uses Anthropic Claude, but can also use "openai", "groq", etc.
    context_file = example_dir / "demo_context.md"
    data = RLMResource(file=str(context_file), auto_register=False)

    # Load the sample context
    print("Loading sample codebase documentation...")
    result = data.load_file(str(sample_context))
    print(f"  {result}")
    print()

    # Query 1: Find authentication functions
    print("-" * 60)
    print("Query 1: What functions handle authentication?")
    print("-" * 60)
    print()
    print("Watch: LLM writes Python to search, finds answer iteratively...")
    print()

    answer = data.query("What functions handle authentication?")
    print(f"Answer: {answer}")
    print()

    # Query 2: Summarize error handling patterns
    print("-" * 60)
    print("Query 2: Summarize all error handling patterns")
    print("-" * 60)
    print()
    print("Watch: LLM uses llm_query() for semantic summarization...")
    print()

    answer = data.query("Summarize all error handling patterns in this codebase")
    print(f"Answer: {answer}")
    print()

    # Query 3: Find specific code
    print("-" * 60)
    print("Query 3: How is password hashing implemented?")
    print("-" * 60)
    print()

    answer = data.query("How is password hashing implemented?")
    print(f"Answer: {answer}")
    print()

    # Cleanup
    if context_file.exists():
        context_file.unlink()

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
