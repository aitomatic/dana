"""
Example demonstrating how to create a basic Default workflow.

This example shows how to:
1. Create a Default workflow with a specific objective
2. Inspect the workflow structure using the pretty_print method
"""

from dxa.execution import WorkflowFactory

def main():
    """Create and inspect a basic Default workflow."""
    # Define the objective for the workflow
    objective = "Design a database schema for a library management system."
    
    # Create the Default workflow using the convenience method
    workflow = WorkflowFactory.create_default_workflow(
        objective=objective,
        agent_role="Database Designer"
    )
    
    # Print the workflow using the pretty_print method
    print(workflow.pretty_print())
    
    print("\nWorkflow created successfully!")

if __name__ == "__main__":
    main() 