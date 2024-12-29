"""Example of converting natural language to workflow."""

from dxa.core.workflow import create_from_text

# Basic sequential workflow
text = """
I need a workflow that helps me analyze some data.
First, load the dataset from our database.
Then clean up any missing or invalid values.
After that, run statistical analysis on the clean data.
Finally, generate a report with visualizations.
"""

# Create and display workflow
workflow = create_from_text(text)
print("Generated YAML:")
print(workflow.to_yaml())

# Use the workflow
# cursor = workflow.cursor()
# while cursor.has_next():
#     node = cursor.next()
#     print(f"\nExecuting: {node.type} - {node.description}")
#     if node.requires:
#         print(f"Requires: {node.requires}")
#     if node.provides:
#         print(f"Provides: {node.provides}") 
