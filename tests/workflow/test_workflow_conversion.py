"""Test cases for natural language to workflow conversion."""

import pytest
from dxa.core.workflow import create_from_text

TEST_CASES = [
    # Simple sequential
    ("""
    Download the data.
    Clean it up.
    Save results.
    """, 5),  # Expected nodes (START, 3 tasks, END)
    
    # With decision
    ("""
    Check the data quality.
    If quality is good:
        Process normally.
    Otherwise:
        Run cleanup first.
        Then process.
    """, 7),  # START, decision, 3-4 tasks, END
    
    # Complex with states
    ("""
    Load customer data (needs database access).
    Analyze purchase history.
    If total purchases > 1000:
        Generate VIP report.
    Otherwise:
        Create standard report.
    Send report to customer email.
    """, 7)
]

@pytest.mark.parametrize("text,expected_nodes", TEST_CASES)
def test_workflow_conversion(text, expected_nodes):
    """Test that workflows are created correctly from text."""
    workflow = create_from_text(text)
    
    # Basic structure tests
    assert len(workflow.nodes) == expected_nodes
    assert workflow.get_start().type == "START"
    assert len(workflow.get_ends()) == 1
    
    # Validate all edges connect existing nodes
    for edge in workflow.edges.values():
        assert edge.from_id in workflow.nodes
        assert edge.to_id in workflow.nodes

    # Validate YAML generation
    yaml_str = workflow.to_yaml()
    assert yaml_str is not None
    assert "nodes:" in yaml_str
    assert "edges:" in yaml_str 