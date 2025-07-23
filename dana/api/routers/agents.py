"""
Agent routers - consolidated routing for agent-related endpoints.
Thin routing layer that delegates business logic to services.
"""

import logging
from typing import Any, List
import os

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Query
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import (
    AgentCreate, AgentRead, AgentGenerationRequest, AgentGenerationResponse,
    AgentDescriptionRequest, AgentDescriptionResponse, AgentCodeGenerationRequest,
    AgentDeployRequest, AgentDeployResponse, DanaSyntaxCheckRequest, DanaSyntaxCheckResponse,
    CodeValidationRequest, CodeValidationResponse, CodeFixRequest, CodeFixResponse,
    ProcessAgentDocumentsRequest, ProcessAgentDocumentsResponse, DocumentRead
)
from dana.api.services.agent_service import get_agent_service, AgentService
from dana.api.services.agent_manager import get_agent_manager, AgentManager
from dana.api.services.document_service import get_document_service, DocumentService
from dana.api.core.models import AgentChatHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


async def _auto_generate_basic_agent_code(
    agent_id: int,
    agent_name: str,
    agent_description: str,
    agent_config: dict,
    agent_manager
) -> str | None:
    """Auto-generate basic Dana code for a newly created agent."""
    try:
        from pathlib import Path
        import time
        
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
        await _create_basic_dana_files(
            agent_folder=agent_folder,
            agent_name=agent_name,
            agent_description=agent_description,
            agent_config=agent_config
        )
        
        logger.info(f"Successfully created agent folder and basic Dana code at: {agent_folder}")
        return str(agent_folder)
        
    except Exception as e:
        logger.error(f"Error auto-generating basic Dana code: {e}")
        raise e


async def _create_basic_dana_files(
    agent_folder,  # Path object
    agent_name: str,
    agent_description: str,
    agent_config: dict
):
    """Create basic Dana files for the agent."""
    
    # Get specialties and skills from config
    specialties = agent_config.get("specialties", "general assistance")
    skills = agent_config.get("skills", "problem solving")
    
    # TODO: Correct the content
    # Create main.na - the entry point
    main_content = f'''/*
 * {agent_name} - Main Entry Point
 * {agent_description if agent_description else "A helpful AI agent"}
 * 
 * Specialties: {specialties}
 * Skills: {skills}
 */

import common
import tools
import knowledge
import workflows

def main(input: str) -> str {{
    log(f"{{agent_name}} received input: {{input}}")
    
    # Process the input using available knowledge and tools
    result = process_request(input)
    
    log(f"{{agent_name}} responding with: {{result}}")
    return result
}}

def process_request(input: str) -> str {{
    /*
     * Main processing logic for the agent
     * Customize this function based on your agent's specific needs
     */
    
    # Check if this is a greeting
    if input.lower() in ["hello", "hi", "hey"] {{
        return f"Hello! I'm {{agent_name}}, and I specialize in {specialties}. How can I help you today?"
    }}
    
    # Default response with agent capabilities
    return f"I'm {{agent_name}}, ready to help with {specialties}. You asked: {{input}}. How can I assist you further?"
}}

# Agent metadata for reference
agent_name = "{agent_name}"
agent_description = "{agent_description if agent_description else 'A helpful AI agent'}"
agent_specialties = "{specialties}"
agent_skills = "{skills}"
'''
    
    # Create common.na - shared utilities
    common_content = '''/*
 * Common utilities and shared functions
 */

def format_response(message: str, agent_name: str) -> str {
    return f"[{agent_name}]: {message}"
}

def log_interaction(input: str, output: str) {
    log(f"Input: {input}")
    log(f"Output: {output}")
}

def validate_input(input: str) -> bool {
    return input != null and input != ""
}
'''
    
    # Create tools.na - agent tools and capabilities
    tools_content = '''/*
 * Agent tools and capabilities
 * Add your custom tools and integrations here
 */

def get_current_time() -> str {
    # Placeholder for time functionality
    return "Current time functionality not implemented"
}

def search_knowledge(query: str) -> str {
    # Placeholder for knowledge search
    return f"Knowledge search for '{query}' - implement knowledge base integration"
}

def calculate(expression: str) -> str {
    # Placeholder for calculation functionality
    return f"Calculation '{expression}' - implement math operations"
}
'''
    
    # Create knowledge.na - knowledge base
    knowledge_content = '''/*
 * Agent knowledge base
 * Define your agent's knowledge and expertise here
 */

def get_expertise_areas() -> list[str] {
    return [
        "General assistance",
        "Problem solving",
        "Information processing"
    ]
}

def get_agent_background() -> str {
    return """
    I am an AI agent designed to be helpful, harmless, and honest.
    I can assist with various tasks and provide information on many topics.
    """
}

def answer_question(question: str) -> str {
    # Placeholder for knowledge-based question answering
    return f"I received your question: '{question}'. Please implement specific knowledge handling for better responses."
}
'''
    
    # Create workflows.na - agent workflows
    workflows_content = '''/*
 * Agent workflows and processes
 * Define complex multi-step processes here
 */

def standard_workflow(input: str) -> str {
    # Standard processing workflow
    log("Starting standard workflow")
    
    # Step 1: Validate input
    if not validate_input(input) {
        return "Invalid input provided"
    }
    
    # Step 2: Process request
    result = process_with_context(input)
    
    # Step 3: Format response
    formatted_result = format_response(result, agent_name)
    
    log("Completed standard workflow")
    return formatted_result
}

def process_with_context(input: str) -> str {
    # Add context-aware processing here
    return f"Processed: {input}"
}
'''
    
    # Write all files
    with open(agent_folder / "main.na", "w") as f:
        f.write(main_content)
    
    with open(agent_folder / "common.na", "w") as f:
        f.write(common_content)
        
    with open(agent_folder / "tools.na", "w") as f:
        f.write(tools_content)
        
    with open(agent_folder / "knowledge.na", "w") as f:
        f.write(knowledge_content)
        
    with open(agent_folder / "workflows.na", "w") as f:
        f.write(workflows_content)


@router.post("/generate", response_model=AgentGenerationResponse)
async def generate_agent(
    request: AgentGenerationRequest,
    agent_service = Depends(get_agent_service)
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
        logger.info(f"Received agent generation request with {len(request.messages)} messages")
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Generate agent code using service
        dana_code, error, conversation_analysis, multi_file_project = await agent_service.generate_agent_code(
            messages=messages,
            current_code=request.current_code or "",
            multi_file=request.multi_file
        )
        
        if error:
            logger.error(f"Error in agent generation: {error}")
            return AgentGenerationResponse(success=False, error=error)
        
        # Analyze agent capabilities
        capabilities = await agent_service.analyze_agent_capabilities(
            dana_code=dana_code,
            messages=messages,
            multi_file_project=multi_file_project
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
            suggested_questions=conversation_analysis.get("suggested_questions", [])
        )
        
    except Exception as e:
        logger.error(f"Error in agent generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/describe", response_model=AgentDescriptionResponse)
async def refine_agent_description(
    request: AgentDescriptionRequest,
    db: Session = Depends(get_db)
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
        logger.info(f"Received agent description request with {len(request.messages)} messages")
        
        # Use AgentManager for consistent handling (same as old endpoint)
        agent_manager = get_agent_manager()
        
        # Convert messages to the format expected by AgentManager
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Create agent description using AgentManager
        result = await agent_manager.create_agent_description(
            messages=messages_dict,
            agent_id=request.agent_id,
            existing_agent_data=request.agent_data
        )
        
        # Convert capabilities to dict if it's an AgentCapabilities object
        capabilities = result["capabilities"]
        if capabilities is not None:
            if hasattr(capabilities, 'dict'):
                # Convert AgentCapabilities object to dict for Pydantic serialization
                capabilities_dict = capabilities.dict()
            elif hasattr(capabilities, '__dict__'):
                # Fallback to convert object attributes to dict
                capabilities_dict = {
                    "summary": getattr(capabilities, 'summary', None),
                    "knowledge": getattr(capabilities, 'knowledge', None),
                    "workflow": getattr(capabilities, 'workflow', None),
                    "tools": getattr(capabilities, 'tools', None)
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
                        "tools": []
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
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in describe_agent endpoint: {e}", exc_info=True)
        return AgentDescriptionResponse(
            success=False,
            agent_id=0,
            error=f"Failed to process agent description: {str(e)}"
        )


@router.post("/generate-code", response_model=AgentGenerationResponse)
async def generate_agent_code(
    request: AgentCodeGenerationRequest,
    agent_service = Depends(get_agent_service)
):
    """
    Phase 2: Generate agent code from refined description.
    
    Args:
        request: Agent code generation request
        agent_service: Agent service dependency
        
    Returns:
        AgentGenerationResponse with generated code
    """
    try:
        logger.info(f"Received Phase 2 agent code generation request for agent {request.agent_id}")
        
        # This would typically load agent data from database
        # For now, use placeholder data
        agent_summary = {
            "name": "Generated Agent",
            "description": "A generated agent",
            "capabilities": {}
        }
        
        # Generate code using service
        dana_code, error, multi_file_project = await agent_service.generate_agent_files_from_prompt(
            prompt="Generate agent code based on description",
            messages=[],  # Would load from agent's conversation history
            agent_summary=agent_summary,
            multi_file=request.multi_file
        )
        
        if error:
            logger.error(f"Error in Phase 2 generation: {error}")
            return AgentGenerationResponse(success=False, error=error)
        
        return AgentGenerationResponse(
            success=True,
            dana_code=dana_code,
            multi_file_project=multi_file_project,
            agent_id=request.agent_id
        )
        
    except Exception as e:
        logger.error(f"Error in agent code generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy", response_model=AgentDeployResponse)
async def deploy_agent(
    request: AgentDeployRequest,
    db: Session = Depends(get_db)
):
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
            generation_phase="code_generated"
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
            updated_at=agent.updated_at
        )
        
        return AgentDeployResponse(
            success=True,
            agent=agent_read
        )
        
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
        return DanaSyntaxCheckResponse(
            success=True,
            output="Syntax is valid"
        )
        
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
            success=True,
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
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
            remaining_errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error in code fix endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-documents", response_model=ProcessAgentDocumentsResponse)
async def process_agent_documents(request: ProcessAgentDocumentsRequest, agent_service = Depends(get_agent_service)):
    """
    Process documents for agent knowledge base.
    
    Args:
        request: Document processing request
        
    Returns:
        ProcessAgentDocumentsResponse with processing results
    """
    try:
        logger.info(f"Received document processing request for folder: {request.document_folder}")
        
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
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in document processing endpoint: {e}")
        return ProcessAgentDocumentsResponse(
            success=False,
            message="Document processing failed",
            error=f"Failed to process documents: {str(e)}"
        )


# CRUD Operations for Agents
@router.get("/", response_model=List[AgentRead])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
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
                updated_at=agent.updated_at
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
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
            updated_at=agent.updated_at
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
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Create a new agent with auto-generated basic Dana code."""
    try:
        from dana.api.core.models import Agent
        
        # Create the agent in database first
        db_agent = Agent(
            name=agent.name,
            description=agent.description,
            config=agent.config
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
                agent_manager=agent_manager
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
                logger.info(f"Updated agent {db_agent.id} with folder_path: {folder_path}")
                logger.info(f"Agent config after update: {db_agent.config}")
                
        except Exception as code_gen_error:
            logger.error(f"Failed to auto-generate code for agent {db_agent.id}: {code_gen_error}")
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
            updated_at=db_agent.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: int,
    agent: AgentCreate,
    db: Session = Depends(get_db)
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
            updated_at=db_agent.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
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
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Generate agent from specific prompt."""
    try:
        logger.info("Received generate from prompt request")
        
        prompt = request.get("prompt", "")
        messages = request.get("messages", [])
        agent_summary = request.get("agent_summary", {})
        
        # Generate agent code using service
        result = await agent_manager.generate_agent_code(
            agent_metadata=agent_summary,
            messages=messages,
            prompt=prompt
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
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in generate from prompt endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/update-description", response_model=AgentDescriptionResponse)
async def update_agent_description(
    agent_id: int,
    request: AgentDescriptionRequest,
    agent_service = Depends(get_agent_service)
):
    """Update agent description."""
    try:
        logger.info(f"Received update description request for agent {agent_id}")
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Analyze conversation completeness
        conversation_analysis = await agent_service.analyze_conversation_completeness(messages)
        
        return AgentDescriptionResponse(
            success=True,
            agent_id=agent_id,
            follow_up_message=conversation_analysis.get("follow_up_message"),
            suggested_questions=conversation_analysis.get("suggested_questions", []),
            ready_for_code_generation=not conversation_analysis.get("needs_more_info", False)
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
            success=True,
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
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
            success=True,
            fixed_code=request.code,
            applied_fixes=[],
            remaining_errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error in fix endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-knowledge")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    agent_id: str = Form(None),
    conversation_context: str = Form(None),  # JSON string of conversation context
    agent_info: str = Form(None),  # JSON string of agent info (must include folder_path)
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
        import json
        conv_context = json.loads(conversation_context) if conversation_context else []
        agent_data = json.loads(agent_info) if agent_info else {}
        
        if not agent_data.get('folder_path'):
            logger.error('Missing folder_path in agent_info for knowledge upload')
            return {"success": False, "error": "Missing folder_path in agent_info. Please complete agent creation before uploading knowledge files."}

        # Read file content
        file_content = await file.read()

        # Upload file using AgentManager
        agent_manager = get_agent_manager()
        result = await agent_manager.upload_knowledge_file(
            file_content=file_content,
            filename=file.filename,
            agent_metadata=agent_data,
            conversation_context=conv_context
        )

        logger.info(f"Successfully uploaded knowledge file: {file.filename}")

        return {
            "success": result["success"],
            "file_path": result["file_path"],
            "message": result["message"],
            "updated_capabilities": result["updated_capabilities"],
            "generated_response": result["generated_response"],
            "ready_for_code_generation": result["ready_for_code_generation"],
            "agent_metadata": result["agent_metadata"]
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
    document_service: DocumentService = Depends(get_document_service)
):
    """Upload a document to a specific agent's folder."""
    try:
        # Get the agent to find its folder_path
        from dana.api.core.models import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        if not agent.folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")
            os.makedirs(folder_path, exist_ok=True)
            agent.folder_path = folder_path
            db.commit()
            db.refresh(agent)
        else:
            folder_path = agent.folder_path

        # Use the agent's docs folder as the upload directory
        docs_folder = os.path.join(folder_path, "docs")
        os.makedirs(docs_folder, exist_ok=True)
        
        document = await document_service.upload_document(
            file=file.file,
            filename=file.filename,
            topic_id=topic_id,
            agent_id=agent_id,
            db_session=db,
            upload_directory=docs_folder
        )
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to agent {agent_id}: {e}")
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
    type: str = Query(None, description="Filter by message type: 'chat_with_dana_build', 'smart_chat', or 'all' for both types"),
    db: Session = Depends(get_db)
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
            "created_at": h.created_at.isoformat()
        }
        for h in history
    ]