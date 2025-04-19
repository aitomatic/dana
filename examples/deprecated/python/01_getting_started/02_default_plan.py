"""Default Plan Creation Example

This example demonstrates how to create a basic Default plan in the DXA framework,
which is the simplest plan pattern for general-purpose tasks.

Key concepts:
- Plan creation using PlanFactory
- Default plan structure and components
- Plan visualization using pretty_print

Learning path: Getting Started
Complexity: Beginner

Prerequisites:
- None

Related examples:
- qa_approaches.py: Different approaches to question answering
- run_default_plan.py: Running the default plan
"""

from opendxa.execution import PlanFactory


def main():
    """Create and inspect a basic Default plan.
    
    This function demonstrates:
    1. Defining an objective for the plan
    2. Creating a Default plan
    3. Visualizing the plan structure
    
    The Default plan is a simple pattern that consists of:
    - START node: Entry point for execution
    - task node: Contains the objective to be accomplished
    - END node: Exit point for execution
    
    Returns:
        None: This function prints the plan structure but doesn't return a value
    """
    # Define the objective for the plan
    # This will be the task that the agent needs to accomplish
    objective = "Design a database schema for a library management system."
    
    # Create the Default plan using the convenience method from PlanFactory
    plan = PlanFactory.create_default_plan(objective=objective)
    
    # Print the plan using the pretty_print method
    # This visualizes the nodes and edges in the plan graph
    print(plan.pretty_print())  # pylint: disable=no-member

    print("\nPlan created successfully!")


if __name__ == "__main__":
    # When run directly, this script creates and displays a default plan
    main() 