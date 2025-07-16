"""
CodeHandler: Utilities for code build, extraction, and manipulation in agent generation.
"""
from typing import List, Dict

class CodeHandler:
    @staticmethod
    def clean_generated_code(code: str) -> str:
        if not code:
            return ""
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
        code = code.strip()
        return code

    @staticmethod
    def parse_multi_file_response(response: str) -> dict:
        files = []
        project_name = "Generated Agent"
        project_description = "Dana agent generated from user requirements"
        lines = response.split('\n')
        current_file = None
        current_content = []
        for line in lines:
            if line.startswith('FILE_START:'):
                if current_file:
                    files.append({
                        'filename': current_file,
                        'content': '\n'.join(current_content).strip(),
                        'file_type': CodeHandler.determine_file_type(current_file),
                        'description': CodeHandler.get_file_description(current_file),
                        'dependencies': CodeHandler.extract_dependencies('\n'.join(current_content))
                    })
                current_file = line.split(':', 1)[1].strip()
                current_content = []
            elif line.startswith('FILE_END:'):
                if current_file:
                    files.append({
                        'filename': current_file,
                        'content': '\n'.join(current_content).strip(),
                        'file_type': CodeHandler.determine_file_type(current_file),
                        'description': CodeHandler.get_file_description(current_file),
                        'dependencies': CodeHandler.extract_dependencies('\n'.join(current_content))
                    })
                    current_file = None
                    current_content = []
            elif current_file:
                current_content.append(line)
        if current_file and current_content:
            files.append({
                'filename': current_file,
                'content': '\n'.join(current_content).strip(),
                'file_type': CodeHandler.determine_file_type(current_file),
                'description': CodeHandler.get_file_description(current_file),
                'dependencies': CodeHandler.extract_dependencies('\n'.join(current_content))
            })
        return {
            'files': files,
            'main_file': 'agents.na',
            'name': project_name,
            'description': project_description
        }

    @staticmethod
    def determine_file_type(filename: str) -> str:
        if filename == 'agents.na':
            return 'agent'
        elif filename == 'workflows.na':
            return 'workflow'
        elif filename == 'knowledges.na':
            return 'resources'
        elif filename == 'methods.na':
            return 'methods'
        elif filename == 'tools.na':
            return 'tools'
        elif filename == 'common.na':
            return 'common'
        return 'other'

    @staticmethod
    def get_file_description(filename: str) -> str:
        descriptions = {
            'agents.na': 'Main agent definition and orchestration',
            'workflows.na': 'Workflow orchestration and pipelines',
            'knowledges.na': 'Resource configurations (RAG, databases, APIs)',
            'methods.na': 'Core processing methods and utilities',
            'tools.na': 'Tool definitions and integrations',
            'common.na': 'Shared data structures and utilities'
        }
        return descriptions.get(filename, 'Dana agent file')

    @staticmethod
    def extract_dependencies(content: str) -> List[str]:
        dependencies = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') and not line.endswith('.py'):
                dep = line.replace('import ', '').strip()
                if dep not in dependencies:
                    dependencies.append(dep)
            elif line.startswith('from ') and ' import ' in line:
                dep = line.split(' import ')[0].replace('from ', '').strip()
                if not dep.endswith('.py') and dep not in dependencies:
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