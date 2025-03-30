"""Test natural language to YAML workflow implementation."""

import unittest
from dxa.execution import WorkflowFactory
from dxa.execution import Workflow
from dxa.common.graph import NodeType

class TestNLToYAML(unittest.TestCase):
    """Test natural language to YAML workflow implementation."""

    def setUp(self):
        """Set up test data."""
        self.yaml_content = {
            "objective": "Analyze market trends",
            "nodes": [
                {
                    "id": "GATHER_DATA",
                    "type": "TASK",
                    "description": "Gather market data",
                    "objective": "Collect relevant market data"
                },
                {
                    "id": "ANALYZE_TRENDS",
                    "type": "TASK",
                    "description": "Analyze trends",
                    "objective": "Analyze market trends"
                },
                {
                    "id": "GENERATE_REPORT",
                    "type": "TASK",
                    "description": "Generate report",
                    "objective": "Create analysis report"
                }
            ],
            "edges": [
                {"source": "START", "target": "GATHER_DATA"},
                {"source": "GATHER_DATA", "target": "ANALYZE_TRENDS"},
                {"source": "ANALYZE_TRENDS", "target": "GENERATE_REPORT"},
                {"source": "GENERATE_REPORT", "target": "END"}
            ]
        }

    def test_workflow_from_yaml(self):
        """Test creating a workflow from YAML data."""
        workflow = WorkflowFactory.from_yaml(self.yaml_content)
        
        # Verify workflow structure
        assert isinstance(workflow, Workflow)
        assert workflow.objective is not None
        assert workflow.objective.current == "Analyze market trends"
        
        # Verify nodes
        assert "GATHER_DATA" in workflow.nodes
        assert "ANALYZE_TRENDS" in workflow.nodes
        assert "GENERATE_REPORT" in workflow.nodes
        
        # Verify node types
        assert workflow.nodes["GATHER_DATA"].node_type == NodeType.TASK
        assert workflow.nodes["ANALYZE_TRENDS"].node_type == NodeType.TASK
        assert workflow.nodes["GENERATE_REPORT"].node_type == NodeType.TASK

if __name__ == '__main__':
    unittest.main() 