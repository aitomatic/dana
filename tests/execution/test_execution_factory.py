"""Tests for ExecutionFactory."""

import tempfile
from pathlib import Path
import yaml

from dxa.execution.execution_factory import ExecutionFactory
from dxa.execution.execution_graph import ExecutionGraph
from dxa.execution.execution_types import Objective

class TestExecutionFactory:
    """Tests for ExecutionFactory."""
    
    def test_create_from_config_with_config_dir(self):
        """Test creating an execution graph with a custom config directory."""
        # Create a temporary directory for our test config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test config file
            test_config = {
                "name": "test_config",
                "description": "Test configuration",
                "nodes": [
                    {
                        "id": "TEST_NODE",
                        "description": "Test node"
                    }
                ]
            }
            
            # Write the config to a file
            config_path = temp_path / "test_config.yaml"
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)
            
            # Create an execution graph using the custom config directory
            objective = Objective("Test objective")
            graph = ExecutionFactory.create_from_config(
                "test_config",
                objective,
                config_dir=temp_path
            )
            
            # Verify the graph was created correctly
            assert isinstance(graph, ExecutionGraph)
            assert graph.objective == objective
            assert "TEST_NODE" in graph.nodes
            assert graph.nodes["TEST_NODE"].description == "Test node"
            
            # Test with explicit .yaml extension
            graph = ExecutionFactory.create_from_config(
                "test_config.yaml",
                objective,
                config_dir=temp_path
            )
            assert "TEST_NODE" in graph.nodes
            
            # Create a .yml version to test that extension
            config_path_yml = temp_path / "test_config_yml.yml"
            with open(config_path_yml, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)
                
            # Test with .yml extension
            graph = ExecutionFactory.create_from_config(
                "test_config_yml.yml",
                objective,
                config_dir=temp_path
            )
            assert "TEST_NODE" in graph.nodes
    
    def test_create_from_config_with_role(self):
        """Test creating an execution graph with a role."""
        # Create a temporary directory for our test config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test config file
            test_config = {
                "name": "test_role",
                "description": "Test role configuration",
                "nodes": [
                    {
                        "id": "TEST_NODE",
                        "description": "Test node"
                    }
                ]
            }
            
            # Write the config to a file
            config_path = temp_path / "test_role.yaml"
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)
            
            # Create an execution graph with a role
            objective = Objective("Test objective")
            role = "Test Role"
            graph = ExecutionFactory.create_from_config(
                "test_role",
                objective,
                role=role,
                config_dir=temp_path
            )
            
            # Verify the role was set correctly
            assert graph.metadata.get("role") == role 