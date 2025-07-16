"""
Prompt templates for agent generation and related server logic.
"""


def get_multi_file_agent_generation_prompt(intentions: str, current_code: str = "") -> str:
    """
    Returns the multi-file agent generation prompt for the LLM.
    """
    return f'''
You are an expert Dana language developer. Based on the user's intentions, generate a well-structured multi-file Dana agent project following proven patterns.

User Intentions:
{intentions}

IMPORTANT: You MUST generate EXACTLY 6 files: main.na, workflows.na, methods.na, common.na, knowledges.na, and tools.na. Even if some files only contain comments, all 6 files must be present.

Generate a multi-file Dana agent project with the following structure, following the established patterns:

For complex agents, organize code into these files:
1. **main.na**        - Main agent definition and orchestration (replaces agents.na)
2. **workflows.na**   - Workflow orchestration using pipe operators
3. **methods.na**     - Core processing methods and utilities
4. **common.na**      - Shared data structures, prompts, and utilities (must include structs and constants)
5. **knowledges.na**  - Knowledge base/resource configurations
6. **tools.na**       - Tool definitions and integrations

For simpler agents, use a minimal structure:
1. **main.na**        - Main agent definition with solve() method
2. **methods.na**     - Helper methods (if needed)

RESPONSE FORMAT:
You MUST generate ALL 6 files in this exact format with FILE_START and FILE_END markers. Do not skip any files.
IMPORTANT: Generate ONLY pure Dana code between the markers - NO markdown code blocks, NO ```python, NO ```dana, NO explanatory text!

FILE_START:main.na
from workflows import workflow
from common import [YourDataStruct]

agent [AgentName]:
    name: str = "[Descriptive Agent Name]"
    description: str = "[Brief description of what the agent does]"

def solve(self : [AgentName], query: str) -> str:
    package = [YourDataStruct](query=query)
    return workflow(package)

this_agent = [AgentName]()

print(this_agent.solve("Example query"))
FILE_END:main.na

FILE_START:workflows.na
from methods import [method1]
from methods import [method2]
from methods import [method3]

workflow = [method1] | [method2] | [method3]
FILE_END:workflows.na

FILE_START:methods.na
from tools import [tool_name]
from common import [PROMPT_CONSTANT]
from common import [DataStruct]

def [method_name](package: [DataStruct]) -> [DataStruct]:
    # Process the package and return modified version
    result = reason([PROMPT_CONSTANT].format(user_input=package.query))
    package.field = result
    return package

def [another_method](package: [DataStruct]) -> [DataStruct]:
    # Example method that uses tools
    if package.some_condition:
        package.result = str([tool_name].query(package.query))
    return package

def [final_method](package: [DataStruct]) -> str:
    # Final method that returns the result
    prompt = [PROMPT_CONSTANT].format(user_input=package.query, data=package.result)
    return reason(prompt)
FILE_END:methods.na

FILE_START:common.na
# Define prompt constants first
[PROMPT_NAME] = """
You are [RoleDescription], an expert [domain] for [purpose].

**Task**
[Clear task description]

**Process**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Output Format**
[Clear output format instructions]

---

USER_REQUEST: 
{{user_input}}
"""

[ANOTHER_PROMPT] = """
[Another well-structured prompt template]

USER_REQUEST: 
{{user_input}}
DATA: 
{{data}}
"""

# Define data structures
struct [YourDataStruct]:
    query: str
    field1: str = ""
    field2: bool = False
    result: str = "<empty>"
FILE_END:common.na

FILE_START:knowledges.na
"""Knowledge base/resource configurations.

Knowledge Description:
- Describe the knowledge sources, databases, RAG resources, and their roles in the agent.
- If no knowledge sources are needed, explain why the agent works without them.
"""

# Example knowledge resource definitions (include only if needed):
# knowledge_base = use("rag", sources=["path/to/documents"])
# database = use("database", connection_string="...")
# api_knowledge = use("api", endpoint="...")

# If no knowledge sources are needed, you can include this comment:
# No external knowledge sources required - this agent uses only built-in knowledge and reasoning
FILE_END:knowledges.na

FILE_START:tools.na
"""Tool definitions and integrations.

Tools Description:
- List and describe each tool or integration, its purpose, and how it is used in the agent.
- If no external tools are needed, explain why the agent can work without them.
"""

# Example tool definitions (include only if needed):
# rag_resource = use("rag", sources=["path/to/documents"])
# database_tool = use("database", connection_string="...")
# api_service = use("api", endpoint="...")

# If no tools are needed, you can include this comment:
# No external tools required - this agent uses only built-in reasoning capabilities
FILE_END:tools.na

CRITICAL GUIDELINES - FOLLOW THESE EXACTLY:
1. **GENERATE ALL 6 FILES**: You MUST generate all 6 files (main.na, workflows.na, methods.na, common.na, knowledges.na, tools.na) even if some only contain comments
2. **File Structure**: Use main.na instead of agents.na
3. **Agent Pattern**: Include solve(self: AgentName, query: str) -> str method
4. **Workflow Pattern**: Use pipe operators (|) to chain methods: method1 | method2 | method3
5. **Data Flow**: Pass a struct through the pipeline, each method modifying and returning it
6. **Common.na**: Must include both prompt constants and data structures
7. **Prompts**: Use structured prompts with clear task descriptions, process steps, and output formats
8. **Tools File**: ALWAYS generate tools.na - if no tools needed, include only comments explaining this
9. **Imports**: Use proper Dana syntax: `import methods` (no .na extension)
10. **Final Method**: Last method in pipeline should return final result (string)
11. **Agent Instance**: Create instance with `this_agent = AgentName()` and include example usage

MANDATORY FILE REQUIREMENTS:
- main.na: ALWAYS required - main agent definition
- workflows.na: ALWAYS required - workflow definition (even if simple)
- methods.na: ALWAYS required - processing methods
- common.na: ALWAYS required - data structures and prompts
- knowledges.na: ALWAYS required - knowledge sources or comment explaining none needed
- tools.na: ALWAYS required - tools or comment explaining no tools needed

EXAMPLE PATTERNS TO FOLLOW:
- Use reason() for LLM calls with formatted prompts
- Use str() to convert tool results to strings
- Check conditions before expensive operations
- Format prompts with .format() method
- Use descriptive variable names and clear comments

CRITICAL OUTPUT REQUIREMENTS:
- Generate ONLY pure Dana code between FILE_START and FILE_END markers
- Do NOT include markdown code blocks like ```python, ```dana, or ```
- Do NOT include any explanatory text or comments outside the code
- Each file should contain only the actual Dana code content
- NO markdown formatting, NO code block markers, NO additional text

Current code to improve (if any):
{current_code}

FINAL REMINDER: Your response MUST contain ALL 6 files with proper FILE_START and FILE_END markers:
1. FILE_START:main.na ... FILE_END:main.na
2. FILE_START:workflows.na ... FILE_END:workflows.na  
3. FILE_START:methods.na ... FILE_END:methods.na
4. FILE_START:common.na ... FILE_END:common.na
5. FILE_START:knowledges.na ... FILE_END:knowledges.na
6. FILE_START:tools.na ... FILE_END:tools.na

Do not skip any files. If a file doesn't need actual code, include descriptive comments explaining its purpose.
'''
