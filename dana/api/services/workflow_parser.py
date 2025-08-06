"""
Workflow Parser for Dana workflows.na files.

This module provides functionality to parse workflows.na files and extract
workflow definitions, pipeline operations, and function chains.
"""

import re
import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorkflowImport:
    """Represents an import statement in workflows.na"""

    module: str
    function: str

    def __str__(self) -> str:
        return f"from {self.module} import {self.function}"


@dataclass
class PipelineStep:
    """Represents a step in a pipeline workflow"""

    function_name: str
    order: int

    def __str__(self) -> str:
        return self.function_name


@dataclass
class WorkflowDefinition:
    """Represents a complete workflow definition"""

    name: str
    type: str  # 'pipeline' or 'function'
    steps: list[PipelineStep]
    imports: list[WorkflowImport]
    raw_content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow definition to JSON-friendly dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "steps": [{"function_name": step.function_name, "order": step.order} for step in self.steps],
            "imports": [{"module": imp.module, "function": imp.function} for imp in self.imports],
            "raw_content": self.raw_content,
        }


@dataclass
class FunctionDefinition:
    """Represents a function definition in workflows.na"""

    name: str
    parameters: list[str]
    return_type: str | None
    body: str

    def to_dict(self) -> dict[str, Any]:
        """Convert function definition to JSON-friendly dictionary"""
        return {"name": self.name, "parameters": self.parameters, "return_type": self.return_type, "body": self.body}


@dataclass
class ParsedWorkflow:
    """Complete parsed workflow file"""

    workflow_definitions: list[WorkflowDefinition]
    function_definitions: list[FunctionDefinition]
    imports: list[WorkflowImport]
    raw_content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert parsed workflow to JSON-friendly dictionary"""
        return {
            "workflow_definitions": [wd.to_dict() for wd in self.workflow_definitions],
            "function_definitions": [fd.to_dict() for fd in self.function_definitions],
            "imports": [{"module": imp.module, "function": imp.function} for imp in self.imports],
            "has_pipeline_workflows": any(wd.type == "pipeline" for wd in self.workflow_definitions),
            "has_function_definitions": len(self.function_definitions) > 0,
            "total_workflows": len(self.workflow_definitions),
            "total_functions": len(self.function_definitions),
            "raw_content": self.raw_content,
        }


class WorkflowParser:
    """Parser for Dana workflows.na files"""

    def __init__(self):
        # Regex patterns for parsing
        self.import_pattern = re.compile(r"^from\s+(\w+)\s+import\s+(\w+)$", re.MULTILINE)
        self.pipeline_pattern = re.compile(r"^(\w+)\s*=\s*(.+?)$", re.MULTILINE)
        self.function_def_pattern = re.compile(r"^def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+?))?\s*\{(.*?)\}$", re.MULTILINE | re.DOTALL)

    def parse_workflows_file(self, content: str) -> ParsedWorkflow:
        """
        Parse a workflows.na file content and extract workflow information.

        Args:
            content: The raw content of the workflows.na file

        Returns:
            ParsedWorkflow object containing all extracted information
        """
        logger.info("Starting workflow file parsing")

        # Clean content
        cleaned_content = self._clean_content(content)

        # Extract imports
        imports = self._extract_imports(cleaned_content)
        logger.info(f"Found {len(imports)} imports")

        # Extract pipeline workflows
        workflow_definitions = self._extract_pipeline_workflows(cleaned_content, imports)
        logger.info(f"Found {len(workflow_definitions)} pipeline workflows")

        # Extract function definitions
        function_definitions = self._extract_function_definitions(cleaned_content)
        logger.info(f"Found {len(function_definitions)} function definitions")

        parsed_workflow = ParsedWorkflow(
            workflow_definitions=workflow_definitions, function_definitions=function_definitions, imports=imports, raw_content=content
        )

        logger.info("Workflow file parsing completed successfully")
        return parsed_workflow

    def _clean_content(self, content: str) -> str:
        """Clean and normalize the content for parsing"""
        # Remove comments (but preserve multi-line strings)
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove single line comments, but not comments inside strings
            if "//" in line and not self._is_in_string(line, line.find("//")):
                line = line[: line.find("//")]

            # Remove C-style comments start
            if "/*" in line and not self._is_in_string(line, line.find("/*")):
                comment_start = line.find("/*")
                line = line[:comment_start]

            cleaned_lines.append(line.rstrip())

        # Join and remove empty lines
        cleaned_content = "\n".join(line for line in cleaned_lines if line.strip())
        return cleaned_content

    def _is_in_string(self, line: str, position: int) -> bool:
        """Check if a position in a line is inside a string literal"""
        quote_count = 0
        for i in range(position):
            if line[i] == '"' and (i == 0 or line[i - 1] != "\\"):
                quote_count += 1
        return quote_count % 2 == 1

    def _extract_imports(self, content: str) -> list[WorkflowImport]:
        """Extract import statements from the content"""
        imports = []
        matches = self.import_pattern.findall(content)

        for module, function in matches:
            imports.append(WorkflowImport(module=module, function=function))

        return imports

    def _extract_pipeline_workflows(self, content: str, imports: list[WorkflowImport]) -> list[WorkflowDefinition]:
        """Extract pipeline workflow definitions (e.g., workflow = func1 | func2 | func3)"""
        workflows = []
        matches = self.pipeline_pattern.findall(content)

        for workflow_name, pipeline_content in matches:
            # Skip if this looks like a function definition
            if "def " in pipeline_content or "{" in pipeline_content:
                continue

            # Check if this is a pipeline (contains | operator)
            if "|" in pipeline_content:
                steps = self._parse_pipeline_steps(pipeline_content)

                workflow = WorkflowDefinition(
                    name=workflow_name, type="pipeline", steps=steps, imports=imports, raw_content=f"{workflow_name} = {pipeline_content}"
                )
                workflows.append(workflow)

        return workflows

    def _parse_pipeline_steps(self, pipeline_content: str) -> list[PipelineStep]:
        """Parse pipeline steps from a pipeline string (e.g., 'func1 | func2 | func3')"""
        steps = []
        # Split by | and clean each function name
        function_names = [name.strip() for name in pipeline_content.split("|")]

        for i, function_name in enumerate(function_names):
            # Remove any extra whitespace or parentheses
            function_name = function_name.strip()
            if function_name:
                steps.append(PipelineStep(function_name=function_name, order=i))

        return steps

    def _extract_function_definitions(self, content: str) -> list[FunctionDefinition]:
        """Extract function definitions from the content"""
        functions = []
        matches = self.function_def_pattern.findall(content)

        for function_name, params_str, return_type, body in matches:
            # Parse parameters
            parameters = []
            if params_str.strip():
                param_parts = [p.strip() for p in params_str.split(",")]
                for param in param_parts:
                    # Extract parameter name (before :)
                    if ":" in param:
                        param_name = param.split(":")[0].strip()
                    else:
                        param_name = param
                    parameters.append(param_name)

            # Clean return type
            if return_type:
                return_type = return_type.strip()

            # Clean function body
            body = body.strip()

            function_def = FunctionDefinition(name=function_name, parameters=parameters, return_type=return_type, body=body)
            functions.append(function_def)

        return functions


def parse_workflow_file(file_path: str) -> dict[str, Any]:
    """
    Parse a workflows.na file and return workflow information in JSON-friendly format.

    Args:
        file_path: Path to the workflows.na file

    Returns:
        Dictionary containing parsed workflow information
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        parser = WorkflowParser()
        parsed_workflow = parser.parse_workflows_file(content)

        return parsed_workflow.to_dict()

    except FileNotFoundError:
        logger.error(f"Workflow file not found: {file_path}")
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        logger.error(f"Error parsing workflow file {file_path}: {e}")
        return {"error": f"Parse error: {str(e)}"}


def parse_workflow_content(content: str) -> dict[str, Any]:
    """
    Parse workflows.na content string and return workflow information in JSON-friendly format.

    Args:
        content: The raw content of a workflows.na file

    Returns:
        Dictionary containing parsed workflow information
    """
    try:
        parser = WorkflowParser()
        parsed_workflow = parser.parse_workflows_file(content)

        return parsed_workflow.to_dict()

    except Exception as e:
        logger.error(f"Error parsing workflow content: {e}")
        return {"error": f"Parse error: {str(e)}"}


# Convenience function for common use case
def extract_workflow_pipeline(content: str) -> dict[str, Any] | None:
    """
    Extract just the main pipeline workflow from content (simplified interface).

    Args:
        content: The raw content of a workflows.na file

    Returns:
        Dictionary with pipeline information or None if no pipeline found
    """
    try:
        parsed = parse_workflow_content(content)

        if parsed.get("error"):
            return None

        workflows = parsed.get("workflow_definitions", [])

        # Find the first pipeline workflow
        for workflow in workflows:
            if workflow["type"] == "pipeline":
                return {
                    "name": workflow["name"],
                    "functions": [step["function_name"] for step in workflow["steps"]],
                    "imports": parsed.get("imports", []),
                }

        return None

    except Exception as e:
        logger.error(f"Error extracting workflow pipeline: {e}")
        return None
