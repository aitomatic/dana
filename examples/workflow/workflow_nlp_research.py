"""Example of research workflow with decision points."""

from dxa.core.workflow import create_from_text

# Research workflow with conditional paths
text = """
Create a workflow for conducting literature review.

Start by searching academic databases for papers about quantum computing.
If we find enough relevant papers (at least 10), proceed with analysis.
Otherwise, expand the search criteria and try again.

For papers that pass initial screening, download their full text.
Then extract key methodologies and findings from each paper.

If any groundbreaking discoveries are found, mark them for detailed review.
Otherwise, proceed with standard analysis.

Finally, synthesize all findings into a comprehensive report.
Include recommendations for future research directions.
"""

# Create workflow
workflow = create_from_text(text)

# Display the generated YAML
print("Generated YAML:")
print(workflow.to_yaml())

# Demonstrate traversal with decisions
cursor = workflow.cursor()
while cursor.has_next():
    node = cursor.next()
    print(f"\nAt node: {node.type} - {node.description}")
    
    if node.type == "DECISION":
        # Simulate decision logic
        print("Decision point reached:")
        edges = workflow.get_edges_from(node.id)
        for edge in edges:
            print(f"- Option: {edge.condition}")
        
        # For demo, always take first path
        next_nodes = [
            workflow.nodes[edge.to_id] 
            for edge in edges
        ]
        if next_nodes:
            cursor.set_next(next_nodes[0]) 