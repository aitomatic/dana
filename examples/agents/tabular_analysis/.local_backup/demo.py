"""
Demo script for TabularAnalysisAgent.

This demonstrates the agent using the MetadataExtractorResource to analyze
Excel and CSV files and provide recommendations.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.tabular_analysis_agent import TabularAnalysisAgent


def main():
    print("=" * 80)
    print("TabularAnalysisAgent Demo")
    print("=" * 80)
    print()

    # Initialize agent with dataset directory
    dataset_dir = Path(__file__).parent / "dataset"

    print("🤖 Initializing agent...")
    print(f"📁 Workspace: {dataset_dir}")
    print()

    agent = TabularAnalysisAgent(workspace_root=str(dataset_dir), model="gpt-4o-mini")

    print("Agent initialized successfully!")
    print()
    print("Available files in dataset:")
    for f in dataset_dir.iterdir():
        if f.suffix in [".csv", ".xlsx", ".xls"]:
            print(f"  - {f.name}")
    print()

    # Example query
    print("=" * 80)
    print("Example Query")
    print("=" * 80)
    query = "I need to analyze data about states and their revenues. Which file should I use?"
    print(f"\nUser: {query}")
    print("\nAgent is analyzing...")
    print("-" * 80)

    # The agent will:
    # 1. Extract metadata from relevant files
    # 2. Analyze column names and types
    # 3. Suggest which file to use based on the query

    response = agent.converse(query)
    print()


if __name__ == "__main__":
    main()
