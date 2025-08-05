"""
Unit tests for workflow_parser module.
"""

import pytest
from dana.api.services.workflow_parser import (
    WorkflowParser, 
    parse_workflow_content, 
    extract_workflow_pipeline,
    WorkflowImport,
    PipelineStep,
    WorkflowDefinition,
    FunctionDefinition
)


class TestWorkflowParser:
    """Test cases for WorkflowParser class"""
    
    def test_simple_pipeline_workflow(self):
        """Test parsing simple pipeline workflow"""
        content = """from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = refine_query | search_document | get_answer"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 1
        assert result["total_functions"] == 0
        assert result["has_pipeline_workflows"] is True
        assert result["has_function_definitions"] is False
        
        workflow_def = result["workflow_definitions"][0]
        assert workflow_def["name"] == "workflow"
        assert workflow_def["type"] == "pipeline"
        assert len(workflow_def["steps"]) == 3
        
        step_names = [step["function_name"] for step in workflow_def["steps"]]
        assert step_names == ["refine_query", "search_document", "get_answer"]
        
        # Check step ordering
        for i, step in enumerate(workflow_def["steps"]):
            assert step["order"] == i
    
    def test_extended_pipeline_workflow(self):
        """Test parsing extended pipeline workflow"""
        content = """from methods import should_use_rag
from methods import refine_query
from methods import search_document  
from methods import get_answer

workflow = should_use_rag | refine_query | search_document | get_answer"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 1
        workflow_def = result["workflow_definitions"][0]
        step_names = [step["function_name"] for step in workflow_def["steps"]]
        assert step_names == ["should_use_rag", "refine_query", "search_document", "get_answer"]
    
    def test_imports_extraction(self):
        """Test extraction of import statements"""
        content = """from methods import refine_query
from utils import helper_function
from data import process_data

workflow = refine_query | helper_function | process_data"""
        
        result = parse_workflow_content(content)
        
        imports = result["imports"]
        assert len(imports) == 3
        
        import_pairs = [(imp["module"], imp["function"]) for imp in imports]
        expected_imports = [
            ("methods", "refine_query"),
            ("utils", "helper_function"), 
            ("data", "process_data")
        ]
        assert import_pairs == expected_imports
    
    def test_function_definitions(self):
        """Test parsing function definitions"""
        content = """def standard_workflow(input: str) -> str {
    log("Starting standard workflow")
    
    if not validate_input(input) {
        return "Invalid input provided"
    }
    
    result = process_with_context(input)
    return result
}

def process_with_context(input: str) -> str {
    return f"Processed: {input}"
}"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 0
        assert result["total_functions"] == 2
        assert result["has_function_definitions"] is True
        
        functions = result["function_definitions"]
        
        # Check first function
        func1 = functions[0]
        assert func1["name"] == "standard_workflow"
        assert func1["parameters"] == ["input"]
        assert func1["return_type"] == "str"
        assert "log(" in func1["body"]
        
        # Check second function
        func2 = functions[1]
        assert func2["name"] == "process_with_context"
        assert func2["parameters"] == ["input"]
        assert func2["return_type"] == "str"
        assert "Processed:" in func2["body"]
    
    def test_mixed_content(self):
        """Test parsing content with both pipelines and functions"""
        content = """from methods import refine_query
from methods import search_document

workflow = refine_query | search_document

def helper_function(data: str) -> str {
    return f"Processed: {data}"
}"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 1
        assert result["total_functions"] == 1
        assert result["has_pipeline_workflows"] is True
        assert result["has_function_definitions"] is True
    
    def test_comments_handling(self):
        """Test that comments are properly handled"""
        content = """/*
 * Agent workflows and processes
 * Define complex multi-step processes here
 */

from methods import refine_query  // Import refine function
from methods import search_document

// Main workflow definition
workflow = refine_query | search_document"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 1
        workflow_def = result["workflow_definitions"][0]
        step_names = [step["function_name"] for step in workflow_def["steps"]]
        assert step_names == ["refine_query", "search_document"]
    
    def test_empty_content(self):
        """Test parsing empty or whitespace-only content"""
        content = """


        
        """
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 0
        assert result["total_functions"] == 0
        assert result["has_pipeline_workflows"] is False
        assert result["has_function_definitions"] is False
    
    def test_extract_workflow_pipeline_convenience_function(self):
        """Test the convenience function for extracting pipeline info"""
        content = """from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = refine_query | search_document | get_answer"""
        
        pipeline_info = extract_workflow_pipeline(content)
        
        assert pipeline_info is not None
        assert pipeline_info["name"] == "workflow"
        assert pipeline_info["functions"] == ["refine_query", "search_document", "get_answer"]
        assert len(pipeline_info["imports"]) == 3
    
    def test_extract_workflow_pipeline_no_pipeline(self):
        """Test convenience function when no pipeline exists"""
        content = """def some_function(input: str) -> str {
    return input
}"""
        
        pipeline_info = extract_workflow_pipeline(content)
        
        assert pipeline_info is None
    
    def test_malformed_content_error_handling(self):
        """Test error handling for malformed content"""
        content = "this is not valid workflow content"
        
        result = parse_workflow_content(content)
        
        # Should not error, just return empty results
        assert result["total_workflows"] == 0
        assert result["total_functions"] == 0
    
    def test_multiple_workflows(self):
        """Test parsing multiple workflow definitions"""
        content = """from methods import func1
from methods import func2
from methods import func3

main_workflow = func1 | func2
secondary_workflow = func2 | func3"""
        
        result = parse_workflow_content(content)
        
        assert result["total_workflows"] == 2
        
        workflow_names = [wd["name"] for wd in result["workflow_definitions"]]
        assert "main_workflow" in workflow_names
        assert "secondary_workflow" in workflow_names
    
    def test_complex_function_parameters(self):
        """Test parsing functions with complex parameter signatures"""
        content = """def complex_function(input: str, config: dict, optional: bool = True) -> dict {
    return {"result": input, "config": config}
}"""
        
        result = parse_workflow_content(content)
        
        assert result["total_functions"] == 1
        func_def = result["function_definitions"][0]
        assert func_def["name"] == "complex_function"
        # Parameters should extract just the names
        assert "input" in func_def["parameters"]
        assert "config" in func_def["parameters"]
        assert "optional" in func_def["parameters"]


class TestWorkflowParserDataClasses:
    """Test data classes used by workflow parser"""
    
    def test_workflow_import(self):
        """Test WorkflowImport data class"""
        import_obj = WorkflowImport(module="methods", function="refine_query")
        assert str(import_obj) == "from methods import refine_query"
    
    def test_pipeline_step(self):
        """Test PipelineStep data class"""
        step = PipelineStep(function_name="refine_query", order=0)
        assert str(step) == "refine_query"
    
    def test_workflow_definition_to_dict(self):
        """Test WorkflowDefinition to_dict method"""
        imports = [WorkflowImport(module="methods", function="func1")]
        steps = [PipelineStep(function_name="func1", order=0)]
        
        workflow_def = WorkflowDefinition(
            name="test_workflow",
            type="pipeline",
            steps=steps,
            imports=imports,
            raw_content="test_workflow = func1"
        )
        
        result_dict = workflow_def.to_dict()
        
        assert result_dict["name"] == "test_workflow"
        assert result_dict["type"] == "pipeline"
        assert len(result_dict["steps"]) == 1
        assert len(result_dict["imports"]) == 1
        assert result_dict["raw_content"] == "test_workflow = func1"
    
    def test_function_definition_to_dict(self):
        """Test FunctionDefinition to_dict method"""
        func_def = FunctionDefinition(
            name="test_func",
            parameters=["input", "config"],
            return_type="str",
            body="return input"
        )
        
        result_dict = func_def.to_dict()
        
        assert result_dict["name"] == "test_func"
        assert result_dict["parameters"] == ["input", "config"]
        assert result_dict["return_type"] == "str"
        assert result_dict["body"] == "return input"