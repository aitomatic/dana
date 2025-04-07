"""
Example demonstrating how to create a basic planning pattern.
"""

from typing import cast
from opendxa.execution import PlanFactory
from opendxa.execution.execution_types import Objective
from opendxa.execution.planning import Plan

def main():
    """Create and inspect a basic planning pattern."""
    # Define the objective
    objective = "Design a database schema for a library management system."
    
    # Create planning from default config
    plan = PlanFactory.create_from_config(
        "default",
        objective=Objective(objective)
    )
    plan = cast(Plan, plan)
    
    # Print planning information
    assert plan is not None
    assert plan.objective is not None
    print(f"Planning Objective: {plan.objective.original}")
    assert plan.nodes is not None
    print(f"Number of nodes: {len(plan.nodes)}")
    
    # Print node details
    for node_id, node in plan.nodes.items():
        print(f"\nNode ID: {node_id}")
        print(f"  Description: {node.description}")
        
        # Print node metadata
        if node.metadata:
            print("  Metadata:")
            for key, value in node.metadata.items():
                print(f"    {key}: {value}")

if __name__ == "__main__":
    main() 