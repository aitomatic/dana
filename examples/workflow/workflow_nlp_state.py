"""Example of workflow with explicit state management."""

from dxa.core.workflow import create_from_text

# Data processing workflow with state requirements
text = """
Create a data processing pipeline for machine learning.

We start with raw data files in S3. We need to:
1. Download the files (requires S3 credentials)
2. Parse the CSV data (needs file paths, produces DataFrame)
3. Check data quality:
   - If quality score > 0.8, proceed to feature engineering
   - If quality is poor, run data cleaning first

For feature engineering:
- Take the clean data
- Apply standard scaling
- Generate new features based on domain rules
- Save the processed dataset

Finally, validate the results and generate a data quality report.
"""

# Create and examine workflow
workflow = create_from_text(text)

print("Generated YAML:")
print(workflow.to_yaml())

# Analyze state requirements
def print_state_requirements(workflow):
    """Print state requirements for each node."""
    print("\nState Requirements Analysis:")
    for node in workflow.nodes.values():
        if node.requires or node.provides:
            print(f"\n{node.type} - {node.description}")
            if node.requires:
                print("  Requires:", node.requires)
            if node.provides:
                print("  Provides:", node.provides)

print_state_requirements(workflow) 