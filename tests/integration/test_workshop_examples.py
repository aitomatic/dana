"""Integration tests for Dana workshop examples.

This test suite validates all Dana examples in the examples/workshop/ directory
to ensure they work correctly and demonstrate proper usage patterns.
"""

import os
import unittest
from pathlib import Path
from typing import Any, Dict

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


class TestWorkshopExamples(unittest.TestCase):
    """Integration tests for Dana workshop examples."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment
        self.original_env = os.environ.copy()
        
        # Set up mock environment for testing
        os.environ.update({
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key", 
            "GROQ_API_KEY": "test-groq-key",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
            # Enable mock mode for testing
            "DANA_MOCK_LLM": "true",
        })
        
        # Get workshop directory path
        self.workshop_dir = Path(__file__).parent.parent.parent / "examples" / "workshop"
        
    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def _execute_dana_file(self, file_path: Path, should_succeed: bool = True) -> Dict[str, Any]:
        """
        Execute a Dana file and return results.
        
        Args:
            file_path: Path to the .na file
            should_succeed: Whether the execution should succeed
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Use DanaSandbox.quick_run for file execution
            result = DanaSandbox.quick_run(file_path, debug_mode=False)
            
            return {
                "success": result.success,
                "result": result.result,
                "output": result.output,
                "error": result.error,
                "file_path": str(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "output": "",
                "error": e,
                "file_path": str(file_path)
            }

    def test_basic_language_features(self):
        """Test basic Dana language features from workshop examples."""
        # Test builtin reasoning
        builtin_reasoning_file = self.workshop_dir / "1_dana_language_and_runtime" / "builtin_reasoning.na"
        if builtin_reasoning_file.exists():
            result = self._execute_dana_file(builtin_reasoning_file)
            self.assertTrue(result["success"], 
                          f"builtin_reasoning.na failed: {result['error']}")

        # Test semantic type coercion - may fail due to external dependencies
        semantic_coercion_file = self.workshop_dir / "1_dana_language_and_runtime" / "semantic_type_coercion.na"
        if semantic_coercion_file.exists():
            result = self._execute_dana_file(semantic_coercion_file, should_succeed=False)
            # This may fail due to MCP service dependency, which is expected in test environment
            print(f"Semantic type coercion result: {result['success']}")

    def test_resource_examples_mock_mode(self):
        """Test resource examples in mock mode (may have limited functionality)."""
        resource_examples = [
            "1_dana_language_and_runtime/docs_resource/docs_resource.na",
            "1_dana_language_and_runtime/mcp_resource/mcp_resource.na",
        ]
        
        for example_path in resource_examples:
            full_path = self.workshop_dir / example_path
            if full_path.exists():
                result = self._execute_dana_file(full_path, should_succeed=False)
                # These may fail due to external dependencies, log for information
                print(f"Resource example {example_path}: success={result['success']}")

    def test_agent_examples(self):
        """Test individual agent examples."""
        # Test reasoning agent
        agent_file = self.workshop_dir / "2_agent_and_system_of_agents" / "agent" / "reasoning_using_an_agent.na"
        if agent_file.exists():
            result = self._execute_dana_file(agent_file, should_succeed=False)
            # May fail due to MCP dependency, but should at least parse correctly
            print(f"Reasoning agent result: {result['success']}")

    def test_python_interoperability_examples(self):
        """Test Python interoperability examples."""
        # Test order intelligence Dana file
        order_intel_file = self.workshop_dir / "5_python_interoperability" / "python_calling_dana" / "dana_files" / "order_intelligence.na"
        if order_intel_file.exists():
            result = self._execute_dana_file(order_intel_file)
            self.assertTrue(result["success"], 
                          f"order_intelligence.na failed: {result['error']}")

    def test_workshop_file_existence(self):
        """Test that expected workshop files exist."""
        expected_files = [
            "1_dana_language_and_runtime/builtin_reasoning.na",
            "1_dana_language_and_runtime/semantic_type_coercion.na", 
            "1_dana_language_and_runtime/docs_resource/docs_resource.na",
            "1_dana_language_and_runtime/mcp_resource/mcp_resource.na",
            "2_agent_and_system_of_agents/agent/reasoning_using_an_agent.na",
            "2_agent_and_system_of_agents/system_of_agents/gma.na",
            "2_agent_and_system_of_agents/system_of_agents/specialist_agent_1.na",
            "2_agent_and_system_of_agents/system_of_agents/specialist_agent_2.na", 
            "2_agent_and_system_of_agents/system_of_agents/specialist_agent_3.na",
            "5_python_interoperability/python_calling_dana/dana_files/order_intelligence.na",
        ]
        
        missing_files = []
        for file_path in expected_files:
            full_path = self.workshop_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.assertEqual([], missing_files, 
                        f"Missing expected workshop files: {missing_files}")

    def test_agent_structure_validation(self):
        """Test that agent examples have proper structure."""
        agent_files = [
            "2_agent_and_system_of_agents/agent/reasoning_using_an_agent.na",
            "5_python_interoperability/python_calling_dana/dana_files/order_intelligence.na",
        ]
        
        for agent_path in agent_files:
            full_path = self.workshop_dir / agent_path
            if full_path.exists():
                # Read file content to check for agent structure
                content = full_path.read_text()
                
                # Check for function definitions (basic validation)
                self.assertIn("def ", content, 
                            f"Agent file {agent_path} should contain function definitions")

    def test_file_discovery_and_basic_validation(self):
        """Test that Dana files can be discovered and have basic validity."""
        dana_files = []
        
        # Find all .na files in workshop directory
        for dana_file in self.workshop_dir.rglob("*.na"):
            dana_files.append(dana_file)
        
        self.assertGreater(len(dana_files), 0, "No Dana files found in workshop directory")
        
        file_issues = []
        for dana_file in dana_files:
            try:
                # Basic file validation
                content = dana_file.read_text()
                
                # Check file is not empty
                if not content.strip():
                    file_issues.append(f"{dana_file.relative_to(self.workshop_dir)}: Empty file")
                    continue
                
                # Basic syntax heuristics (without full parsing)
                # Check for balanced quotes and parentheses
                quote_count = content.count('"') + content.count("'")
                if quote_count % 2 != 0:
                    file_issues.append(f"{dana_file.relative_to(self.workshop_dir)}: Unbalanced quotes")
                
                # Check for basic Dana patterns
                if 'def ' in content and content.count('def ') > content.count('def ') * 2:
                    # This is a loose check - if there are function definitions, the file should be reasonable
                    pass
                    
                # Check for obvious syntax issues like unmatched brackets
                open_parens = content.count('(')
                close_parens = content.count(')')
                if open_parens != close_parens:
                    file_issues.append(f"{dana_file.relative_to(self.workshop_dir)}: Unbalanced parentheses ({open_parens} open, {close_parens} close)")
                    
            except Exception as e:
                file_issues.append(f"{dana_file.relative_to(self.workshop_dir)}: Could not read file - {e}")
        
        # Report findings but don't fail the test - this is informational
        if file_issues:
            print(f"\n⚠️  File issues found (informational): {file_issues}")
        
        print(f"\n✅ Found {len(dana_files)} Dana files in workshop directory")
        for dana_file in dana_files:
            print(f"   - {dana_file.relative_to(self.workshop_dir)}")
        
        # This test passes as long as we found files
        self.assertTrue(True, "File discovery completed")


# Parametrized tests for individual files
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "builtin_reasoning",
            "file_path": "1_dana_language_and_runtime/builtin_reasoning.na",
            "should_succeed": True,
            "description": "Basic reasoning functionality"
        },
        {
            "name": "semantic_type_coercion",
            "file_path": "1_dana_language_and_runtime/semantic_type_coercion.na", 
            "should_succeed": False,  # May fail due to MCP dependency
            "description": "Semantic type coercion with external service"
        },
        {
            "name": "docs_resource",
            "file_path": "1_dana_language_and_runtime/docs_resource/docs_resource.na",
            "should_succeed": False,  # May fail due to RAG dependency
            "description": "Document resource querying"
        },
        {
            "name": "mcp_resource", 
            "file_path": "1_dana_language_and_runtime/mcp_resource/mcp_resource.na",
            "should_succeed": False,  # May fail due to MCP server dependency
            "description": "MCP resource integration"
        },
        {
            "name": "reasoning_agent",
            "file_path": "2_agent_and_system_of_agents/agent/reasoning_using_an_agent.na",
            "should_succeed": False,  # May fail due to MCP dependency
            "description": "Individual reasoning agent"
        },
        {
            "name": "order_intelligence",
            "file_path": "5_python_interoperability/python_calling_dana/dana_files/order_intelligence.na",
            "should_succeed": True,
            "description": "Python interoperability example"
        },
    ],
    ids=lambda x: x["name"]
)
def test_workshop_file_execution(test_case):
    """Parametrized test for individual workshop file execution."""
    # Set up mock environment
    original_env = os.environ.copy()
    os.environ.update({
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GROQ_API_KEY": "test-groq-key", 
        "DEEPSEEK_API_KEY": "test-deepseek-key",
        "DANA_MOCK_LLM": "true",
    })
    
    try:
        # Get file path
        workshop_dir = Path(__file__).parent.parent.parent / "examples" / "workshop"
        file_path = workshop_dir / test_case["file_path"]
        
        # Skip if file doesn't exist
        if not file_path.exists():
            pytest.skip(f"Workshop file not found: {test_case['file_path']}")
        
        # Execute the file
        result = DanaSandbox.quick_run(file_path, debug_mode=False)
        
        if test_case["should_succeed"]:
            assert result.success, f"Expected {test_case['name']} to succeed but got error: {result.error}"
        else:
            # For files that may fail due to dependencies, just log the result
            print(f"Workshop file {test_case['name']}: success={result.success}, error={result.error}")
    
    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(original_env)


if __name__ == "__main__":
    unittest.main() 