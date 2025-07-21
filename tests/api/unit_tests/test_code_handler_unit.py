"""
Unit tests for CodeHandler - tests function logic with all dependencies mocked.
"""

import unittest
from unittest.mock import Mock, patch
import json

from dana.api.services.code_handler import CodeHandler


class TestCodeHandlerUnit(unittest.TestCase):
    """Unit tests for CodeHandler utility class."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def test_clean_generated_code_empty_input(self):
        """Test cleaning empty code input."""
        # Test cases
        test_cases = ["", None, "   ", "\n\n"]
        
        for code in test_cases:
            with self.subTest(code=repr(code)):
                result = CodeHandler.clean_generated_code(code)
                self.assertEqual(result, "")
    
    def test_clean_generated_code_dana_markdown(self):
        """Test cleaning Dana markdown code blocks."""
        # Setup
        input_code = """Some text before
```dana
agent TestAgent:
    name: str = "Test"

def solve(query: str) -> str:
    return reason(query)
```
Some text after"""
        
        expected = """agent TestAgent:
    name: str = "Test"

def solve(query: str) -> str:
    return reason(query)"""
        
        # Execute
        result = CodeHandler.clean_generated_code(input_code)
        
        # Verify
        self.assertEqual(result, expected)
    
    def test_clean_generated_code_python_markdown(self):
        """Test cleaning Python markdown code blocks."""
        # Setup
        input_code = """```python
def hello():
    print("Hello World")
    return True
```"""
        
        expected = """def hello():
    print("Hello World")
    return True"""
        
        # Execute
        result = CodeHandler.clean_generated_code(input_code)
        
        # Verify
        self.assertEqual(result, expected)
    
    def test_clean_generated_code_na_markdown(self):
        """Test cleaning .na markdown code blocks."""
        # Setup
        input_code = """```na
struct Point:
    x: int = 0
    y: int = 0
```"""
        
        expected = """struct Point:
    x: int = 0
    y: int = 0"""
        
        # Execute
        result = CodeHandler.clean_generated_code(input_code)
        
        # Verify
        self.assertEqual(result, expected)
    
    def test_clean_generated_code_generic_markdown(self):
        """Test cleaning generic markdown code blocks."""
        # Setup
        input_code = """```
log("Starting agent")
agent_instance = MyAgent()
result = agent_instance.solve("test")
```"""
        
        expected = """log("Starting agent")
agent_instance = MyAgent()
result = agent_instance.solve("test")"""
        
        # Execute
        result = CodeHandler.clean_generated_code(input_code)
        
        # Verify
        self.assertEqual(result, expected)
    
    def test_clean_generated_code_removes_markdown_artifacts(self):
        """Test removal of markdown artifacts from code."""
        # Setup
        input_code = """agent MyAgent:
    name: str = "Test"
```
```python
def helper():
    pass
```dana
# Clean this up"""
        
        expected = """agent MyAgent:
    name: str = "Test"

def helper():
    pass
# Clean this up"""
        
        # Execute
        result = CodeHandler.clean_generated_code(input_code)
        
        # Verify
        self.assertEqual(result, expected)
    
    def test_parse_multi_file_response_empty_input(self):
        """Test parsing empty multi-file response."""
        # Test cases
        test_cases = ["", None, "   ", "\n\n"]
        
        for response in test_cases:
            with self.subTest(response=repr(response)):
                result = CodeHandler.parse_multi_file_response(response)
                
                # Verify fallback structure
                self.assertEqual(result["name"], "Georgia Training Project")
                self.assertEqual(result["structure_type"], "simple")
                self.assertEqual(len(result["files"]), 1)
                self.assertEqual(result["files"][0]["filename"], "main.na")
                self.assertEqual(result["main_file"], "main.na")
    
    def test_parse_multi_file_response_json_format(self):
        """Test parsing JSON format multi-file response."""
        # Setup
        json_response = json.dumps({
            "main.na": "agent MainAgent:\n    name: str = \"Main\"",
            "tools.na": "def helper_tool():\n    return \"help\"",
            "workflows.na": "workflow = process | generate"
        })
        
        # Execute
        result = CodeHandler.parse_multi_file_response(json_response)
        
        # Verify
        self.assertEqual(len(result["files"]), 6)  # 3 parsed + 3 missing required files
        self.assertEqual(result["structure_type"], "complex")
        
        # Find the parsed files
        main_file = next(f for f in result["files"] if f["filename"] == "main.na")
        tools_file = next(f for f in result["files"] if f["filename"] == "tools.na")
        workflows_file = next(f for f in result["files"] if f["filename"] == "workflows.na")
        
        self.assertIn("MainAgent", main_file["content"])
        self.assertIn("helper_tool", tools_file["content"])
        self.assertIn("workflow = process", workflows_file["content"])
    
    def test_parse_multi_file_response_file_start_end_format(self):
        """Test parsing FILE_START/FILE_END format."""
        # Setup
        response = """FILE_START: main.na
agent FileAgent:
    name: str = "FileAgent"

def solve(query: str) -> str:
    return reason(query)
FILE_END: main.na

FILE_START: methods.na
def process_data(data: str) -> str:
    return data.upper()
FILE_END: methods.na"""
        
        # Execute
        result = CodeHandler.parse_multi_file_response(response)
        
        # Verify
        self.assertEqual(len(result["files"]), 6)  # 2 parsed + 4 missing required files
        
        # Find the parsed files
        main_file = next(f for f in result["files"] if f["filename"] == "main.na")
        methods_file = next(f for f in result["files"] if f["filename"] == "methods.na")
        
        self.assertIn("FileAgent", main_file["content"])
        self.assertIn("process_data", methods_file["content"])
    
    def test_determine_file_type(self):
        """Test file type determination logic."""
        # Test cases
        test_cases = [
            ("main.na", "agent"),
            ("workflows.na", "workflow"),
            ("knowledge.na", "resources"),
            ("methods.na", "methods"),
            ("tools.na", "tools"),
            ("common.na", "common"),
            ("unknown.na", "other"),
            ("custom_file.na", "other")
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                result = CodeHandler.determine_file_type(filename)
                self.assertEqual(result, expected_type)
    
    def test_get_file_description(self):
        """Test file description generation."""
        # Test cases
        test_cases = [
            ("main.na", "Main agent definition and orchestration"),
            ("workflows.na", "Workflow orchestration and pipelines"),
            ("knowledge.na", "Resource configurations (RAG, databases, APIs)"),
            ("methods.na", "Core processing methods and utilities"),
            ("tools.na", "Tool definitions and integrations"),
            ("common.na", "Shared data structures and utilities"),
            ("unknown.na", "Dana agent file")
        ]
        
        for filename, expected_desc in test_cases:
            with self.subTest(filename=filename):
                result = CodeHandler.get_file_description(filename)
                self.assertEqual(result, expected_desc)
    
    def test_extract_dependencies(self):
        """Test dependency extraction from code content."""
        # Setup
        content = """from workflows import workflow
from methods import process_request, generate_response
import common
import math.py
from tools import helper_tool
# Comment line
def some_function():
    pass"""
        
        # Execute
        result = CodeHandler.extract_dependencies(content)
        
        # Verify
        expected_deps = ["workflows", "methods", "common", "tools"]
        self.assertEqual(sorted(result), sorted(expected_deps))
        # Verify Python imports are excluded
        self.assertNotIn("math.py", result)
    
    def test_get_file_template_known_files(self):
        """Test template generation for known file types."""
        # Test main.na template
        main_template = CodeHandler.get_file_template("main.na")
        self.assertIn("agent Georgia:", main_template)
        self.assertIn("def solve(", main_template)
        self.assertIn("this_agent = Georgia()", main_template)
        
        # Test workflows.na template
        workflows_template = CodeHandler.get_file_template("workflows.na")
        self.assertIn("from methods import", workflows_template)
        self.assertIn("workflow = ", workflows_template)
        
        # Test methods.na template
        methods_template = CodeHandler.get_file_template("methods.na")
        self.assertIn("def process_request(", methods_template)
        self.assertIn("def generate_response(", methods_template)
        
        # Test common.na template
        common_template = CodeHandler.get_file_template("common.na")
        self.assertIn("struct AgentPackage:", common_template)
        
        # Test knowledge.na template
        knowledge_template = CodeHandler.get_file_template("knowledge.na")
        self.assertIn("Knowledge Description:", knowledge_template)
        
        # Test tools.na template
        tools_template = CodeHandler.get_file_template("tools.na")
        self.assertIn("Tools Description:", tools_template)
    
    def test_get_file_template_unknown_file(self):
        """Test template generation for unknown file types."""
        # Execute
        result = CodeHandler.get_file_template("unknown.na")
        
        # Verify
        self.assertEqual(result, "# unknown.na - Generated template file")
    
    def test_ensure_all_files_present(self):
        """Test ensuring all required files are present in project."""
        # Setup
        project = {
            "files": [
                {
                    "filename": "main.na",
                    "content": "agent Test: pass",
                    "file_type": "agent",
                    "description": "Main file",
                    "dependencies": []
                }
            ],
            "main_file": "main.na",
            "name": "Test Project",
            "description": "Test description"
        }
        
        # Execute
        result = CodeHandler.ensure_all_files_present(project)
        
        # Verify all required files are present
        required_files = ["main.na", "workflows.na", "methods.na", "common.na", "knowledge.na", "tools.na"]
        result_filenames = {f["filename"] for f in result["files"]}
        
        for required_file in required_files:
            self.assertIn(required_file, result_filenames)
        
        # Verify original file is preserved
        main_file = next(f for f in result["files"] if f["filename"] == "main.na")
        self.assertIn("agent Test:", main_file["content"])
    
    def test_get_fallback_template(self):
        """Test fallback template generation."""
        # Execute
        result = CodeHandler.get_fallback_template()
        
        # Verify
        self.assertIn("agent BasicAgent:", result)
        self.assertIn("def solve(", result)
        self.assertIn("return reason(", result)
        self.assertIn("example_input", result)
    
    @patch('dana.api.services.code_handler.logger')
    def test_parse_multi_file_response_json_error_fallback(self, mock_logger):
        """Test JSON parsing error fallback to FILE_START/FILE_END format."""
        # Setup - invalid JSON that will fall back to FILE_START/FILE_END
        response = """Not valid JSON
FILE_START: test.na
agent FallbackAgent:
    name: str = "Fallback"
FILE_END: test.na"""
        
        # Execute
        result = CodeHandler.parse_multi_file_response(response)
        
        # Verify
        mock_logger.warning.assert_called()
        self.assertIn("Failed to parse JSON response", str(mock_logger.warning.call_args))
        
        # Verify fallback parsing worked
        test_file = next((f for f in result["files"] if f["filename"] == "test.na"), None)
        self.assertIsNotNone(test_file)
        self.assertIn("FallbackAgent", test_file["content"])
    
    def test_parse_multi_file_response_tools_import_patch(self):
        """Test the tools import patch functionality."""
        # Setup - JSON response with methods.na importing from tools
        json_response = json.dumps({
            "methods.na": "from tools import calculator, formatter\ndef process():\n    return calculator('2+2')",
            "tools.na": "def calculator(expr: str) -> str:\n    return '4'"
        })
        
        # Execute
        result = CodeHandler.parse_multi_file_response(json_response)
        
        # Verify
        tools_file = next(f for f in result["files"] if f["filename"] == "tools.na")
        
        # Should have original calculator and auto-generated formatter stub
        self.assertIn("def calculator(", tools_file["content"])
        self.assertIn("def formatter(", tools_file["content"])
        self.assertIn("Auto-generated stub", tools_file["content"])


if __name__ == '__main__':
    unittest.main()