"""Default Workflow Creation Example

This example demonstrates how to create a basic Default workflow in the DXA framework,
which is the simplest workflow pattern for general-purpose tasks.

Key concepts:
- Workflow creation using WorkflowFactory
- Default workflow structure and components
- Workflow visualization using pretty_print

Learning path: Getting Started
Complexity: Beginner

Prerequisites:
- None

Related examples:
- qa_approaches.py: Different approaches to question answering
- run_default_workflow.py: Running the default workflow
"""

from dxa.execution import WorkflowFactory


def main():
    """Create and inspect a basic Default workflow.
    
    This function demonstrates:
    1. Defining an objective for the workflow
    2. Creating a Default workflow
    3. Visualizing the workflow structure
    
    The Default workflow is a simple pattern that consists of:
    - START node: Entry point for execution
    - task node: Contains the objective to be accomplished
    - END node: Exit point for execution
    
    Returns:
        None: This function prints the workflow structure but doesn't return a value
    """
    # Define the objective for the workflow
    # This will be the task that the agent needs to accomplish
    objective = "Design a database schema for a library management system."
    
    # Create the Default workflow using the convenience method from WorkflowFactory
    workflow = WorkflowFactory.create_default_workflow(objective=objective)
    
    # Print the workflow using the pretty_print method
    # This visualizes the nodes and edges in the workflow graph
    print(workflow.pretty_print())  # pylint: disable=no-member

    print("\nWorkflow created successfully!")


if __name__ == "__main__":
    # When run directly, this script creates and displays a default workflow
    main() 