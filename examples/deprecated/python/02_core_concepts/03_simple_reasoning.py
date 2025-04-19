"""Basic Reasoning Pattern Example

This example demonstrates how to create and inspect a basic reasoning pattern in the DXA framework.
Reasoning patterns represent the HOW layer of execution, responsible for the detailed implementation
of individual tasks.

Key concepts:
- Reasoning creation using ReasoningFactory
- Reasoning structure and components
- Inspecting reasoning nodes and metadata

Learning path: Core Concepts
Complexity: Intermediate

Prerequisites:
- None

Related examples:
- ../planning/simple_plan.py: Basic planning patterns
- ../workflow/qa_approaches.py: Different approaches to question answering
"""

from opendxa.execution import ReasoningFactory
from opendxa.execution.execution_types import Objective

def main():
    """Create and inspect a basic reasoning pattern.
    
    This function demonstrates:
    1. Defining an objective for reasoning
    2. Creating a reasoning pattern from a default configuration
    3. Inspecting the reasoning structure and metadata
    
    The reasoning pattern typically consists of:
    - START node: Entry point for execution
    - Task nodes: Detailed implementation steps
    - END node: Exit point for execution
    
    Returns:
        None: This function prints the reasoning structure but doesn't return a value
    """
    # Define the objective - this is the task that needs to be reasoned about
    objective = "Solve the equation: 2x + 5 = 15"
    
    # Create reasoning from default config
    # This loads a predefined reasoning pattern and applies it to our objective
    reasoning = ReasoningFactory.create_from_config(
        "default",
        objective=Objective(objective)
    )
    
    # Print reasoning information
    # The objective.original contains the original text of the objective
    print(f"Reasoning Objective: {reasoning.objective.original if reasoning.objective else 'None'}")
    print(f"Number of nodes: {len(reasoning.nodes)}")
    
    # Print node details
    # Each node represents a step in the reasoning process
    for node_id, node in reasoning.nodes.items():
        print(f"\nNode ID: {node_id}")
        print(f"  Description: {node.description}")
        
        # Print node metadata
        # Metadata contains additional information about the node, such as
        # reasoning strategies, prompts, and other configuration
        if node.metadata:
            print("  Metadata:")
            for key, value in node.metadata.items():
                print(f"    {key}: {value}")

if __name__ == "__main__":
    # When run directly, this script creates and displays a reasoning pattern
    main() 