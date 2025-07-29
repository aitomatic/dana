"""
Prompt templates for agent generation and related server logic.
"""


def get_multi_file_agent_generation_prompt(intentions: str, current_code: str = "", has_docs_folder: bool = False) -> str:
    """
    Returns the multi-file agent generation prompt for the LLM, aligned with the normal_chat_with_document example, but including knowledge.na as a required file and conditional RAG resource usage.
    """
    rag_tools_block = 'rag_resource = use("rag", sources=["./docs"])'
    rag_import_block = "from tools import rag_resource\n"
    rag_search_block = "    package.retrieval_result = str(rag_resource.query(query))"
    return f'''
You are Dana, an expert Dana language developer. Based on the user's intentions, generate a training project for Georgia that follows the modular, workflow-based pattern as in the 'normal_chat_with_document' example.

User Intentions:
{intentions}

IMPORTANT: You MUST generate EXACTLY 6 files: main.na, workflows.na, methods.na, common.na, knowledge.na, and tools.na. Even if some files only contain comments, all 6 files must be present.

Generate a multi-file Dana training project for Georgia with the following structure, following the established patterns:

1. **main.na**        - Main agent definition and orchestration (entrypoint)
2. **workflows.na**   - Workflow orchestration using pipe operators
3. **methods.na**     - Core processing methods and utilities
4. **common.na**      - Shared data structures, prompt templates, and constants (must include structs and constants)
5. **knowledge.na**  - Knowledge base/resource configurations (describe or define knowledge sources, or explain if not needed)
6. **tools.na**       - Tool/resource definitions and integrations (always define rag_resource for ./docs)

RESPONSE FORMAT:
You MUST generate ALL 6 files in this exact format with FILE_START and FILE_END markers. Do not skip any files.
IMPORTANT: Generate ONLY pure Dana code between the markers - NO markdown code blocks, NO ```python, NO ```dana, NO explanatory text!

FILE_START:main.na
from workflows import workflow
from common import RetrievalPackage

agent RetrievalExpertAgent:
    name: str = "RetrievalExpertAgent"
    description: str = "A retrieval expert agent that can answer questions about documents"

def solve(self : RetrievalExpertAgent, query: str) -> str:
    package = RetrievalPackage(query=query)
    return workflow(package)

this_agent = RetrievalExpertAgent()

FILE_END:main.na

FILE_START:workflows.na
from methods import should_use_rag
from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = should_use_rag | refine_query | search_document | get_answer
FILE_END:workflows.na

FILE_START:methods.na
{rag_import_block}from common import QUERY_GENERATION_PROMPT
from common import QUERY_DECISION_PROMPT
from common import ANSWER_PROMPT
from common import RetrievalPackage

def search_document(package: RetrievalPackage) -> RetrievalPackage:
    query = package.query
    if package.refined_query != "":
        query = package.refined_query
{rag_search_block}
    return package

def refine_query(package: RetrievalPackage) -> RetrievalPackage:
    if package.should_use_rag:
        package.refined_query = reason(QUERY_GENERATION_PROMPT.format(user_input=package.query))
    return package

def should_use_rag(package: RetrievalPackage) -> RetrievalPackage:
    package.should_use_rag = reason(QUERY_DECISION_PROMPT.format(user_input=package.query))
    return package

def get_answer(package: RetrievalPackage) -> str:
    prompt = ANSWER_PROMPT.format(user_input=package.query, retrieved_docs=package.retrieval_result)
    return reason(prompt)
FILE_END:methods.na

FILE_START:common.na
QUERY_GENERATION_PROMPT = """
You are **QuerySmith**, an expert search-query engineer for a Retrieval-Augmented Generation (RAG) pipeline.

**Task**  
Given the USER_REQUEST below, craft **one** concise query string (≤ 12 tokens) that will maximize recall of the most semantically relevant documents.

**Process**  
1. **Extract Core Concepts** – identify the main entities, actions, and qualifiers.  
2. **Select High-Signal Terms** – keep nouns/verbs with the strongest discriminative power; drop stop-words and vague modifiers.  
3. **Synonym Check** – if a well-known synonym outperforms the original term in typical search engines, substitute it.  
4. **Context Packing** – arrange terms from most to least important; group multi-word entities in quotes ("like this").  
5. **Final Polish** – ensure the string is lowercase, free of punctuation except quotes, and contains **no** explanatory text.

**Output Format**  
Return **only** the final query string on a single line. No markdown, labels, or additional commentary.

---

USER_REQUEST: 
{{user_input}}
"""

QUERY_DECISION_PROMPT = """
You are **RetrievalGate**, a binary decision agent guarding a Retrieval-Augmented Generation (RAG) pipeline.

Task  
Analyze the USER_REQUEST below and decide whether external document retrieval is required to answer it accurately.

Decision Rules  
1. External-Knowledge Need – Does the request demand up-to-date facts, statistics, citations, or niche info unlikely to be in the model's parameters?  
2. Internal Sufficiency – Could the model satisfy the request with its own reasoning, creativity, or general knowledge?  
3. Explicit User Cue – If the user explicitly asks to "look up," "cite," "fetch," "search," or mentions a source/corpus, retrieval is required.  
4. Ambiguity Buffer – When uncertain, default to retrieval (erring on completeness).

Output Format  
Return **only** one lowercase Boolean literal on a single line:  
- `true`  → retrieval is needed  
- `false` → retrieval is not needed

---

USER_REQUEST: 
{{user_input}}
"""

ANSWER_PROMPT = """
You are **RAGResponder**, an expert answer-composer for a Retrieval-Augmented Generation pipeline.

────────────────────────────────────────
INPUTS
• USER_REQUEST: The user's natural-language question.  
• RETRIEVED_DOCS: *Optional* — multiple objects, each with:
    - metadata
    - content
  If no external retrieval was performed, RETRIEVED_DOCS will be empty.

────────────────────────────────────────
TASK  
Produce a single, well-structured answer that satisfies USER_REQUEST.

────────────────────────────────────────
GUIDELINES  
1. **Grounding Strategy**  
   • If RETRIEVED_DOCS is **non-empty**, read the top-scoring snippets first.  
   • Extract only the facts truly relevant to the question.  
   • Integrate those facts into your reasoning and cite them inline as **[doc_id]**.

2. **Fallback Strategy**  
   • If RETRIEVED_DOCS is **empty**, rely on your internal knowledge.  
   • Answer confidently but avoid invented specifics (no hallucinations).

3. **Citation Rules**  
   • Cite **every** external fact or quotation with its matching [doc_id].  
   • Do **not** cite when drawing solely from internal knowledge.  
   • Never reference retrieval *scores* or expose raw snippets.

4. **Answer Quality**  
   • Prioritize clarity, accuracy, and completeness.  
   • Use short paragraphs, bullets, or headings if it helps readability.  
   • Maintain a neutral, informative tone unless the user requests otherwise.

────────────────────────────────────────
OUTPUT FORMAT  
Return **only** the answer text—no markdown fences, JSON, or additional labels.
Citations must appear inline in square brackets, e.g.:
    Solar power capacity grew by 24 % in 2024 [energy_outlook_2025].

────────────────────────────────────────
USER_REQUEST: 
{{user_input}}
RETRIEVED_DOCS: 
{{retrieved_docs}}
"""

struct RetrievalPackage:
    query: str
    refined_query: str = ""
    should_use_rag: bool = False
    retrieval_result: str = "<empty>"
FILE_END:common.na

FILE_START:knowledge.na
"""Knowledge base/resource configurations.

Knowledge Description:
- Describe the knowledge sources, databases, RAG resources, and their roles in the agent.
- If no knowledge sources are needed, explain why the agent works without them.
"""

# Example knowledge resource definitions (include only if needed):
# knowledge_base = use("rag", sources=["./docs"])
# database = use("database", connection_string="...")
# api_knowledge = use("api", endpoint="...")

# If no knowledge sources are needed, you can include this comment:
# No external knowledge sources required - this agent uses only built-in knowledge and reasoning
FILE_END:knowledge.na

FILE_START:tools.na
{rag_tools_block}

FILE_END:tools.na

CRITICAL GUIDELINES - FOLLOW THESE EXACTLY:
1. **GENERATE ALL 6 FILES**: You MUST generate all 6 files (main.na, workflows.na, methods.na, common.na, knowledge.na, tools.na) even if some only contain comments
2. **File Structure**: Use main.na as the entrypoint
3. **Agent Pattern**: Include solve(self: AgentName, query: str) -> str method
4. **Workflow Pattern**: Use pipe operators (|) to chain methods: should_use_rag | refine_query | search_document | get_answer
5. **Data Flow**: Pass a struct through the pipeline, each method modifying and returning it
6. **common.na**: Must include both prompt constants and data structures
7. **Prompts**: Use structured prompts with clear task descriptions, process steps, and output formats
8. **tools.na**: ALWAYS generate tools.na - if no tools needed, include only comments explaining this
9. **Imports**: Use proper Dana syntax: import methods (no .na extension)
10. **Final Method**: Last method in pipeline should return final result (string)
11. **Agent Instance**: Create instance with this_agent = AgentName() and include example usage

MANDATORY FILE REQUIREMENTS:
- main.na: ALWAYS required - main agent definition
- workflows.na: ALWAYS required - workflow definition (even if simple)
- methods.na: ALWAYS required - processing methods
- common.na: ALWAYS required - data structures and prompts
- knowledge.na: ALWAYS required - knowledge sources or comment explaining none needed
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
5. FILE_START:knowledge.na ... FILE_END:knowledge.na
6. FILE_START:tools.na ... FILE_END:tools.na

Do not skip any files. If a file doesn't need actual code, include descriptive comments explaining its purpose.
'''
