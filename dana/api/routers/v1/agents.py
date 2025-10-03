"""
Agent routers - consolidated routing for agent-related endpoints.
Thin routing layer that delegates business logic to services.
"""

import asyncio
import base64
import logging
import os
import shutil
import tarfile
import tempfile

# import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from dana.common.utils import Misc

# from typing import List
import json
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from dana.api.core.database import engine, get_db
from dana.api.core.models import Agent, AgentChatHistory, Document
from dana.api.core.schemas import (
    AgentCreate,
    AgentGenerationRequest,
    AgentRead,
    CodeFixRequest,
    CodeFixResponse,
    CodeValidationRequest,
    CodeValidationResponse,
    DocumentRead,
    AgentUpdate,
)
from pydantic import BaseModel
from dana.api.server.server import ws_manager
from dana.common.types import BaseRequest
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.api.services.agent_deletion_service import AgentDeletionService, get_agent_deletion_service
from dana.api.services.agent_manager import AgentManager, get_agent_manager
from dana.api.services.avatar_service import AvatarService
from dana.api.services.document_service import DocumentService, get_document_service
from dana.api.services.domain_knowledge_service import (
    DomainKnowledgeService,
    get_domain_knowledge_service,
)
from dana.api.services.domain_knowledge_version_service import (
    DomainKnowledgeVersionService,
    get_domain_knowledge_version_service,
)
from dana.api.services.knowledge_status_manager import (
    KnowledgeGenerationManager,
    KnowledgeStatusManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


class AssociateDocumentsRequest(BaseModel):
    document_ids: list[int]


class AgentSuggestionRequest(BaseModel):
    user_message: str


class AgentSuggestionResponse(BaseModel):
    success: bool
    suggestions: list[dict]
    message: str


class BuildAgentFromSuggestionRequest(BaseModel):
    prebuilt_key: str
    user_input: str
    agent_name: str = "Untitled Agent"


class WorkflowInfo(BaseModel):
    workflows: list[dict]
    methods: list[str]


class TarExportRequest(BaseModel):
    agent_id: int
    include_dependencies: bool = True


class TarExportResponse(BaseModel):
    success: bool
    tar_path: str
    message: str


class TarImportRequest(BaseModel):
    agent_name: str
    agent_description: str = "Imported agent"


class TarImportResponse(BaseModel):
    success: bool
    agent_id: int
    message: str


API_FOLDER = Path(__file__).parent.parent.parent


def _copy_na_files_from_prebuilt(prebuilt_key: str, target_folder: str) -> bool:
    """Copy only .na files from a prebuilt agent asset folder into the target agent folder, preserving structure.

    Skips any files under a 'knows' directory.
    """
    try:
        source_folder = API_FOLDER / "server" / "assets" / prebuilt_key
        if not source_folder.exists():
            logger.error(f"Prebuilt agent folder not found for key: {prebuilt_key}")
            return False

        for root, _dirs, files in os.walk(source_folder):
            root_path = Path(root)
            # Skip any subtree that includes a 'knows' directory in its relative path
            try:
                rel_root = root_path.relative_to(source_folder)
                if "knows" in rel_root.parts:
                    continue
            except Exception:
                pass

            for file_name in files:
                if not file_name.endswith(".na"):
                    continue

                rel_path = root_path.relative_to(source_folder) / file_name
                if "knows" in rel_path.parts:
                    continue

                dest_path = Path(target_folder) / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root_path / file_name, dest_path)

        return True
    except Exception as e:
        logger.error(f"Error copying .na files from prebuilt '{prebuilt_key}': {e}")
        return False


def _parse_workflow_content(content: str) -> dict:
    """Parse workflows.na file content to extract workflow definitions and methods."""
    try:
        workflows = []
        methods = set()

        # Split into lines for analysis
        lines = content.strip().split("\n")
        current_workflow = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Extract methods from import statements
            if line.startswith("from methods import"):
                method_name = line.split("import", 1)[1].strip()
                methods.add(method_name)

            # Extract workflow definitions
            elif "def " in line and "(" in line and ")" in line:
                # Extract function name
                func_def = line.split("def ", 1)[1].split("(")[0].strip()
                current_workflow = {"name": func_def, "steps": []}

                # Extract pipeline steps if using | operator
                if "=" in line and "|" in line:
                    pipeline_part = line.split("=", 1)[1].strip()
                    steps = [step.strip() for step in pipeline_part.split("|")]
                    current_workflow["steps"] = steps

                workflows.append(current_workflow)

        return {"workflows": workflows, "methods": list(methods)}
    except Exception as e:
        logger.error(f"Error parsing workflow content: {e}")
        return {"workflows": [], "methods": []}


def _load_prebuilt_agents() -> list[dict]:
    """Load available prebuilt agents from assets JSON."""
    try:
        assets_path = API_FOLDER / "server" / "assets" / "prebuilt_agents.json"
        if not assets_path.exists():
            logger.warning("prebuilt_agents.json not found")
            return []

        with open(assets_path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        logger.error(f"Error loading prebuilt agents: {e}")
        return []


def _suggest_agents_with_llm(llm: LLMResource, user_message: str, prebuilt_agents: list[dict]) -> list[dict]:
    """Use LLM to suggest the 2 most relevant agents with matching percentages."""
    try:
        if not prebuilt_agents:
            return []

        # Create agent descriptions for LLM
        agent_descriptions = []
        for agent in prebuilt_agents:
            config = agent.get("config", {})
            desc = f"""
Agent: {agent.get("name", "Unknown")}
Description: {agent.get("description", "")}
Domain: {config.get("domain", "General")}
Specialties: {", ".join(config.get("specialties", []))}
Skills: {", ".join(config.get("skills", []))}
Tasks: {config.get("task", "General tasks")}
"""
            agent_descriptions.append(desc.strip())

        agents_text = "\n\n".join([f"AGENT_{i + 1}:\n{desc}" for i, desc in enumerate(agent_descriptions)])

        system_prompt = """You are an AI agent recommendation system. Your task is to analyze a user's request and recommend the 2 most relevant prebuilt agents with matching percentages.

Instructions:
1. Analyze the user's message to understand what they want to build/achieve
2. Compare it against the provided prebuilt agents
3. Return exactly 2 agents that best match the user's needs
4. For each agent, provide a matching percentage (0-100%) based on how well it fits the user's requirements
5. Provide a brief explanation of why each agent matches

Return your response in this exact JSON format:
{
  "suggestions": [
    {
      "agent_index": 0,
      "agent_name": "Agent Name",
      "matching_percentage": 85,
      "explanation": "Brief explanation of why this agent matches"
    },
    {
      "agent_index": 1,
      "agent_name": "Agent Name",
      "matching_percentage": 72,
      "explanation": "Brief explanation of why this agent matches"
    }
  ]
}

Return ONLY the JSON, no additional text."""

        user_content = f"User Request: {user_message}\n\nAvailable Agents:\n{agents_text}"

        request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ]
            }
        )

        response = llm.query_sync(request)
        if not getattr(response, "success", False):
            logger.warning(f"LLM agent suggestion failed: {getattr(response, 'error', 'unknown error')}")
            return []

        # Handle OpenAI-style response
        content = response.content
        if isinstance(content, dict) and "choices" in content:
            try:
                content = content["choices"][0]["message"]["content"]
            except Exception:
                content = ""

        # Extract text content
        if isinstance(content, dict) and "content" in content:
            text = str(content.get("content", "")).strip()
        else:
            text = str(content).strip()

        # Parse JSON response
        try:
            result = json.loads(text)
            suggestions = result.get("suggestions", [])

            # Build final response with full agent data
            final_suggestions = []
            for suggestion in suggestions[:2]:  # Limit to 2 suggestions
                agent_index = suggestion.get("agent_index", 0)
                if 0 <= agent_index < len(prebuilt_agents):
                    agent = prebuilt_agents[agent_index].copy()
                    agent["matching_percentage"] = suggestion.get("matching_percentage", 0)
                    agent["explanation"] = suggestion.get("explanation", "")
                    final_suggestions.append(agent)

            return final_suggestions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}, content: {text}")
            return []

    except Exception as e:
        logger.error(f"Error in LLM agent suggestion: {e}")
        return []


def clear_agent_cache(agent_folder_path: str) -> None:
    """
    Remove the .cache folder from an agent's directory to force RAG rebuild.

    Args:
        agent_folder_path: Path to the agent's folder
    """
    try:
        cache_folder = os.path.join(agent_folder_path, ".cache")
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder)
            logger.info(f"Cleared cache folder: {cache_folder}")
        else:
            logger.debug(f"Cache folder does not exist: {cache_folder}")
    except Exception as e:
        logger.warning(f"Failed to clear cache folder {cache_folder}: {e}")
        # Don't raise exception - cache clearing shouldn't block the main operation


async def _auto_generate_basic_agent_code(
    agent_id: int,
    agent_name: str,
    agent_description: str,
    agent_config: dict,
    agent_manager,
) -> str | None:
    """Auto-generate basic Dana code for a newly created agent."""
    try:
        logger.info(f"Auto-generating basic Dana code for agent {agent_id}: {agent_name}")

        # Create agent folder
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)

        # Create unique folder name
        safe_name = agent_name.lower().replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        folder_name = f"agent_{agent_id}_{safe_name}"
        agent_folder = agents_dir / folder_name
        agent_folder.mkdir(exist_ok=True)

        # Create docs folder
        docs_folder = agent_folder / "docs"
        docs_folder.mkdir(exist_ok=True)

        # Generate basic Dana files
        await _create_basic_dana_files(agent_folder)

        # Generate domain_knowledge.json based on agent config
        try:
            domain_knowledge_path = agent_folder / "domain_knowledge.json"
            domain = agent_config.get("domain", "General")

            # Create a basic domain knowledge structure for new agents with UUID
            root_uuid = str(uuid.uuid4())
            basic_domain_knowledge = {"root": {"id": root_uuid, "topic": domain, "children": []}}

            with open(domain_knowledge_path, "w", encoding="utf-8") as f:
                json.dump(basic_domain_knowledge, f, indent=2, ensure_ascii=False)

            logger.info(f"Created basic domain_knowledge.json for {domain}")
        except Exception as e:
            logger.error(f"Error creating domain_knowledge.json: {e}")

        logger.info(f"Successfully created agent folder and basic Dana code at: {agent_folder}")
        return str(agent_folder)

    except Exception as e:
        logger.error(f"Error auto-generating basic Dana code: {e}")
        raise e


def _add_uuids_to_domain_knowledge(domain_data: dict) -> dict:
    """Add UUIDs to existing domain knowledge structure"""

    def add_uuid_to_node(node: dict, path_so_far: list[str] = None) -> dict:
        if path_so_far is None:
            path_so_far = []

        topic_name = node.get("topic", "")

        # Build current path for stable UUID generation
        if topic_name.lower() not in ["root", "untitled"]:
            current_path = path_so_far + [topic_name]
        else:
            current_path = path_so_far

        # Generate stable UUID based on path
        path_str = " - ".join(current_path) if current_path else "root"
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        node_uuid = str(uuid.uuid5(namespace, path_str))

        # Create enhanced node with UUID
        enhanced_node = {"id": node_uuid, "topic": topic_name, "children": []}

        # Process children recursively
        for child in node.get("children", []):
            enhanced_child = add_uuid_to_node(child, current_path)
            enhanced_node["children"].append(enhanced_child)

        return enhanced_node

    if "root" not in domain_data:
        return domain_data

    # Preserve other fields and add UUID to root
    result = domain_data.copy()
    result["root"] = add_uuid_to_node(domain_data["root"])

    return result


def _ensure_domain_knowledge_has_uuids(domain_knowledge_path: str):
    """Ensure domain knowledge file has UUIDs, add them if missing"""

    try:
        with open(domain_knowledge_path, encoding="utf-8") as f:
            domain_data = json.load(f)

        # Check if root already has UUID
        if "root" in domain_data and domain_data["root"].get("id"):
            return  # Already has UUIDs

        # Add UUIDs
        enhanced_data = _add_uuids_to_domain_knowledge(domain_data)

        # Save back to file
        with open(domain_knowledge_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Added UUIDs to domain knowledge at {domain_knowledge_path}")

    except Exception as e:
        logger.error(f"Error adding UUIDs to domain knowledge: {e}")


def _create_agent_tar(agent_id: int, agent_folder: str, include_dependencies: bool = True) -> str:
    """Create a tar archive of the agent folder."""
    try:
        logger.info(f"Creating tar archive for agent {agent_id} from folder: {agent_folder}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Agent folder exists: {os.path.exists(agent_folder)}")

        # Create a temporary directory for the tar file
        temp_dir = tempfile.mkdtemp()
        tar_filename = f"agent_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        tar_path = os.path.join(temp_dir, tar_filename)
        logger.info(f"Tar file will be created at: {tar_path}")

        # Create the tar archive
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add the agent folder to the tar
            logger.info(f"Adding agent folder {agent_folder} to tar as agent_{agent_id}")
            tar.add(agent_folder, arcname=f"agent_{agent_id}")

            # Optionally include dependencies (Dana framework files)
            if include_dependencies:
                # Add core Dana files that might be needed
                dana_core_path = Path(__file__).parent.parent.parent.parent / "dana"
                logger.info(f"Looking for Dana core at: {dana_core_path}")
                if dana_core_path.exists():
                    # Add essential Dana modules
                    essential_modules = ["__init__.py", "core", "common", "frameworks"]
                    for module in essential_modules:
                        module_path = dana_core_path / module
                        if module_path.exists():
                            logger.info(f"Adding Dana module: {module_path}")
                            tar.add(module_path, arcname=f"dana/{module}")

        logger.info(f"Successfully created tar archive: {tar_path}")
        return tar_path
    except Exception as e:
        logger.error(f"Error creating tar archive for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create tar archive: {str(e)}")


async def _create_basic_dana_files(
    agent_folder,  # Path object
):
    """Create basic Dana files for the agent."""

    # TODO: Correct the content
    # Create main.na - the entry point
    main_content = """

from workflows import workflow
from common import RetrievalPackage

agent RetrievalExpertAgent:
    name: str = "RetrievalExpertAgent"
    description: str = "A retrieval expert agent that can answer questions about documents"

def solve(self : RetrievalExpertAgent, query: str) -> str:
    package = RetrievalPackage(query=query)
    return workflow(package)

this_agent = RetrievalExpertAgent()

# Example usage
# print(this_agent.solve("What is Dana language?"))
"""

    # Create common.na - shared utilities
    common_content = '''
struct RetrievalPackage:
    query: str
    refined_query: str = ""
    should_use_rag: bool = False
    retrieval_result: str = "<empty>"
QUERY_GENERATION_PROMPT = """
You are **QuerySmith**, an expert search-query engineer for a Retrieval-Augmented Generation (RAG) pipeline.

**Task**
Given the USER_REQUEST below, craft **one** concise query string (≤ 12 tokens) that will maximize recall of the most semantically relevant documents.

**Process**
1. **Extract Core Concepts** – identify the main entities, actions, and qualifiers.
2. **Select High-Signal Terms** – keep nouns/verbs with the strongest discriminative power; drop stop-words and vague modifiers.
3. **Synonym Check** – if a well-known synonym outperforms the original term in typical search engines, substitute it.
4. **Context Packing** – arrange terms from most to least important; group multi-word entities in quotes (“like this”).
5. **Final Polish** – ensure the string is lowercase, free of punctuation except quotes, and contains **no** explanatory text.

**Output Format**
Return **only** the final query string on a single line. No markdown, labels, or additional commentary.

---

USER_REQUEST:
{user_input}
"""

QUERY_DECISION_PROMPT = """
You are **RetrievalGate**, a binary decision agent guarding a Retrieval-Augmented Generation (RAG) pipeline.

Task
Analyze the USER_REQUEST below and decide whether external document retrieval is required to answer it accurately.

Decision Rules
1. External-Knowledge Need – Does the request demand up-to-date facts, statistics, citations, or niche info unlikely to be in the model’s parameters?
2. Internal Sufficiency – Could the model satisfy the request with its own reasoning, creativity, or general knowledge?
3. Explicit User Cue – If the user explicitly asks to “look up,” “cite,” “fetch,” “search,” or mentions a source/corpus, retrieval is required.
4. Ambiguity Buffer – When uncertain, default to retrieval (erring on completeness).

Output Format
Return **only** one lowercase Boolean literal on a single line:
- `true`  → retrieval is needed
- `false` → retrieval is not needed

---

USER_REQUEST:
{user_input}
"""

ANSWER_PROMPT = """
You are **RAGResponder**, an expert answer-composer for a Retrieval-Augmented Generation pipeline.

────────────────────────────────────────
INPUTS
• USER_REQUEST: The user’s natural-language question.
• RETRIEVED_DOCS: *Optional* — multiple objects, each with:
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
RETRIEVED_DOCS:
{retrieved_docs}

────────────────────────────────────────
USER_REQUEST:
{user_input}
"""
'''

    # Create tools.na - agent tools and capabilities
    tools_content = """
"""

    # Create knowledge.na - knowledge base
    knowledge_content = """
# Primary knowledge from documents
doc_knowledge = use("rag", sources=["./docs"])

# Contextual knowledge from generated knowledge files
contextual_knowledge = use("rag", sources=["./knows"])
"""

    methods_content = """
from knowledge import doc_knowledge
from knowledge import contextual_knowledge
from common import QUERY_GENERATION_PROMPT
from common import QUERY_DECISION_PROMPT
from common import ANSWER_PROMPT
from common import RetrievalPackage

def search_document(package: RetrievalPackage) -> RetrievalPackage:
    query = package.query
    if package.refined_query != "":
        query = package.refined_query

    # Query both knowledge sources
    doc_result = str(doc_knowledge.query(query))
    contextual_result = str(contextual_knowledge.query(query))

    package.retrieval_result = doc_result + contextual_result
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
"""

    # Create workflows.na - agent workflows
    workflows_content = """
from methods import should_use_rag
from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = should_use_rag | refine_query | search_document | get_answer
"""

    # Write all files
    with open(agent_folder / "main.na", "w") as f:
        f.write(main_content)

    with open(agent_folder / "common.na", "w") as f:
        f.write(common_content)

    with open(agent_folder / "methods.na", "w") as f:
        f.write(methods_content)

    with open(agent_folder / "tools.na", "w") as f:
        f.write(tools_content)

    with open(agent_folder / "knowledge.na", "w") as f:
        f.write(knowledge_content)

    with open(agent_folder / "workflows.na", "w") as f:
        f.write(workflows_content)


@router.post("/generate")
async def generate_agent(request: AgentGenerationRequest):
    """
    Generate Dana agent code based on conversation messages.

    Supports two-phase generation:
    - Phase 1 (description): Extract agent name/description from conversation
    - Phase 2 (code_generation): Generate full Dana code

    Args:
        request: AgentGenerationRequest with messages and optional agent_data

    Returns:
        Agent generation response with Dana code or agent metadata
    """
    try:
        logger.info(f"Received agent generation request: phase={request.phase}")

        # Check if mock mode is enabled
        mock_mode = os.getenv("DANA_MOCK_AGENT_GENERATION", "false").lower() == "true"

        if mock_mode:
            logger.info("Using mock agent generation")

            if request.phase == "code_generation":
                # Mock Dana code for testing
                mock_dana_code = '''"""Weather Information Agent"""

# Agent Card declaration
agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "A weather information agent that provides current weather and recommendations"
    resources : list = []

# Agent's problem solver
def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Weather help for: {problem}")'''

                return {
                    "success": True,
                    "phase": "code_generation",
                    "dana_code": mock_dana_code,
                    "agent_name": "Weather Information Agent",
                    "agent_description": "A weather information agent that provides current weather and recommendations",
                    "error": None,
                }
            else:
                # Phase 1 - description extraction
                return {
                    "success": True,
                    "phase": "description",
                    "dana_code": None,
                    "agent_name": "Weather Information Agent",
                    "agent_description": "A weather information agent that provides current weather and recommendations",
                    "error": None,
                }
        else:
            # Real implementation would go here
            # For now, return a basic implementation
            logger.warning("Real agent generation not implemented, using basic mock")

            basic_code = """# Generated Agent

agent GeneratedAgent:
    name : str = "Generated Agent"
    description : str = "A generated agent"

def solve(agent : GeneratedAgent, problem : str):
    return reason(f"Help with: {problem}")"""

            return {
                "success": True,
                "phase": request.phase,
                "dana_code": basic_code,
                "agent_name": "Generated Agent",
                "agent_description": "A generated agent",
                "error": None,
            }

    except Exception as e:
        logger.error(f"Error in agent generation endpoint: {e}")
        return {"success": False, "phase": request.phase, "dana_code": None, "agent_name": None, "agent_description": None, "error": str(e)}


@router.post("/validate-code", response_model=CodeValidationResponse)
async def validate_code(request: CodeValidationRequest):
    """
    Validate Dana code for errors and provide suggestions.

    Args:
        request: Code validation request

    Returns:
        CodeValidationResponse with validation results
    """
    try:
        logger.info("Received code validation request")

        # This would use CodeHandler to validate code
        # Placeholder implementation
        return CodeValidationResponse(success=True, is_valid=True, errors=[], warnings=[], suggestions=[])

    except Exception as e:
        logger.error(f"Error in code validation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fix-code", response_model=CodeFixResponse)
async def fix_code(request: CodeFixRequest):
    """
    Automatically fix Dana code errors.

    Args:
        request: Code fix request

    Returns:
        CodeFixResponse with fixed code
    """
    try:
        logger.info("Received code fix request")

        # This would use the agent service to fix code
        # Placeholder implementation
        return CodeFixResponse(
            success=True,
            fixed_code=request.code,  # Placeholder - would contain actual fixes
            applied_fixes=[],
            remaining_errors=[],
        )

    except Exception as e:
        logger.error(f"Error in code fix endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CRUD Operations for Agents
@router.get("/", response_model=list[AgentRead])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all agents with pagination."""
    try:
        agents = db.query(Agent).offset(skip).limit(limit).all()
        return [
            AgentRead(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                config=agent.config,
                generation_phase=agent.generation_phase,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prebuilt")
async def get_prebuilt_agents():
    """
    Get the list of pre-built agents from the JSON file.
    These agents are displayed in the Explore tab for users to browse.
    """
    try:
        # Load prebuilt agents from the assets file
        assets_path = API_FOLDER / "server" / "assets" / "prebuilt_agents.json"

        if not assets_path.exists():
            logger.warning(f"Prebuilt agents file not found at {assets_path}")
            return []

        with open(assets_path, encoding="utf-8") as f:
            prebuilt_agents = json.load(f)

        # Add mock IDs and additional UI properties for compatibility
        for i, agent in enumerate(prebuilt_agents, start=1000):  # Start from 1000 to avoid conflicts
            # agent["id"] =
            agent["is_prebuilt"] = True

            # Add UI-specific properties based on domain
            domain = agent.get("config", {}).get("domain", "Other")
            agent["avatarColor"] = {
                "Finance": "from-purple-400 to-green-400",
                "Semiconductor": "from-green-400 to-blue-400",
                "Research": "from-purple-400 to-pink-400",
                "Sales": "from-yellow-400 to-purple-400",
                "Engineering": "from-blue-400 to-green-400",
            }.get(domain, "from-gray-400 to-gray-600")

            # Add rating and accuracy for UI display
            agent["rating"] = 5  # Vary between 4.8-5.0
            agent["accuracy"] = 97 + (i % 4)  # Vary between 97-100

            # Add details from specialties and skills
            specialties = agent.get("config", {}).get("specialties", [])
            skills = agent.get("config", {}).get("skills", [])

            if specialties and skills:
                agent["details"] = f"Expert in {', '.join(specialties[:2])} with advanced skills in {', '.join(skills[:2])}"
            elif specialties:
                agent["details"] = f"Specialized in {', '.join(specialties[:3])}"
            else:
                agent["details"] = "Domain expert with comprehensive knowledge and experience"

        logger.info(f"Loaded {len(prebuilt_agents)} prebuilt agents")
        return prebuilt_agents

    except Exception as e:
        logger.error(f"Error loading prebuilt agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to load prebuilt agents")


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get an agent by ID."""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentRead(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            config=agent.config,
            generation_phase=agent.generation_phase,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AgentRead)
async def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    """Create a new agent with auto-generated basic Dana code."""
    try:
        # Create the agent in database first
        db_agent = Agent(name=agent.name, description=agent.description, config=agent.config)

        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        # # Auto-generate basic Dana code and agent folder
        # try:
        #     folder_path = await _auto_generate_basic_agent_code(
        #         agent_id=db_agent.id,
        #         agent_name=agent.name,
        #         agent_description=agent.description,
        #         agent_config=agent.config or {},
        #         agent_manager=agent_manager,
        #     )

        #     # Update agent with folder path
        #     if folder_path:
        #         # Update config with folder_path
        #         updated_config = db_agent.config.copy() if db_agent.config else {}
        #         updated_config["folder_path"] = folder_path

        #         # Update database record
        #         db_agent.config = updated_config
        #         db_agent.generation_phase = "code_generated"

        #         # Force update by marking as dirty
        #         flag_modified(db_agent, "config")

        #         db.commit()
        #         db.refresh(db_agent)
        #         logger.info(f"Updated agent {db_agent.id} with folder_path: {folder_path}")
        #         logger.info(f"Agent config after update: {db_agent.config}")

        # except Exception as code_gen_error:
        #     Don't fail the agent creation if code generation fails
        #     logger.error(f"Failed to auto-generate code for agent {db_agent.id}: {code_gen_error}")
        #     logger.error(f"Full traceback: {traceback.format_exc()}")

        return AgentRead(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            config=db_agent.config,
            folder_path=db_agent.config.get("folder_path") if db_agent.config else None,
            generation_phase=db_agent.generation_phase,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(agent_id: int, agent: AgentUpdate, db: Session = Depends(get_db)):
    """Update an agent."""
    try:
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.name:
            db_agent.name = agent.name
        if agent.config:
            if db_agent.config:
                db_agent.config.update(agent.config)
            else:
                db_agent.config = agent.config

        flag_modified(db_agent, "config")
        db.commit()
        db.refresh(db_agent)

        return AgentRead(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            config=db_agent.config,
            generation_phase=db_agent.generation_phase,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int, db: Session = Depends(get_db), deletion_service: AgentDeletionService = Depends(get_agent_deletion_service)
):
    """Delete an agent and all associated resources."""
    try:
        result = await deletion_service.delete_agent_comprehensive(agent_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/soft")
async def soft_delete_agent(
    agent_id: int, db: Session = Depends(get_db), deletion_service: AgentDeletionService = Depends(get_agent_deletion_service)
):
    """Soft delete an agent by marking it as deleted without removing files."""
    try:
        result = await deletion_service.soft_delete_agent(agent_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error soft deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-orphaned-files")
async def cleanup_orphaned_files(
    db: Session = Depends(get_db), deletion_service: AgentDeletionService = Depends(get_agent_deletion_service)
):
    """Clean up orphaned files that don't have corresponding database records."""
    try:
        result = await deletion_service.cleanup_orphaned_files(db)
        return {"message": "Cleanup completed successfully", "cleanup_stats": result}
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional endpoints expected by UI


@router.post("/validate", response_model=CodeValidationResponse)
async def validate_agent_code(request: CodeValidationRequest):
    """Validate agent code."""
    try:
        logger.info("Received code validation request")

        # Placeholder implementation
        return CodeValidationResponse(success=True, is_valid=True, errors=[], warnings=[], suggestions=[])

    except Exception as e:
        logger.error(f"Error in validate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fix", response_model=CodeFixResponse)
async def fix_agent_code(request: CodeFixRequest):
    """Fix agent code."""
    try:
        logger.info("Received code fix request")

        # Placeholder implementation
        return CodeFixResponse(success=True, fixed_code=request.code, applied_fixes=[], remaining_errors=[])

    except Exception as e:
        logger.error(f"Error in fix endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-prebuilt", response_model=AgentRead)
async def create_agent_from_prebuilt(
    prebuilt_key: str = Body(..., embed=True),
    config: dict = Body(..., embed=True),
    db: Session = Depends(get_db),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    """Create a new agent by cloning a prebuilt agent's files and domain_knowledge.json."""
    try:
        # Load prebuilt agents list
        assets_path = API_FOLDER / "server" / "assets" / "prebuilt_agents.json"
        with open(assets_path, encoding="utf-8") as f:
            prebuilt_agents = json.load(f)
        prebuilt_agent = next((a for a in prebuilt_agents if a["key"] == prebuilt_key), None)
        if not prebuilt_agent:
            raise HTTPException(status_code=404, detail="Prebuilt agent not found")
        # Add status field from provided config to prebuilt config
        prebuilt_config = prebuilt_agent.get("config", {})
        merged_config = prebuilt_config.copy()
        if "status" in config:
            merged_config["status"] = config["status"]

        # Create new agent in DB
        db_agent = Agent(
            name=prebuilt_agent["name"],
            description=prebuilt_agent.get("description", ""),
            config=merged_config,
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        # Copy files from prebuilt assets folder
        prebuilt_folder = API_FOLDER / "server" / "assets" / prebuilt_agent["key"]
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)
        safe_name = db_agent.name.lower().replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        folder_name = f"agent_{db_agent.id}_{safe_name}"
        agent_folder = agents_dir / folder_name

        if prebuilt_folder.exists():
            shutil.copytree(prebuilt_folder, agent_folder)
            logger.info(f"Copied prebuilt agent files from {prebuilt_folder} to {agent_folder}")
        else:
            # Create basic agent structure if prebuilt folder doesn't exist
            agent_folder.mkdir(exist_ok=True)
            docs_folder = agent_folder / "docs"
            docs_folder.mkdir(exist_ok=True)
            knows_folder = agent_folder / "knows"
            knows_folder.mkdir(exist_ok=True)
            logger.info(f"Created basic agent structure at {agent_folder}")

        # Ensure domain_knowledge.json is in the correct location and has UUIDs
        domain_knowledge_path = agent_folder / "domain_knowledge.json"
        if not domain_knowledge_path.exists():
            # Try to generate domain_knowledge.json from knowledge files
            try:
                from dana.common.utils.domain_knowledge_generator import (
                    DomainKnowledgeGenerator,
                )

                generator = DomainKnowledgeGenerator()
                knows_folder = agent_folder / "knows"
                domain = prebuilt_agent.get("config", {}).get("domain", "General")

                if generator.save_domain_knowledge(str(knows_folder), domain, str(domain_knowledge_path)):
                    logger.info(f"Generated domain_knowledge.json for agent {db_agent.id}")
                else:
                    logger.warning(f"Failed to generate domain_knowledge.json for agent {db_agent.id}")
            except Exception as e:
                logger.error(f"Error generating domain_knowledge.json: {e}")

        # Ensure domain_knowledge.json has UUIDs (for both existing and newly generated files)
        if domain_knowledge_path.exists():
            _ensure_domain_knowledge_has_uuids(str(domain_knowledge_path))

        # Update knowledge status for prebuilt agents - mark all topics as success
        try:
            knows_folder = agent_folder / "knows"
            status_path = knows_folder / "knowledge_status.json"

            if status_path.exists():
                from datetime import datetime

                from dana.api.services.knowledge_status_manager import (
                    KnowledgeStatusManager,
                )

                status_manager = KnowledgeStatusManager(str(status_path), agent_id=str(db_agent.id))
                data = status_manager.load()

                # Mark all topics as successfully generated since they're prebuilt
                updated = False
                now_str = datetime.now(UTC).isoformat() + "Z"

                for entry in data.get("topics", []):
                    if entry.get("status") in (
                        "pending",
                        "failed",
                        None,
                        "in_progress",
                    ):
                        # Only mark as success if the knowledge file actually exists
                        knowledge_file = knows_folder / entry.get("file", "")
                        if knowledge_file.exists():
                            entry["status"] = "success"
                            entry["last_generated"] = now_str
                            entry["error"] = None
                            updated = True

                if updated:
                    status_manager.save(data)
                    logger.info(f"Updated knowledge status for prebuilt agent {db_agent.id} - marked all topics as success")

        except Exception as e:
            logger.error(f"Error updating knowledge status for prebuilt agent: {e}")

        # Update config with folder_path and status
        updated_config = db_agent.config.copy() if db_agent.config else {}
        updated_config["folder_path"] = str(agent_folder)
        db_agent.config = updated_config
        db_agent.generation_phase = "code_generated"
        flag_modified(db_agent, "config")
        db.commit()
        db.refresh(db_agent)
        return AgentRead(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            config=db_agent.config,
            generation_phase=db_agent.generation_phase,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
        )
    except Exception as e:
        logger.error(f"Error creating agent from prebuilt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/documents", response_model=DocumentRead)
async def upload_agent_document(
    agent_id: int,
    file: UploadFile = File(...),
    topic_id: int | None = Form(None),
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document to a specific agent's folder."""
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get folder_path from agent config
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            # Generate folder path and save it to config
            folder_path = os.path.join("agents", f"agent_{agent_id}")
            os.makedirs(folder_path, exist_ok=True)

            # Update config with folder_path
            updated_config = agent.config.copy() if agent.config else {}
            updated_config["folder_path"] = folder_path
            agent.config = updated_config

            # Force update by marking as dirty
            flag_modified(agent, "config")

            db.commit()
            db.refresh(agent)

        # Use the agent's docs folder as the upload directory
        docs_folder = os.path.join(folder_path, "docs")
        os.makedirs(docs_folder, exist_ok=True)

        document = await document_service.upload_document(
            file=file.file,
            filename=file.filename,
            topic_id=topic_id,
            agent_id=agent_id,
            db_session=db,
            upload_directory=docs_folder,
        )

        # Clear cache to force RAG rebuild with new document
        clear_agent_cache(folder_path)

        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/documents/associate")
async def associate_documents_with_agent(
    agent_id: int,
    request_body: AssociateDocumentsRequest,
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Associate existing documents with an agent."""
    try:
        # Extract document_ids from request body
        document_ids = request_body.document_ids
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with id {agent_id} not found")

        # Get folder_path from agent config
        folder_path = agent.config.get("folder_path") if agent.config else None

        if not folder_path:
            # Generate folder path and save it to config
            folder_path = os.path.join("agents", f"agent_{agent_id}")
            os.makedirs(folder_path, exist_ok=True)

            # Update config with folder_path
            updated_config = agent.config.copy() if agent.config else {}
            updated_config["folder_path"] = folder_path
            agent.config = updated_config

            # Force update by marking as dirty
            flag_modified(agent, "config")

            db.commit()
            db.refresh(agent)

        # Get current associated documents
        current_associated_documents = set(agent.config.get("associated_documents", []))
        new_document_ids = set(document_ids)

        # Calculate documents to add and remove
        documents_to_add = new_document_ids - current_associated_documents
        documents_to_remove = current_associated_documents - new_document_ids

        if not documents_to_add and not documents_to_remove:
            return {
                "success": True,
                "message": (f"No changes needed - documents {document_ids} are already correctly associated with agent {agent_id}"),
                "updated_count": 0,
            }

        # Update the agent's associated documents to match the new set
        agent.config["associated_documents"] = list(new_document_ids)

        # Force update by marking as dirty
        flag_modified(agent, "config")

        # Handle document additions
        new_file_paths = []
        if documents_to_add:
            new_file_paths = await document_service.associate_documents_with_agent(agent_id, folder_path, list(documents_to_add), db)
            print(f"new_file_paths: {new_file_paths}")

        # Handle document removals
        if documents_to_remove:
            for doc_id in documents_to_remove:
                # Remove the file from agent's folder
                document = db.query(Document).filter(Document.id == doc_id).first()
                if document and folder_path:
                    document_fp = document_service.get_agent_associated_fp(folder_path, str(document.original_filename))
                    if os.path.exists(document_fp):
                        os.remove(document_fp)

        # Clear cache to force RAG rebuild
        if documents_to_add or documents_to_remove:
            db.commit()
            clear_agent_cache(folder_path)

        total_changes = len(documents_to_add) + len(documents_to_remove)

        return {
            "success": True,
            "message": (
                f"Successfully updated document associations for agent {agent_id}. "
                f"Added: {len(documents_to_add)}, Removed: {len(documents_to_remove)}"
            ),
            "updated_count": total_changes,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating documents with agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/documents/{document_id}/disassociate")
async def disassociate_document_from_agent(
    agent_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Disassociate a document from an agent without deleting the document."""
    try:
        # Get the agent to verify it exists
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with id {agent_id} not found")

        # Get the document to verify it exists and is associated with this agent
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Associate documents by placing them inside agent config for now
        current_associated_documents = agent.config.get("associated_documents", [])
        agent.config["associated_documents"] = list(set(current_associated_documents) - {document_id})

        # Force update by marking as dirty
        flag_modified(agent, "config")

        # Remove the association by setting agent_id to None
        agent_folder_path = agent.config.get("folder_path") if agent.config else None
        if agent_folder_path:
            document_fp = document_service.get_agent_associated_fp(agent_folder_path, document.original_filename)
            if os.path.exists(document_fp):
                os.remove(document_fp)
            # Clear cache to force RAG rebuild without the disassociated document
            clear_agent_cache(agent_folder_path)

        db.commit()

        return {
            "success": True,
            "message": f"Successfully disassociated document {document_id} from agent {agent_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disassociating document {document_id} from agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/files")
async def list_agent_files(agent_id: int, db: Session = Depends(get_db)):
    """List all files in the agent's folder structure."""
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            return {"files": [], "message": "Agent folder not found"}

        # List all files in the agent folder
        agent_folder = Path(folder_path)
        if not agent_folder.exists():
            return {"files": [], "message": "Agent folder does not exist"}

        files = []
        for file_path in agent_folder.rglob("*"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(agent_folder))
                file_info = {
                    "name": file_path.name,
                    "path": relative_path,
                    "full_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                    "type": "dana" if file_path.suffix == ".na" else "document" if relative_path.startswith("docs/") else "other",
                }
                files.append(file_info)

        # Sort files with custom ordering for .na files
        def get_file_sort_priority(file_info):
            filename = file_info["name"].lower()

            # Define the priority order for .na files
            if filename == "main.na":
                return (0, filename)
            elif filename == "workflows.na":
                return (1, filename)
            elif filename == "knowledge.na":
                return (2, filename)
            elif filename == "methods.na":
                return (3, filename)
            elif filename == "common.na":
                return (4, filename)
            elif filename == "tools.na":
                return (5, filename)
            elif filename.endswith(".na"):
                # Other .na files come after the main ones, sorted alphabetically
                return (6, filename)
            else:
                # Non-.na files come last, sorted alphabetically
                return (7, filename)

        files.sort(key=get_file_sort_priority)
        return {"files": files}

    except Exception as e:
        logger.error(f"Error listing agent files for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/files/{file_path:path}")
async def get_agent_file_content(agent_id: int, file_path: str, db: Session = Depends(get_db)):
    """Get the content of a specific file in the agent's folder."""
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            raise HTTPException(status_code=404, detail="Agent folder not found")

        # Construct full file path and validate it's within agent folder
        agent_folder = Path(folder_path)
        full_file_path = agent_folder / file_path

        # Security check: ensure file is within agent folder
        try:
            full_file_path.resolve().relative_to(agent_folder.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied: file outside agent folder")

        if not full_file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not full_file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read file content
        try:
            content = full_file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # For binary files, return base64 encoded content
            content = base64.b64encode(full_file_path.read_bytes()).decode("utf-8")
            return {
                "content": content,
                "encoding": "base64",
                "file_path": file_path,
                "file_name": full_file_path.name,
                "file_size": full_file_path.stat().st_size,
            }

        return {
            "content": content,
            "encoding": "utf-8",
            "file_path": file_path,
            "file_name": full_file_path.name,
            "file_size": full_file_path.stat().st_size,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading agent file {file_path} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}/files/{file_path:path}")
async def update_agent_file_content(agent_id: int, file_path: str, request: dict, db: Session = Depends(get_db)):
    """Update the content of a specific file in the agent's folder."""
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            raise HTTPException(status_code=404, detail="Agent folder not found")

        # Construct full file path and validate it's within agent folder
        agent_folder = Path(folder_path)
        full_file_path = agent_folder / file_path

        # Security check: ensure file is within agent folder
        try:
            full_file_path.resolve().relative_to(agent_folder.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied: file outside agent folder")

        content = request.get("content", "")
        encoding = request.get("encoding", "utf-8")

        # Create parent directories if they don't exist
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file content
        if encoding == "base64":
            full_file_path.write_bytes(base64.b64decode(content))
        else:
            full_file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "message": f"File {file_path} updated successfully",
            "file_path": file_path,
            "file_size": full_file_path.stat().st_size,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent file {file_path} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-file/{file_path:path}")
async def open_file(file_path: str):
    """Open file endpoint."""
    try:
        logger.info(f"Received open file request for: {file_path}")

        # Placeholder implementation
        return {"message": f"Open file endpoint for {file_path} - not yet implemented"}

    except Exception as e:
        logger.error(f"Error in open file endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/chat-history")
async def get_agent_chat_history(
    agent_id: int,
    type: str = Query(
        None,
        description="Filter by message type: 'chat_with_dana_build', 'smart_chat', or 'all' for both types",
    ),
    db: Session = Depends(get_db),
):
    """
    Get chat history for an agent.

    Args:
        agent_id: Agent ID
        type: Message type filter ('chat_with_dana_build', 'smart_chat', 'all', or None for default 'smart_chat')

    Returns:
        List of chat messages with sender and text
    """
    query = db.query(AgentChatHistory).filter(AgentChatHistory.agent_id == agent_id)

    # Filter by type: default to 'smart_chat' if None, or filter by specific type unless 'all'
    filter_type = type or "smart_chat"
    if filter_type != "all":
        query = query.filter(AgentChatHistory.type == filter_type)

    history = query.order_by(AgentChatHistory.created_at).all()

    return [
        {
            "sender": h.sender,
            "text": h.text,
            "type": h.type,
            "created_at": h.created_at.isoformat(),
        }
        for h in history
    ]


def run_generation(agent_id: int):
    # This function runs in a background thread
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_thread = SessionLocal()
    try:
        agent = db_thread.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            print(f"[generate-knowledge] Agent {agent_id} not found")
            return
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")
            os.makedirs(folder_path, exist_ok=True)
            print(f"[generate-knowledge] Created default folder_path: {folder_path}")
        knows_folder = os.path.join(folder_path, "knows")
        os.makedirs(knows_folder, exist_ok=True)
        print(f"[generate-knowledge] Using knows folder: {knows_folder}")

        role = agent.config.get("role") if agent.config and agent.config.get("role") else (agent.description or "Domain Expert")
        topic = agent.config.get("topic") if agent.config and agent.config.get("topic") else (agent.name or "General Topic")
        print(f"[generate-knowledge] Using topic: {topic}, role: {role}")

        from dana.api.services.domain_knowledge_service import DomainKnowledgeService

        domain_service_thread = DomainKnowledgeService()
        tree = asyncio.run(domain_service_thread.get_agent_domain_knowledge(agent_id, db_thread))
        if not tree:
            print(f"[generate-knowledge] Domain knowledge tree not found for agent {agent_id}")
            return
        print(f"[generate-knowledge] Loaded domain knowledge tree for agent {agent_id}")

        def collect_leaf_paths(node, path_so_far, is_root=False):
            # Skip adding root topic to path to match original knowledge status format
            if is_root:
                path = path_so_far
            else:
                path = path_so_far + [node.topic]

            if not getattr(node, "children", []):
                return [(path, node)]
            leaves = []
            for child in getattr(node, "children", []):
                leaves.extend(collect_leaf_paths(child, path, is_root=False))
            return leaves

        leaf_paths = collect_leaf_paths(tree.root, [], is_root=True)
        print(f"[generate-knowledge] Collected {len(leaf_paths)} leaf topics from tree")

        # 1. Build or update knowledge_status.json
        status_path = os.path.join(knows_folder, "knowledge_status.json")
        status_manager = KnowledgeStatusManager(status_path, agent_id=str(agent_id))
        now_str = datetime.now(UTC).isoformat() + "Z"
        # Add/update all leaves
        for path, _ in leaf_paths:
            area_name = " - ".join(path)
            safe_area = area_name.replace("/", "_").replace(" ", "_").replace("-", "_")
            file_name = f"{safe_area}.json"
            status_manager.add_or_update_topic(
                path=area_name,
                file=file_name,
                last_topic_update=now_str,
                status="preserve_existing",  # Preserve existing status, set to pending if null
            )
        # Remove topics that are no longer in the tree
        all_paths = set([" - ".join(path) for path, _ in leaf_paths])
        for entry in status_manager.load()["topics"]:
            if entry["path"] not in all_paths:
                status_manager.remove_topic(entry["path"])

        # 2. Only queue topics with status 'pending', 'failed', or null
        pending = status_manager.get_pending_failed_or_null()
        print(f"[generate-knowledge] {len(pending)} topics to generate (pending, failed, or null)")

        # 3. Use KnowledgeGenerationManager to run the queue
        manager = KnowledgeGenerationManager(status_manager, max_concurrent=4, ws_manager=ws_manager)

        async def main():
            for entry in pending:
                await manager.add_topic(entry)
            await manager.run()
            print("[generate-knowledge] All queued topics processed and saved.")

        asyncio.run(main())
    finally:
        db_thread.close()


@router.post("/{agent_id}/generate-knowledge")
async def generate_agent_knowledge(
    agent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
):
    """
    Start asynchronous background generation of domain knowledge for all leaf topics in the agent's domain knowledge tree using ManagerAgent.
    Each leaf's knowledge is saved as a separate JSON file in the agent's knows folder.
    The area name for LLM context is the full path (parent, grandparent, ...).
    Runs up to 4 leaf generations in parallel.
    """

    # Start the background job
    background_tasks.add_task(run_generation, agent_id)
    return {
        "success": True,
        "message": "Knowledge generation started in background. Check logs for progress.",
        "agent_id": agent_id,
    }


@router.get("/{agent_id}/knowledge-status")
async def get_agent_knowledge_status(agent_id: int, db: Session = Depends(get_db)):
    """
    Get the knowledge generation status for all topics in the agent's domain knowledge tree.
    Returns the knowledge_status.json content with status information for each topic.
    """
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            # Return empty status if no folder exists yet
            return {"topics": []}

        # Check if knowledge status file exists
        knows_folder = os.path.join(folder_path, "knows")
        status_path = os.path.join(knows_folder, "knowledge_status.json")

        if not os.path.exists(status_path):
            # Return empty status if no knowledge status file exists yet
            return {"topics": []}

        # Load and return the knowledge status
        status_manager = KnowledgeStatusManager(status_path, agent_id=str(agent_id))
        return status_manager.load()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge status for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/test")
async def test_agent_by_id(agent_id: str, request: dict, db: Session = Depends(get_db)):
    """
    Test an agent by ID with a message.

    This endpoint gets the agent details from the database by ID (for integer IDs)
    or handles prebuilt agents (for string IDs), then runs the Dana file execution logic.

    Args:
        agent_id: The ID of the agent to test (integer for DB agents, string for prebuilt)
        request: Dict containing 'message' and optional context
        db: Database session

    Returns:
        Agent response or error
    """
    try:
        # Get message from request
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        agent_name = None
        agent_description = None
        folder_path = None

        # Handle both integer and string agent IDs
        if agent_id.isdigit():
            # Handle regular agent (integer ID)
            agent_id_int = int(agent_id)
            agent = db.query(Agent).filter(Agent.id == agent_id_int).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            # Extract agent details
            agent_name = agent.name
            agent_description = agent.description or "A Dana agent"
            folder_path = agent.config.get("folder_path") if agent.config else None
        else:
            # Handle prebuilt agent (string ID)
            logger.info(f"Testing prebuilt agent: {agent_id}")

            # Load prebuilt agents list
            assets_path = API_FOLDER / "server" / "assets" / "prebuilt_agents.json"

            try:
                with open(assets_path, encoding="utf-8") as f:
                    prebuilt_agents = json.load(f)

                prebuilt_agent = next((a for a in prebuilt_agents if a["key"] == agent_id), None)

                if not prebuilt_agent:
                    raise HTTPException(status_code=404, detail="Prebuilt agent not found")

                agent_name = prebuilt_agent["name"]
                agent_description = prebuilt_agent.get("description", "A prebuilt Dana agent")

                # Check if prebuilt agent folder exists in assets
                prebuilt_folder = API_FOLDER / "server" / "assets" / agent_id

                if not prebuilt_folder.exists():
                    raise HTTPException(status_code=404, detail=f"Prebuilt agent folder '{agent_id}' not found")

                # Create agents directory if it doesn't exist
                agents_dir = Path("agents")
                agents_dir.mkdir(exist_ok=True)

                # Target folder in agents directory
                target_folder = agents_dir / agent_id

                # Copy prebuilt folder to agents directory if not already there
                if not target_folder.exists():
                    shutil.copytree(prebuilt_folder, target_folder)
                    logger.info(f"Copied prebuilt agent '{agent_id}' to {target_folder}")

                folder_path = str(target_folder)

            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error loading prebuilt agents: {e}")
                raise HTTPException(status_code=500, detail="Failed to load prebuilt agents")

        logger.info(f"Testing agent {agent_id} ({agent_name}) with message: '{message}'")

        # Import the test logic from agent_test module
        from dana.api.routers.v1.agent_test import AgentTestRequest, test_agent
        from dana.__init__.init_modules import (
            initialize_module_system,
            reset_module_system,
        )

        initialize_module_system()
        reset_module_system()

        # Create test request using agent details
        test_request = AgentTestRequest(
            agent_code="",  # Will use folder_path instead
            message=message,
            agent_name=agent_name,
            agent_description=agent_description,
            context=request.get("context", {"user_id": "test_user"}),
            folder_path=folder_path,
            websocket_id=request.get("websocket_id"),
        )

        # Call the existing test_agent function
        result = await test_agent(test_request)

        # Save chat history to database if the test was successful
        if result.success and result.agent_response:
            try:
                # Convert agent_id to int if it's a numeric string (for database agents)
                actual_agent_id = None
                if agent_id.isdigit():
                    actual_agent_id = int(agent_id)
                else:
                    # For prebuilt agents, we don't save to chat history since they don't have DB records
                    logger.info(f"Skipping chat history for prebuilt agent: {agent_id}")

                if actual_agent_id:
                    from dana.api.core.models import AgentChatHistory

                    # Save user message
                    user_chat = AgentChatHistory(agent_id=actual_agent_id, sender="user", text=message, type="test_chat")
                    db.add(user_chat)

                    # Save agent response
                    agent_chat = AgentChatHistory(agent_id=actual_agent_id, sender="agent", text=result.agent_response, type="test_chat")
                    db.add(agent_chat)

                    db.commit()
                    logger.info(f"Saved test chat history for agent {actual_agent_id}")

            except Exception as chat_error:
                logger.error(f"Failed to save chat history: {chat_error}")
                # Don't fail the request if chat history saving fails
                db.rollback()

        return {
            "success": result.success,
            "agent_response": result.agent_response,
            "error": result.error,
            "agent_id": agent_id,
            "agent_name": agent_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/domain-knowledge/versions")
async def get_domain_knowledge_versions(
    agent_id: int,
    db: Session = Depends(get_db),
    version_service: DomainKnowledgeVersionService = Depends(get_domain_knowledge_version_service),
):
    """Get all domain knowledge versions for an agent."""
    try:
        # Verify agent exists
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        versions = version_service.get_versions(agent_id)
        return {"versions": versions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain knowledge versions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/domain-knowledge/revert")
async def revert_domain_knowledge(
    agent_id: int,
    request: dict,
    db: Session = Depends(get_db),
    version_service: DomainKnowledgeVersionService = Depends(get_domain_knowledge_version_service),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
):
    """Revert domain knowledge to a specific version."""
    try:
        # Verify agent exists
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        target_version = request.get("version")
        if not target_version:
            raise HTTPException(status_code=400, detail="Version number is required")

        # Revert to the specified version
        reverted_tree = version_service.revert_to_version(agent_id, target_version)
        if not reverted_tree:
            raise HTTPException(status_code=404, detail="Version not found or revert failed")

        # Save the reverted tree as current
        save_success = await domain_service.save_agent_domain_knowledge(agent_id, reverted_tree, db, agent)

        if not save_success:
            raise HTTPException(status_code=500, detail="Failed to save reverted tree")

        # Clear cache to force RAG rebuild
        folder_path = agent.config.get("folder_path") if agent.config else None
        if folder_path:
            clear_agent_cache(folder_path)

        return {
            "success": True,
            "message": f"Successfully reverted to version {target_version}",
            "current_version": reverted_tree.version,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverting domain knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/avatar")
async def get_agent_avatar(agent_id: int):
    """Get agent avatar by ID."""
    try:
        # Verify agent exists
        from dana.api.core.database import get_db

        # Get database session
        db = next(get_db())
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get avatar using avatar service
        avatar_service = AvatarService()
        avatar_file_path = avatar_service.get_avatar_file_path(agent_id)

        if not avatar_file_path or not avatar_file_path.exists():
            raise HTTPException(status_code=404, detail="Avatar not found")

        # Return the avatar file
        from fastapi.responses import FileResponse

        return FileResponse(path=str(avatar_file_path), media_type="image/svg+xml", filename=f"agent-avatar-{agent_id}.svg")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting avatar for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=AgentSuggestionResponse)
async def suggest_agents(request: AgentSuggestionRequest):
    """
    Suggest the 2 most relevant prebuilt agents based on user message using LLM.

    Args:
        request: Contains the user message describing what they want to build

    Returns:
        AgentSuggestionResponse with 2 suggested agents and matching percentages
    """
    try:
        user_message = request.user_message.strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="User message cannot be empty")

        logger.info(f"Suggesting agents for user message: {user_message[:100]}...")

        # Load prebuilt agents
        prebuilt_agents = _load_prebuilt_agents()
        if not prebuilt_agents:
            return AgentSuggestionResponse(success=False, suggestions=[], message="No prebuilt agents available")

        # Use LLM to suggest agents
        llm = LLMResource()
        suggestions = _suggest_agents_with_llm(llm, user_message, prebuilt_agents)

        if not suggestions:
            # Fallback: return first 2 agents if LLM fails
            fallback_suggestions = []
            for agent in prebuilt_agents[:2]:
                agent_copy = agent.copy()
                agent_copy["matching_percentage"] = 50  # Default percentage
                agent_copy["explanation"] = "Fallback suggestion - please review manually"
                fallback_suggestions.append(agent_copy)

            return AgentSuggestionResponse(
                success=True, suggestions=fallback_suggestions, message="Unable to analyze with AI. Here are some general suggestions."
            )

        return AgentSuggestionResponse(
            success=True, suggestions=suggestions, message=f"Found {len(suggestions)} relevant agents based on your requirements."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-from-suggestion", response_model=AgentRead)
async def build_agent_from_suggestion(
    request: BuildAgentFromSuggestionRequest,
    db: Session = Depends(get_db),
):
    """
    Build a new agent by copying only .na files from a suggested prebuilt agent.
    Creates a new agent with user's custom name and description, but uses prebuilt agent's code.

    Args:
        request: Contains prebuilt_key, user_input (description), and optional agent_name

    Returns:
        AgentRead: The newly created agent
    """
    try:
        # Load and validate prebuilt agent
        prebuilt_agents = _load_prebuilt_agents()
        prebuilt_agent = next((a for a in prebuilt_agents if a["key"] == request.prebuilt_key), None)
        if not prebuilt_agent:
            raise HTTPException(status_code=404, detail=f"Prebuilt agent not found: {request.prebuilt_key}")

        logger.info(f"Building agent from suggestion: {request.prebuilt_key}")

        # Create new agent in database with user's input
        db_agent = Agent(
            name=request.agent_name,
            description=request.user_input,  # Use user's input as description
            config=prebuilt_agent.get("config", {}),  # Use prebuilt config as base
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        # Create agent folder structure
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)

        safe_name = db_agent.name.lower().replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        folder_name = f"agent_{db_agent.id}_{safe_name}"
        agent_folder = agents_dir / folder_name

        # Create basic directory structure
        agent_folder.mkdir(exist_ok=True)
        docs_folder = agent_folder / "docs"
        docs_folder.mkdir(exist_ok=True)
        knows_folder = agent_folder / "knows"
        knows_folder.mkdir(exist_ok=True)

        # Copy only .na files from prebuilt agent
        if not _copy_na_files_from_prebuilt(request.prebuilt_key, str(agent_folder)):
            logger.warning(f"Failed to copy .na files from prebuilt '{request.prebuilt_key}', continuing anyway")

        # Update agent config with folder path
        updated_config = db_agent.config.copy() if db_agent.config else {}
        updated_config["folder_path"] = str(agent_folder)

        template_config = {k: v for k, v in db_agent.config.items() if k in ["domain", "specialties", "skills", "task", "role"]}
        prompt = f"""
User request: {request.user_input}
template config:
```json
{template_config}
```

Adjust the agent config to match the user request.
Output format :
```json
{{
    "domain": "...",
    "specialties": ["..."],
    "skills": ["..."],
    "task": "...",
    "role": "...",
}}
```
"""

        # Adjust agent config
        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that adjusts agent config based on user request."},
                    {"role": "user", "content": prompt},
                ]
            }
        )
        response = await LLMResource().query(llm_request)
        result = Misc.get_response_content(response)
        new_config = Misc.text_to_dict(result)
        updated_config.update(new_config)

        # Ensure domain_knowledge.json is in the correct location and has UUIDs
        domain_knowledge_path = agent_folder / "domain_knowledge.json"
        if not domain_knowledge_path.exists():
            # Try to generate domain_knowledge.json from knowledge files
            try:
                from dana.common.utils.domain_knowledge_generator import (
                    DomainKnowledgeGenerator,
                )

                generator = DomainKnowledgeGenerator()
                domain = updated_config.get("domain", "General")

                if generator.save_domain_knowledge(str(knows_folder), domain, str(domain_knowledge_path)):
                    logger.info(f"Generated domain_knowledge.json for agent {db_agent.id} built from suggestion")
                else:
                    logger.warning(f"Failed to generate domain_knowledge.json for agent {db_agent.id} built from suggestion")
            except Exception as e:
                logger.error(f"Error generating domain_knowledge.json for agent {db_agent.id} built from suggestion: {e}")

        db_agent.config = updated_config
        db_agent.generation_phase = "ready_for_training"  # Different phase since no knowledge files
        flag_modified(db_agent, "config")
        db.commit()
        db.refresh(db_agent)

        logger.info(f"Successfully built agent {db_agent.id} from suggestion {request.prebuilt_key}")

        return AgentRead(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            config=db_agent.config,
            generation_phase=db_agent.generation_phase,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building agent from suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prebuilt_key}/workflow-info", response_model=WorkflowInfo)
async def get_prebuilt_agent_workflow_info(prebuilt_key: str):
    """
    Get workflow information from a prebuilt agent's workflows.na file.

    Args:
        prebuilt_key: The key of the prebuilt agent

    Returns:
        WorkflowInfo: Parsed workflow definitions and methods
    """
    try:
        # Validate prebuilt agent exists
        prebuilt_agents = _load_prebuilt_agents()
        prebuilt_agent = next((a for a in prebuilt_agents if a["key"] == prebuilt_key), None)
        if not prebuilt_agent:
            raise HTTPException(status_code=404, detail=f"Prebuilt agent not found: {prebuilt_key}")

        # Try to read workflows.na file
        workflows_path = API_FOLDER / "server" / "assets" / prebuilt_key / "workflows.na"

        if not workflows_path.exists():
            # Return empty workflow info if file doesn't exist
            return WorkflowInfo(workflows=[], methods=[])

        # Read and parse workflow content
        with open(workflows_path, "r", encoding="utf-8") as f:  # noqa
            content = f.read()

        parsed_data = _parse_workflow_content(content)

        return WorkflowInfo(workflows=parsed_data["workflows"], methods=parsed_data["methods"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow info for {prebuilt_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/export-tar", response_model=TarExportResponse)
async def export_agent_tar(agent_id: int, request: TarExportRequest, db: Session = Depends(get_db)):
    """
    Create a tar archive of the agent for sharing.

    Args:
        agent_id: The ID of the agent to export
        request: Export configuration including whether to include dependencies

    Returns:
        TarExportResponse: Success status and path to the tar file
    """
    try:
        # Get the agent from database
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            logger.error(f"Agent {agent_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        logger.info(f"Found agent {agent_id}: {agent.name}")
        logger.info(f"Agent config: {agent.config}")

        # Get agent folder path
        agent_folder = None
        if agent.config and "folder_path" in agent.config:
            agent_folder = agent.config["folder_path"]
            logger.info(f"Using config folder_path: {agent_folder}")
        else:
            # Try to find the agent folder in the agents directory
            agents_dir = Path("agents")
            possible_folders = list(agents_dir.glob(f"agent_{agent_id}_*"))
            logger.info(f"Searching for agent_{agent_id}_* in {agents_dir}")
            logger.info(f"Found possible folders: {possible_folders}")
            if possible_folders:
                agent_folder = str(possible_folders[0])
                logger.info(f"Using found folder: {agent_folder}")

        if not agent_folder:
            logger.error(f"No agent folder found for agent {agent_id}")
            raise HTTPException(status_code=404, detail=f"Agent folder not found for agent {agent_id}")

        if not os.path.exists(agent_folder):
            logger.error(f"Agent folder does not exist: {agent_folder}")
            raise HTTPException(status_code=404, detail=f"Agent folder does not exist: {agent_folder}")

        logger.info(f"Using agent folder: {agent_folder}")

        # Create the tar archive
        tar_path = _create_agent_tar(agent_id, agent_folder, request.include_dependencies)

        return TarExportResponse(success=True, tar_path=tar_path, message=f"Successfully created tar archive for agent {agent_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting agent {agent_id} to tar: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export agent: {str(e)}")


@router.get("/{agent_id}/download-tar")
async def download_agent_tar(agent_id: int, path: str = Query(...), db: Session = Depends(get_db)):
    """
    Download a tar archive of the agent.

    Args:
        agent_id: The ID of the agent
        path: The path to the tar file to download

    Returns:
        FileResponse: The tar file for download
    """
    try:
        # Validate that the path exists and is a tar file
        if not os.path.exists(path) or not path.endswith(".tar.gz"):
            raise HTTPException(status_code=404, detail="Tar file not found")

        # Get the agent name for the filename
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        agent_name = agent.name if agent else f"agent_{agent_id}"

        # Create a safe filename
        safe_name = "".join(c for c in agent_name if c.isalnum() or c in "._-")
        filename = f"{safe_name}_{agent_id}.tar.gz"

        return FileResponse(path=path, filename=filename, media_type="application/gzip")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading tar for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download tar file: {str(e)}")


@router.post("/import-tar", response_model=TarImportResponse)
async def import_agent_tar(
    file: UploadFile = File(...),
    agent_name: str = Form(...),
    agent_description: str = Form("Imported agent"),
    db: Session = Depends(get_db),
):
    """
    Import an agent from a tar archive.

    Args:
        file: The tar file to import
        agent_name: Name for the imported agent
        agent_description: Description for the imported agent

    Returns:
        TarImportResponse: Success status and new agent ID
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(".tar.gz"):
            raise HTTPException(status_code=400, detail="Only .tar.gz files are supported")

        # Create a new agent in the database
        db_agent = Agent(name=agent_name, description=agent_description, config={})
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        # Create agent folder
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)

        safe_name = agent_name.lower().replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        folder_name = f"agent_{db_agent.id}_{safe_name}"
        agent_folder = agents_dir / folder_name
        agent_folder.mkdir(exist_ok=True)

        # Create subdirectories
        docs_folder = agent_folder / "docs"
        docs_folder.mkdir(exist_ok=True)
        knows_folder = agent_folder / "knows"
        knows_folder.mkdir(exist_ok=True)

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extract tar file - extract only the files, not the directory structure
        with tarfile.open(temp_file_path, "r:gz") as tar:
            # Get all members and filter out directories
            members = tar.getmembers()
            for member in members:
                # Skip directories
                if member.isdir():
                    continue

                # Extract only the filename (remove the path)
                member.name = os.path.basename(member.name)
                tar.extract(member, agent_folder)

        # Update agent config with folder path
        updated_config = db_agent.config.copy() if db_agent.config else {}
        updated_config["folder_path"] = str(agent_folder)
        db_agent.config = updated_config

        # Force update by marking as dirty
        flag_modified(db_agent, "config")
        db.commit()

        # Clean up temp file
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

        logger.info(f"Successfully imported agent {db_agent.id} from tar file")

        return TarImportResponse(success=True, agent_id=db_agent.id, message=f"Successfully imported agent {agent_name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing agent from tar: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import agent: {str(e)}")
