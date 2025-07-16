"""
Prompt templates for agent generation and related server logic.
"""

def get_multi_file_agent_generation_prompt(intentions: str, current_code: str = "") -> str:
    """
    Returns the multi-file agent generation prompt for the LLM.
    """
    return f'''
You are an expert Dana language developer. Based on the user's intentions, generate a well-structured multi-file Dana agent project.

User Intentions:
{intentions}

Generate a multi-file Dana agent project with the following structure:

For complex agents, organize code into these files:
1. **agents.na**      - Main agent definition and orchestration
2. **workflows.na**   - Workflow orchestration and pipelines (include a workflows description section at the top)
3. **methods.na**     - Core processing methods and utilities
4. **knowledges.na**  - Knowledge base/resource configurations (include a knowledge description section at the top)
5. **tools.na**       - Tool definitions and integrations (include a tools description section at the top)
6. **common.na**      - Shared data structures and utilities

For simpler agents, use a minimal structure:
1. **agents.na**      - Main agent definition
2. **methods.na**     - Helper methods (if needed)

RESPONSE FORMAT:
Generate your response in this exact format with FILE_START and FILE_END markers:

FILE_START:agents.na
"""Main agent definition and orchestration."""

import methods
import workflows
import knowledges
import tools
import common

agent [AgentName]:
    name: str = "[Descriptive Agent Name]"
    description: str = "[Brief description]"
    resources: list = []  # populate if resources needed

def solve(agent_instance: [AgentName], problem: str) -> str:
    return main_workflow(problem)
FILE_END:agents.na

FILE_START:workflows.na
"""Workflow orchestration and pipelines.

Workflows Description:
- List and describe each workflow and its purpose.
- Each workflow should be defined as a pipe of multiple methods, e.g., process_pipeline = methods.method_1 | methods.method_2 | methods.method_3
- There can be multiple workflows, each with a clear name and description.
"""

import methods

# Example workflow definition:
# process_pipeline = methods.method_1 | methods.method_2 | methods.method_3
# data_cleaning_workflow = methods.clean | methods.normalize | methods.validate

# Define your workflows below:

FILE_END:workflows.na

FILE_START:methods.na
"""Core processing methods and utilities."""

def process_request(request: str) -> str:
    return reason(f"Process this request: " + request)

def validate_input(input_data: str) -> bool:
    return len(input_data.strip()) > 0
FILE_END:methods.na

FILE_START:knowledges.na
"""Knowledge base/resource configurations.

Knowledge Description:
- Describe the knowledge sources, databases, RAG resources, and their roles in the agent.
- List any important files, APIs, or data sources used.
"""

# RAG resources
knowledge_base = use("rag", sources=["document.pdf"])

# Database resources
# database = use("database", connection_string="...")

# API resources
# api_service = use("api", endpoint="...")
FILE_END:knowledges.na

FILE_START:tools.na
"""Tool definitions and integrations.

Tools Description:
- List and describe each tool or integration, its purpose, and how it is used in the agent.
- Include any external APIs, plugins, or custom tools.
"""

# Define tools or external integrations here
# Example:
# calculator_tool = use("calculator")
# web_search_tool = use("web_search")
FILE_END:tools.na

FILE_START:common.na
"""Shared data structures and utilities."""

struct AgentRequest:
    content: str
    timestamp: str
    priority: str = "normal"

def log_request(request: AgentRequest) -> None:
    log(f"Processing request: {{request.content}}")
FILE_END:common.na

IMPORTANT GUIDELINES:
1. Only create files that are actually needed for the agent.
2. Use proper Dana import syntax: `import methods` (no .na extension).
3. Only add RAG resources if document/knowledge retrieval is specifically needed.
4. Keep files focused and avoid unnecessary complexity.
5. Use proper Dana syntax and patterns.
6. Include FILE_START and FILE_END markers exactly as shown.

Current code to improve (if any):
{current_code}
''' 