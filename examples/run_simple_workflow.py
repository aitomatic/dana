#!/usr/bin/env python3
"""Example script to run a simple DXA workflow."""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path to import dxa
sys.path.append(str(Path(__file__).parent.parent))

from dxa.execution.system import run_workflow
from dxa.execution.llm import LLMService

def main():
    """Run the simple workflow example."""
    # Get the path to the workflow YAML
    workflow_path = os.path.join(os.path.dirname(__file__), "simple_workflow.yaml")
    
    # Create LLM service (you can add your API key here if needed)
    llm_service = LLMService(api_key=None)
    
    print("Running simple workflow...")
    print(f"Using workflow definition from: {workflow_path}")
    
    # Run the workflow
    results, context = run_workflow(workflow_path, llm_service)
    
    # Print results
    print("\nWorkflow Results:")
    print("-" * 50)
    for node_id, result in context.workflow_results.items():
        print(f"\nNode: {node_id}")
        print(f"Results: {result}")
    
    print("\nWorkflow execution completed!")

if __name__ == "__main__":
    main() 