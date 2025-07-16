"""
CodeHandler: Utilities for code build, extraction, and manipulation in agent generation.
"""

import re

class CodeHandler:
    @staticmethod
    def clean_generated_code(code: str) -> str:
        if not code:
            return ""

        # Remove markdown code blocks
        if "```dana" in code:
            start = code.find("```dana") + 7
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```python" in code:
            start = code.find("```python") + 9
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```na" in code:
            start = code.find("```na") + 5
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```" in code:
            start = code.find("```") + 3
            newline_pos = code.find("\n", start)
            if newline_pos != -1:
                start = newline_pos + 1
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()

        # Remove any remaining markdown artifacts
        lines = code.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are just markdown code block markers
            if stripped in ["```", "```python", "```dana", "```na"]:
                continue
            cleaned_lines.append(line)

        code = "\n".join(cleaned_lines).strip()
        return code

    @staticmethod
    def parse_multi_file_response(response: str) -> dict:
        files = []
        project_name = "Generated Agent"
        project_description = "Dana agent generated from user requirements"
        lines = response.split("\n")
        current_file = None
        current_content = []
        for line in lines:
            if line.startswith("FILE_START:"):
                if current_file:
                    files.append(
                        {
                            "filename": current_file,
                            "content": "\n".join(current_content).strip(),
                            "file_type": CodeHandler.determine_file_type(current_file),
                            "description": CodeHandler.get_file_description(current_file),
                            "dependencies": CodeHandler.extract_dependencies("\n".join(current_content)),
                        }
                    )
                current_file = line.split(":", 1)[1].strip()
                current_content = []
            elif line.startswith("FILE_END:"):
                if current_file:
                    files.append(
                        {
                            "filename": current_file,
                            "content": "\n".join(current_content).strip(),
                            "file_type": CodeHandler.determine_file_type(current_file),
                            "description": CodeHandler.get_file_description(current_file),
                            "dependencies": CodeHandler.extract_dependencies("\n".join(current_content)),
                        }
                    )
                    current_file = None
                    current_content = []
            elif current_file:
                # Skip markdown code block markers
                if line.strip().startswith("```"):
                    continue
                current_content.append(line)
        if current_file and current_content:
            files.append(
                {
                    "filename": current_file,
                    "content": "\n".join(current_content).strip(),
                    "file_type": CodeHandler.determine_file_type(current_file),
                    "description": CodeHandler.get_file_description(current_file),
                    "dependencies": CodeHandler.extract_dependencies("\n".join(current_content)),
                }
            )

        # Ensure all required files are present
        project = {"files": files, "main_file": "main.na", "name": project_name, "description": project_description}

        project = CodeHandler.ensure_all_files_present(project)

        # --- BEGIN PATCH: Ensure all imported tools are defined in tools.na ---
        # Find all symbols imported from tools in methods.na
        methods_file = next((f for f in project["files"] if f["filename"] == "methods.na"), None)
        tools_file = next((f for f in project["files"] if f["filename"] == "tools.na"), None)
        if methods_file and tools_file:
            import_re = re.compile(r"from tools import ([a-zA-Z0-9_]+)")
            imported_tools = set(import_re.findall(methods_file["content"]))
            # Find all defined symbols in tools.na (simple assignment or def)
            defined_tools = set()
            for line in tools_file["content"].split("\n"):
                line = line.strip()
                if line.startswith("def "):
                    defined_tools.add(line.split()[1].split("(")[0])
                elif "=" in line:
                    defined_tools.add(line.split("=")[0].strip())
            # Add stubs for missing tools
            missing_tools = imported_tools - defined_tools
            if missing_tools:
                stub_lines = [
                    f"def {tool}(query: str) -> str:\n    return reason(f'Reasoning for: {{query}}')  # Auto-generated stub"
                    for tool in missing_tools
                ]
                if tools_file["content"] and not tools_file["content"].endswith("\n"):
                    tools_file["content"] += "\n"
                tools_file["content"] += "\n" + "\n\n".join(stub_lines)
        # --- END PATCH ---

        # Clean up any remaining markdown artifacts from all files
        for file_info in project["files"]:
            file_info["content"] = CodeHandler.clean_generated_code(file_info["content"])

        return project

    @staticmethod
    def ensure_all_files_present(project: dict) -> dict:
        """Ensure all required files are present in the project."""
        required_files = ["main.na", "workflows.na", "methods.na", "common.na", "knowledges.na", "tools.na"]
        existing_files = {f["filename"] for f in project["files"]}

        for required_file in required_files:
            if required_file not in existing_files:
                # Create missing file with appropriate template
                template_content = CodeHandler.get_file_template(required_file)
                project["files"].append(
                    {
                        "filename": required_file,
                        "content": template_content,
                        "file_type": CodeHandler.determine_file_type(required_file),
                        "description": CodeHandler.get_file_description(required_file),
                        "dependencies": CodeHandler.extract_dependencies(template_content),
                    }
                )

        # Clean up any remaining markdown artifacts from all files
        for file_info in project["files"]:
            file_info["content"] = CodeHandler.clean_generated_code(file_info["content"])

        return project

    @staticmethod
    def get_file_template(filename: str) -> str:
        """Get template content for missing files."""
        templates = {
            "main.na": """from workflows import workflow
from common import AgentPackage

agent GeneratedAgent:
    name: str = "Generated Agent"
    description: str = "A generated agent that helps with various tasks"

def solve(self : GeneratedAgent, query: str) -> str:
    package = AgentPackage(query=query)
    return workflow(package)

this_agent = GeneratedAgent()

print(this_agent.solve("Example query"))""",
            "workflows.na": """from methods import process_request
from methods import generate_response

workflow = process_request | generate_response""",
            "methods.na": """from common import AgentPackage

def process_request(package: AgentPackage) -> AgentPackage:
    # Process the user request
    package.processed = True
    return package

def generate_response(package: AgentPackage) -> str:
    # Generate response using reasoning
    return reason(f"Help me with: {package.query}")""",
            "common.na": '''# Data structures for the agent
struct AgentPackage:
    query: str
    processed: bool = False
    result: str = ""''',
            "knowledges.na": '''"""Knowledge base/resource configurations.

Knowledge Description:
- No external knowledge sources required for this agent
- Uses only built-in knowledge and reasoning capabilities
"""

# No external knowledge sources needed for this agent''',
            "tools.na": '''"""Tool definitions and integrations.

Tools Description:
- No external tools required for this agent
- Uses only built-in reasoning capabilities
"""

# No external tools required - this agent uses only built-in reasoning capabilities''',
        }

        return templates.get(filename, f"# {filename} - Generated template file")

    @staticmethod
    def determine_file_type(filename: str) -> str:
        if filename == "main.na":
            return "agent"
        elif filename == "workflows.na":
            return "workflow"
        elif filename == "knowledges.na":
            return "resources"
        elif filename == "methods.na":
            return "methods"
        elif filename == "tools.na":
            return "tools"
        elif filename == "common.na":
            return "common"
        return "other"

    @staticmethod
    def get_file_description(filename: str) -> str:
        descriptions = {
            "main.na": "Main agent definition and orchestration",
            "workflows.na": "Workflow orchestration and pipelines",
            "knowledges.na": "Resource configurations (RAG, databases, APIs)",
            "methods.na": "Core processing methods and utilities",
            "tools.na": "Tool definitions and integrations",
            "common.na": "Shared data structures and utilities",
        }
        return descriptions.get(filename, "Dana agent file")

    @staticmethod
    def extract_dependencies(content: str) -> list[str]:
        dependencies = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("import ") and not line.endswith(".py"):
                dep = line.replace("import ", "").strip()
                if dep not in dependencies:
                    dependencies.append(dep)
            elif line.startswith("from ") and " import " in line:
                dep = line.split(" import ")[0].replace("from ", "").strip()
                if not dep.endswith(".py") and dep not in dependencies:
                    dependencies.append(dep)
        return dependencies

    @staticmethod
    def get_fallback_template() -> str:
        return '''"""Basic Agent Template."""

# Agent Card declaration
agent BasicAgent:
    name : str = "Basic Agent"
    description : str = "A basic agent that can handle general queries."

# Agent's problem solver
def solve(basic_agent : BasicAgent, problem : str):
    """Solve a problem using reasoning."""
    return reason(f"Help me to answer the question: {problem}")

# Example usage
example_input = "Hello, how can you help me?"
print(solve(BasicAgent(), example_input))'''
