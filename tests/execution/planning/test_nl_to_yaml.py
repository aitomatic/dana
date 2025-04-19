"""Test natural language to YAML workflow implementation."""

import unittest
from opendxa import PlanFactory, Plan, NodeType

class TestNLToYAML(unittest.TestCase):
    """Test natural language to YAML plan implementation."""

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

    def test_plan_from_yaml(self):
        """Test creating a plan from YAML data."""
        plan = PlanFactory.from_yaml(self.yaml_content)
        
        # Verify plan structure
        assert isinstance(plan, Plan)
        assert plan.objective is not None
        assert plan.objective.current == "Analyze market trends"
        
        # Verify nodes
        assert "GATHER_DATA" in plan.nodes
        assert "ANALYZE_TRENDS" in plan.nodes
        assert "GENERATE_REPORT" in plan.nodes
        
        # Verify node types
        assert plan.nodes["GATHER_DATA"].node_type == NodeType.TASK
        assert plan.nodes["ANALYZE_TRENDS"].node_type == NodeType.TASK
        assert plan.nodes["GENERATE_REPORT"].node_type == NodeType.TASK

if __name__ == '__main__':
    unittest.main() 