"""
Agent routers - consolidated routing for agent-related endpoints.
Thin routing layer that delegates business logic to services.
"""

import logging
from typing import List
import os
import asyncio

import json
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    Form,
    UploadFile,
    Query,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import (
    AgentCreate,
    AgentRead,
    AgentGenerationRequest,
    AgentGenerationResponse,
    AgentDescriptionRequest,
    AgentDescriptionResponse,
    AgentDeployRequest,
    AgentDeployResponse,
    DanaSyntaxCheckRequest,
    DanaSyntaxCheckResponse,
    CodeValidationRequest,
    CodeValidationResponse,
    CodeFixRequest,
    CodeFixResponse,
    ProcessAgentDocumentsRequest,
    ProcessAgentDocumentsResponse,
    DocumentRead,
)
from dana.api.services.agent_service import get_agent_service, AgentService
from dana.api.services.agent_manager import get_agent_manager, AgentManager
from dana.api.services.document_service import get_document_service, DocumentService
from dana.api.core.models import AgentChatHistory
from dana.api.services.domain_knowledge_service import (
    get_domain_knowledge_service,
    DomainKnowledgeService,
)
from dana.api.core.models import Agent
from datetime import datetime, timezone
from dana.api.services.knowledge_status_manager import (
    KnowledgeStatusManager,
    KnowledgeGenerationManager,
)
from dana.api.server.server import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


async def _auto_generate_basic_agent_code(
    agent_id: int,
    agent_name: str,
    agent_description: str,
    agent_config: dict,
    agent_manager,
) -> str | None:
    """Auto-generate basic Dana code for a newly created agent."""
    try:
        from pathlib import Path

        logger.info(
            f"Auto-generating basic Dana code for agent {agent_id}: {agent_name}"
        )

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
        await _create_basic_dana_files(
            agent_folder=agent_folder,
            agent_name=agent_name,
            agent_description=agent_description,
            agent_config=agent_config,
        )

        logger.info(
            f"Successfully created agent folder and basic Dana code at: {agent_folder}"
        )
        return str(agent_folder)

    except Exception as e:
        logger.error(f"Error auto-generating basic Dana code: {e}")
        raise e


async def _create_basic_dana_files(
    agent_folder,  # Path object
    agent_name: str,
    agent_description: str,
    agent_config: dict,
):
    """Create basic Dana files for the agent."""

    # Get specialties and skills from config
    specialties = agent_config.get("specialties", "general assistance")
    skills = agent_config.get("skills", "problem solving")

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
from knowledge import doc_knowledge, contextual_knowledge
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


@router.post("/generate", response_model=AgentGenerationResponse)
async def generate_agent(
    request: AgentGenerationRequest, agent_service=Depends(get_agent_service)
):
    """
    Generate Dana agent code from conversation messages.

    Args:
        request: Agent generation request with messages and options
        agent_service: Agent service dependency

    Returns:
        AgentGenerationResponse with generated code and analysis
    """
    try:
        logger.info(
            f"Received agent generation request with {len(request.messages)} messages"
        )

        # Convert messages to dict format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Generate agent code using service
        (
            dana_code,
            error,
            conversation_analysis,
            multi_file_project,
        ) = await agent_service.generate_agent_code(
            messages=messages,
            current_code=request.current_code or "",
            multi_file=request.multi_file,
        )

        if error:
            logger.error(f"Error in agent generation: {error}")
            return AgentGenerationResponse(success=False, error=error)

        # Analyze agent capabilities
        capabilities = await agent_service.analyze_agent_capabilities(
            dana_code=dana_code,
            messages=messages,
            multi_file_project=multi_file_project,
        )

        # Extract agent name and description from generated code
        agent_name, agent_description = _extract_agent_info_from_code(dana_code)

        return AgentGenerationResponse(
            success=True,
            dana_code=dana_code,
            agent_name=agent_name,
            agent_description=agent_description,
            capabilities=capabilities,
            multi_file_project=multi_file_project,
            needs_more_info=conversation_analysis.get("needs_more_info", False),
            follow_up_message=conversation_analysis.get("follow_up_message"),
            suggested_questions=conversation_analysis.get("suggested_questions", []),
        )

    except Exception as e:
        logger.error(f"Error in agent generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/describe", response_model=AgentDescriptionResponse)
async def refine_agent_description(
    request: AgentDescriptionRequest, db: Session = Depends(get_db)
):
    """
    Phase 1: Refine agent description based on conversation.

    This endpoint focuses on understanding user requirements and refining
    the agent description without generating code.

    Args:
        request: Agent description refinement request
        db: Database session

    Returns:
        AgentDescriptionResponse with refined description
    """
    try:
        logger.info(
            f"Received agent description request with {len(request.messages)} messages"
        )

        # Use AgentManager for consistent handling (same as old endpoint)
        agent_manager = get_agent_manager()

        # Convert messages to the format expected by AgentManager
        messages_dict = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Create agent description using AgentManager
        result = await agent_manager.create_agent_description(
            messages=messages_dict,
            agent_id=request.agent_id,
            existing_agent_data=request.agent_data,
        )

        # Convert capabilities to dict if it's an AgentCapabilities object
        capabilities = result["capabilities"]
        if capabilities is not None:
            if hasattr(capabilities, "dict"):
                # Convert AgentCapabilities object to dict for Pydantic serialization
                capabilities_dict = capabilities.dict()
            elif hasattr(capabilities, "__dict__"):
                # Fallback to convert object attributes to dict
                capabilities_dict = {
                    "summary": getattr(capabilities, "summary", None),
                    "knowledge": getattr(capabilities, "knowledge", None),
                    "workflow": getattr(capabilities, "workflow", None),
                    "tools": getattr(capabilities, "tools", None),
                }
            elif isinstance(capabilities, dict):
                # Already a dict
                capabilities_dict = capabilities
            else:
                # Convert any other object to dict
                try:
                    capabilities_dict = {
                        "summary": str(capabilities) if capabilities else None,
                        "knowledge": [],
                        "workflow": [],
                        "tools": [],
                    }
                except:
                    capabilities_dict = None
        else:
            capabilities_dict = capabilities

        # Convert to AgentDescriptionResponse (same format as old endpoint)
        return AgentDescriptionResponse(
            success=result["success"],
            agent_id=result["agent_id"] or 0,
            agent_name=result["agent_name"],
            agent_description=result["agent_description"],
            capabilities=capabilities_dict,
            follow_up_message=result["follow_up_message"],
            suggested_questions=result["suggested_questions"],
            ready_for_code_generation=result["ready_for_code_generation"],
            agent_folder=result["agent_folder"],  # <-- Ensure this is included
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Error in describe_agent endpoint: {e}", exc_info=True)
        return AgentDescriptionResponse(
            success=False,
            agent_id=0,
            error=f"Failed to process agent description: {str(e)}",
        )


@router.post("/deploy", response_model=AgentDeployResponse)
async def deploy_agent(request: AgentDeployRequest, db: Session = Depends(get_db)):
    """
    Deploy an agent with generated code.

    Args:
        request: Agent deployment request
        db: Database session

    Returns:
        AgentDeployResponse with deployment status
    """
    try:
        logger.info(f"Received agent deployment request for: {request.name}")

        # Create agent record in database
        from dana.api.core.models import Agent

        agent = Agent(
            name=request.name,
            description=request.description,
            config=request.config,
            generation_phase="code_generated",
        )

        if request.dana_code:
            # Single file deployment
            # Save code to file system and update agent record
            pass
        elif request.multi_file_project:
            # Multi-file deployment
            # Save all files and update agent record
            pass

        db.add(agent)
        db.commit()
        db.refresh(agent)

        agent_read = AgentRead(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            config=agent.config,
            generation_phase=agent.generation_phase,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

        return AgentDeployResponse(success=True, agent=agent_read)

    except Exception as e:
        logger.error(f"Error in agent deployment endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/syntax-check", response_model=DanaSyntaxCheckResponse)
async def check_dana_syntax(request: DanaSyntaxCheckRequest):
    """
    Check Dana code syntax for errors.

    Args:
        request: Syntax check request

    Returns:
        DanaSyntaxCheckResponse with syntax validation results
    """
    try:
        logger.info("Received Dana syntax check request")

        # This would use DanaSandbox to validate syntax
        # Placeholder implementation
        return DanaSyntaxCheckResponse(success=True, output="Syntax is valid")

    except Exception as e:
        logger.error(f"Error in syntax check endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        return CodeValidationResponse(
            success=True, is_valid=True, errors=[], warnings=[], suggestions=[]
        )

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


@router.post("/process-documents", response_model=ProcessAgentDocumentsResponse)
async def process_agent_documents(
    request: ProcessAgentDocumentsRequest, agent_service=Depends(get_agent_service)
):
    """
    Process documents for agent knowledge base.

    Args:
        request: Document processing request

    Returns:
        ProcessAgentDocumentsResponse with processing results
    """
    try:
        logger.info(
            f"Received document processing request for folder: {request.document_folder}"
        )

        # Process documents using agent service
        result = await agent_service.process_agent_documents(request)

        return ProcessAgentDocumentsResponse(
            success=result["success"],
            message=result.get("message", "Documents processed successfully"),
            agent_name=result.get("agent_name"),
            agent_description=result.get("agent_description"),
            processing_details=result.get("processing_details", {}),
            dana_code=result.get("dana_code"),
            multi_file_project=result.get("multi_file_project"),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Error in document processing endpoint: {e}")
        return ProcessAgentDocumentsResponse(
            success=False,
            message="Document processing failed",
            error=f"Failed to process documents: {str(e)}",
        )


# CRUD Operations for Agents
@router.get("/", response_model=List[AgentRead])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all agents with pagination."""
    try:
        from dana.api.core.models import Agent

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
        import json
        from pathlib import Path
        
        # Load prebuilt agents from the assets file
        assets_path = Path(__file__).parent.parent / "server" / "assets" / "prebuilt_agents.json"
        
        if not assets_path.exists():
            logger.warning(f"Prebuilt agents file not found at {assets_path}")
            return []
        
        with open(assets_path, 'r', encoding='utf-8') as f:
            prebuilt_agents = json.load(f)
        
        # Add mock IDs and additional UI properties for compatibility
        for i, agent in enumerate(prebuilt_agents, start=1000):  # Start from 1000 to avoid conflicts
            agent["id"] = i
            agent["is_prebuilt"] = True
            
            # Add UI-specific properties based on domain
            domain = agent.get("config", {}).get("domain", "Other")
            agent["avatarColor"] = {
                "Finance": "from-purple-400 to-green-400",
                "Semiconductor": "from-green-400 to-blue-400", 
                "Research": "from-purple-400 to-pink-400",
                "Sales": "from-yellow-400 to-purple-400",
                "Engineering": "from-blue-400 to-green-400"
            }.get(domain, "from-gray-400 to-gray-600")
            
            # Add rating and accuracy for UI display
            agent["rating"] = 4.8 + (i % 3) * 0.1  # Vary between 4.8-5.0
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
        from dana.api.core.models import Agent

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
        from dana.api.core.models import Agent

        # Create the agent in database first
        db_agent = Agent(
            name=agent.name, description=agent.description, config=agent.config
        )

        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        # Auto-generate basic Dana code and agent folder
        try:
            folder_path = await _auto_generate_basic_agent_code(
                agent_id=db_agent.id,
                agent_name=agent.name,
                agent_description=agent.description,
                agent_config=agent.config or {},
                agent_manager=agent_manager,
            )

            # Update agent with folder path
            if folder_path:
                # Update config with folder_path
                updated_config = db_agent.config.copy() if db_agent.config else {}
                updated_config["folder_path"] = folder_path

                # Update database record
                db_agent.config = updated_config
                db_agent.generation_phase = "code_generated"

                # Force update by marking as dirty
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(db_agent, "config")

                db.commit()
                db.refresh(db_agent)
                logger.info(
                    f"Updated agent {db_agent.id} with folder_path: {folder_path}"
                )
                logger.info(f"Agent config after update: {db_agent.config}")

        except Exception as code_gen_error:
            logger.error(
                f"Failed to auto-generate code for agent {db_agent.id}: {code_gen_error}"
            )
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Don't fail the agent creation if code generation fails

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
async def update_agent(
    agent_id: int, agent: AgentCreate, db: Session = Depends(get_db)
):
    """Update an agent."""
    try:
        from dana.api.core.models import Agent

        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        db_agent.name = agent.name
        db_agent.description = agent.description
        db_agent.config = agent.config

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
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent."""
    try:
        from dana.api.core.models import Agent

        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        db.delete(db_agent)
        db.commit()

        return {"message": "Agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional endpoints expected by UI
@router.post("/generate-from-prompt", response_model=AgentGenerationResponse)
async def generate_agent_from_prompt(
    request: dict,
    agent_service: AgentService = Depends(get_agent_service),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    """Generate agent from specific prompt."""
    try:
        logger.info("Received generate from prompt request")

        prompt = request.get("prompt", "")
        messages = request.get("messages", [])
        agent_summary = request.get("agent_summary", {})

        # Generate agent code using service
        result = await agent_manager.generate_agent_code(
            agent_metadata=agent_summary, messages=messages, prompt=prompt
        )

        return AgentGenerationResponse(
            success=result["success"],
            dana_code=result["dana_code"],
            agent_name=result["agent_name"],
            agent_description=result["agent_description"],
            capabilities=result["capabilities"],
            auto_stored_files=result["auto_stored_files"],
            multi_file_project=result["multi_file_project"],
            agent_id=result["agent_id"],
            agent_folder=result["agent_folder"],
            phase=result["phase"],
            ready_for_code_generation=result["ready_for_code_generation"],
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Error in generate from prompt endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/update-description", response_model=AgentDescriptionResponse)
async def update_agent_description(
    agent_id: int,
    request: AgentDescriptionRequest,
    agent_service=Depends(get_agent_service),
):
    """Update agent description."""
    try:
        logger.info(f"Received update description request for agent {agent_id}")

        # Convert messages to dict format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Analyze conversation completeness
        conversation_analysis = await agent_service.analyze_conversation_completeness(
            messages
        )

        return AgentDescriptionResponse(
            success=True,
            agent_id=agent_id,
            follow_up_message=conversation_analysis.get("follow_up_message"),
            suggested_questions=conversation_analysis.get("suggested_questions", []),
            ready_for_code_generation=not conversation_analysis.get(
                "needs_more_info", False
            ),
        )

    except Exception as e:
        logger.error(f"Error in update description endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=CodeValidationResponse)
async def validate_agent_code(request: CodeValidationRequest):
    """Validate agent code."""
    try:
        logger.info("Received code validation request")

        # Placeholder implementation
        return CodeValidationResponse(
            success=True, is_valid=True, errors=[], warnings=[], suggestions=[]
        )

    except Exception as e:
        logger.error(f"Error in validate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fix", response_model=CodeFixResponse)
async def fix_agent_code(request: CodeFixRequest):
    """Fix agent code."""
    try:
        logger.info("Received code fix request")

        # Placeholder implementation
        return CodeFixResponse(
            success=True, fixed_code=request.code, applied_fixes=[], remaining_errors=[]
        )

    except Exception as e:
        logger.error(f"Error in fix endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-knowledge")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    agent_id: str = Form(None),
    conversation_context: str = Form(None),  # JSON string of conversation context
    agent_info: str = Form(
        None
    ),  # JSON string of agent info (must include folder_path)
):
    """
    Upload a knowledge file for an agent.
    Creates a docs folder in the agent directory and stores the file there.
    Also updates the tools.na file with RAG declarations.
    Requires agent_info to include folder_path.
    """
    try:
        logger.info(f"Uploading knowledge file: {file.filename}")

        # Parse conversation context and agent info
        conv_context = json.loads(conversation_context) if conversation_context else []
        agent_data = json.loads(agent_info) if agent_info else {}

        if not agent_data.get("folder_path"):
            logger.error("Missing folder_path in agent_info for knowledge upload")
            return {
                "success": False,
                "error": "Missing folder_path in agent_info. Please complete agent creation before uploading knowledge files.",
            }

        # Read file content
        file_content = await file.read()

        # Upload file using AgentManager
        agent_manager = get_agent_manager()
        result = await agent_manager.upload_knowledge_file(
            file_content=file_content,
            filename=file.filename,
            agent_metadata=agent_data,
            conversation_context=conv_context,
        )

        logger.info(f"Successfully uploaded knowledge file: {file.filename}")

        return {
            "success": result["success"],
            "file_path": result["file_path"],
            "message": result["message"],
            "updated_capabilities": result["updated_capabilities"],
            "generated_response": result["generated_response"],
            "ready_for_code_generation": result["ready_for_code_generation"],
            "agent_metadata": result["agent_metadata"],
        }

    except Exception as e:
        logger.error(f"Error uploading knowledge file: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


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
        from dana.api.core.models import Agent

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
            from sqlalchemy.orm.attributes import flag_modified

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
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/files")
async def list_agent_files(agent_id: int, db: Session = Depends(get_db)):
    """List all files in the agent's folder structure."""
    try:
        # Get the agent to find its folder_path
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            return {"files": [], "message": "Agent folder not found"}

        # List all files in the agent folder
        from pathlib import Path

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
                    "type": "dana"
                    if file_path.suffix == ".na"
                    else "document"
                    if relative_path.startswith("docs/")
                    else "other",
                }
                files.append(file_info)

        return {"files": files}

    except Exception as e:
        logger.error(f"Error listing agent files for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/files/{file_path:path}")
async def get_agent_file_content(
    agent_id: int, file_path: str, db: Session = Depends(get_db)
):
    """Get the content of a specific file in the agent's folder."""
    try:
        # Get the agent to find its folder_path
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            raise HTTPException(status_code=404, detail="Agent folder not found")

        # Construct full file path and validate it's within agent folder
        from pathlib import Path

        agent_folder = Path(folder_path)
        full_file_path = agent_folder / file_path

        # Security check: ensure file is within agent folder
        try:
            full_file_path.resolve().relative_to(agent_folder.resolve())
        except ValueError:
            raise HTTPException(
                status_code=403, detail="Access denied: file outside agent folder"
            )

        if not full_file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not full_file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read file content
        try:
            content = full_file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # For binary files, return base64 encoded content
            import base64

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
async def update_agent_file_content(
    agent_id: int, file_path: str, request: dict, db: Session = Depends(get_db)
):
    """Update the content of a specific file in the agent's folder."""
    try:
        # Get the agent to find its folder_path
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            raise HTTPException(status_code=404, detail="Agent folder not found")

        # Construct full file path and validate it's within agent folder
        from pathlib import Path

        agent_folder = Path(folder_path)
        full_file_path = agent_folder / file_path

        # Security check: ensure file is within agent folder
        try:
            full_file_path.resolve().relative_to(agent_folder.resolve())
        except ValueError:
            raise HTTPException(
                status_code=403, detail="Access denied: file outside agent folder"
            )

        content = request.get("content", "")
        encoding = request.get("encoding", "utf-8")

        # Create parent directories if they don't exist
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file content
        if encoding == "base64":
            import base64

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


def _extract_agent_info_from_code(dana_code: str) -> tuple[str | None, str | None]:
    """
    Extract agent name and description from generated Dana code.

    Args:
        dana_code: The generated Dana code

    Returns:
        Tuple of (agent_name, agent_description)
    """
    lines = dana_code.split("\\n")
    agent_name = None
    agent_description = None

    for i, line in enumerate(lines):
        if line.strip().startswith("agent ") and line.strip().endswith(":"):
            # Next few lines should contain name and description
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if "name : str =" in next_line:
                    agent_name = next_line.split("=")[1].strip().strip('"')
                elif "description : str =" in next_line:
                    agent_description = next_line.split("=")[1].strip().strip('"')

    return agent_name, agent_description


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
    from sqlalchemy.orm import sessionmaker
    from dana.api.core.database import engine

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

        role = (
            agent.config.get("role")
            if agent.config and agent.config.get("role")
            else (agent.description or "Domain Expert")
        )
        topic = (
            agent.config.get("topic")
            if agent.config and agent.config.get("topic")
            else (agent.name or "General Topic")
        )
        print(f"[generate-knowledge] Using topic: {topic}, role: {role}")

        from dana.api.services.domain_knowledge_service import DomainKnowledgeService

        domain_service_thread = DomainKnowledgeService()
        tree = asyncio.run(
            domain_service_thread.get_agent_domain_knowledge(agent_id, db_thread)
        )
        if not tree:
            print(
                f"[generate-knowledge] Domain knowledge tree not found for agent {agent_id}"
            )
            return
        print(f"[generate-knowledge] Loaded domain knowledge tree for agent {agent_id}")

        def collect_leaf_paths(node, path_so_far):
            path = path_so_far + [node.topic]
            if not getattr(node, "children", []):
                return [(path, node)]
            leaves = []
            for child in getattr(node, "children", []):
                leaves.extend(collect_leaf_paths(child, path))
            return leaves

        leaf_paths = collect_leaf_paths(tree.root, [])
        print(f"[generate-knowledge] Collected {len(leaf_paths)} leaf topics from tree")

        # 1. Build or update knowledge_status.json
        status_path = os.path.join(knows_folder, "knowledge_status.json")
        status_manager = KnowledgeStatusManager(status_path, agent_id=str(agent_id))
        now_str = datetime.now(timezone.utc).isoformat() + "Z"
        # Add/update all leaves
        for path, leaf_node in leaf_paths:
            area_name = " - ".join(path)
            safe_area = area_name.replace("/", "_").replace(" ", "_").replace("-", "_")
            file_name = f"{safe_area}.json"
            status_manager.add_or_update_topic(
                path=area_name,
                file=file_name,
                last_topic_update=now_str,
                status=None,  # Don't force status change if already present
            )
        # Remove topics that are no longer in the tree
        all_paths = set([" - ".join(path) for path, _ in leaf_paths])
        for entry in status_manager.load()["topics"]:
            if entry["path"] not in all_paths:
                status_manager.remove_topic(entry["path"])

        # 2. Only queue topics with status 'pending' or 'failed'
        pending = status_manager.get_pending_or_failed()
        print(
            f"[generate-knowledge] {len(pending)} topics to generate (pending or failed)"
        )

        # 3. Use KnowledgeGenerationManager to run the queue
        manager = KnowledgeGenerationManager(
            status_manager, max_concurrent=4, ws_manager=ws_manager
        )

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
        from dana.api.core.models import Agent

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
async def test_agent_by_id(
    agent_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Test an agent by ID with a message.
    
    This endpoint gets the agent details from the database by ID,
    then runs the Dana file execution logic similar to /test-agent route.
    
    Args:
        agent_id: The ID of the agent to test
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
        
        # Get the agent from database
        from dana.api.core.models import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Extract agent details
        agent_name = agent.name
        agent_description = agent.description or "A Dana agent"
        folder_path = agent.config.get("folder_path") if agent.config else None
        
        logger.info(f"Testing agent {agent_id} ({agent_name}) with message: '{message}'")
        
        # Import the test logic from agent_test module
        from dana.core.runtime.modules.core import initialize_module_system, reset_module_system
        from dana.api.routers.agent_test import AgentTestRequest, test_agent
        initialize_module_system()
        reset_module_system()
        
        
        # Create test request using agent details
        test_request = AgentTestRequest(
            agent_code="",  # Will use folder_path instead
            message=message,
            agent_name=agent_name,
            agent_description=agent_description,
            context=request.get("context", {"user_id": "test_user"}),
            folder_path=folder_path
        )
        
        # Call the existing test_agent function
        result = await test_agent(test_request)
        
        return {
            "success": result.success,
            "agent_response": result.agent_response,
            "error": result.error,
            "agent_id": agent_id,
            "agent_name": agent_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


