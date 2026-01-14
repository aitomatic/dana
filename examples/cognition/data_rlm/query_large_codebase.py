"""
Demo: Querying a large codebase with RLM.

This example demonstrates how RLMResource allows querying documents that are
too large to fit in the context window. The LLM writes Python code to explore
the document programmatically.

Run: python examples/cognition/data_rlm/query_large_codebase.py
"""

import os
import sys
from pathlib import Path

# Add dana_agent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "dana_agent"))

from dana.common.resource.rlm_resource import RLMResource


def main():
    # Create a temporary context file
    context_file = Path(__file__).parent / "context_temp.md"

    # Load the sample codebase
    sample_codebase = Path(__file__).parent / "sample_codebase.md"

    print("=" * 60)
    print("RLM Demo: Querying a Large Codebase")
    print("=" * 60)
    print()

    # Create the RLM resource (using OpenAI)
    print("Creating RLMResource...")
    data = RLMResource(
        file=str(context_file),
        llm_provider="openai",
        llm_model="gpt-4o",
        auto_register=False,
    )

    # Load the sample codebase into context
    print(f"Loading sample codebase from {sample_codebase.name}...")
    result = data.load_file(str(sample_codebase))
    print(f"  {result}")
    print()

    # Query the codebase
    question = "What functions handle authentication?"
    print(f"Query: {question}")
    print("-" * 40)
    print("LLM is writing Python code to explore the codebase...")
    print()

    answer = data.query(question)

    print("-" * 40)
    print(f"Answer: {answer}")
    print()

    # Cleanup
    if context_file.exists():
        os.remove(context_file)
        print("(Cleaned up temporary context file)")


if __name__ == "__main__":
    main()
