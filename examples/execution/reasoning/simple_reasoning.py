"""
Example demonstrating how to create a basic reasoning pattern.
"""

from dxa.execution import ReasoningFactory
from dxa.execution.execution_types import Objective

def main():
    """Create and inspect a basic reasoning pattern."""
    # Define the objective
    objective = "Solve the equation: 2x + 5 = 15"
    
    # Create reasoning from default config
    reasoning = ReasoningFactory.create_from_config(
        "default",
        objective=Objective(objective)
    )
    
    # Print reasoning information
    print(f"Reasoning Objective: {reasoning.objective.original if reasoning.objective else 'None'}")
    print(f"Number of nodes: {len(reasoning.nodes)}")
    
    # Print node details
    for node_id, node in reasoning.nodes.items():
        print(f"\nNode ID: {node_id}")
        print(f"  Description: {node.description}")
        
        # Print node metadata
        if node.metadata:
            print("  Metadata:")
            for key, value in node.metadata.items():
                print(f"    {key}: {value}")

if __name__ == "__main__":
    main() 