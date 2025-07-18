import io
import os
import tempfile
import zipfile
import shutil
import platform
import subprocess
import urllib.parse
import glob
from pathlib import Path
import json
import re
import uuid
import time
from datetime import UTC, datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from dana.core.lang.dana_sandbox import DanaSandbox

from .. import db, schemas, services
from ..agent_generator import analyze_agent_capabilities, generate_agent_code_from_messages, analyze_conversation_completeness
from ..schemas import (
    AgentDeployRequest,
    AgentDeployResponse,
    AgentGenerationRequest,
    AgentGenerationResponse,
    CodeFixRequest,
    CodeFixResponse,
    CodeValidationRequest,
    CodeValidationResponse,
    DanaSyntaxCheckRequest,
    DanaSyntaxCheckResponse,
    MultiFileProject,
    RunNAFileRequest,
    RunNAFileResponse,
    ProcessAgentDocumentsRequest,
    ProcessAgentDocumentsResponse,
    AgentDescriptionRequest,
    AgentDescriptionResponse,
    AgentCodeGenerationRequest,
    AgentCapabilities,
    DanaFile,
)
from ..services import run_na_file_service

router = APIRouter(prefix="/agents", tags=["agents"])

# Simple in-memory task status tracker
processing_status = {}


@router.get("/", response_model=list[schemas.AgentRead])
def list_agents(skip: int = 0, limit: int = 10, db: Session = Depends(db.get_db)):
    return services.get_agents(db, skip=skip, limit=limit)


@router.get("/{agent_id}", response_model=schemas.AgentRead)
def get_agent(agent_id: int, db: Session = Depends(db.get_db)):
    agent = services.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=schemas.AgentRead)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(db.get_db)):
    return services.create_agent(db, agent)


@router.post("/deploy", response_model=AgentDeployResponse)
async def deploy_agent(request: AgentDeployRequest, db: Session = Depends(db.get_db)):
    """
    Deploy an agent by creating database record and storing .na files in organized folder structure.

    This endpoint:
    1. Creates agent folder: agents/{agent_id}_{sanitized_name}/
    2. Writes .na files to the folder
    3. Creates metadata.json with agent info
    4. Creates database record with folder path
    5. Returns agent info + file paths
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Deploying agent: {request.name}")

        # Create the agent in database first to get ID
        agent_create_data = schemas.AgentCreate(name=request.name, description=request.description, config=request.config)

        # Create agent record
        agent = services.create_agent(db, agent_create_data)
        logger.info(f"Created agent record with ID: {agent.id}")

        # Create sanitized folder name
        sanitized_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", request.name.lower())
        folder_name = f"agent_{agent.id}_{sanitized_name}"

        # Create agents directory if it doesn't exist
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)

        # Create agent folder
        agent_folder = agents_dir / folder_name
        agent_folder.mkdir(exist_ok=True)
        logger.info(f"Created agent folder: {agent_folder}")

        # Store file paths
        file_paths = []

        # Handle single file deployment
        if request.dana_code:
            agent_file = agent_folder / "agent.na"
            with open(agent_file, "w", encoding="utf-8") as f:
                f.write(request.dana_code)
            file_paths.append(str(agent_file))
            logger.info(f"Created agent.na file: {agent_file}")

        # Handle multi-file deployment
        elif request.multi_file_project:
            project = request.multi_file_project
            for file_info in project.files:
                # Ensure .na extension
                filename = file_info.filename
                if not filename.endswith(".na"):
                    filename += ".na"

                file_path = agent_folder / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_info.content)
                file_paths.append(str(file_path))
                logger.info(f"Created file: {file_path}")

        # Create metadata.json
        metadata = {
            "agent_id": agent.id,
            "name": request.name,
            "description": request.description,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "config": request.config,
            "files": [str(Path(p).name) for p in file_paths],  # Store relative filenames
            "folder_path": str(agent_folder),
            "deployment_type": "multi_file" if request.multi_file_project else "single_file",
        }

        metadata_file = agent_folder / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        file_paths.append(str(metadata_file))
        logger.info(f"Created metadata.json: {metadata_file}")

        # Note: These are temporary files for generation preview only
        # No database operations needed for generation auto-storage

        logger.info(f"Agent deployed successfully: {agent.name} at {agent.folder_path}")

        return AgentDeployResponse(success=True, agent=agent)

    except Exception as e:
        logger.error(f"Error deploying agent: {e}", exc_info=True)
        # Rollback database changes
        db.rollback()

        # Clean up created files if any
        try:
            if "agent_folder" in locals() and agent_folder.exists():
                import shutil

                shutil.rmtree(agent_folder)
                logger.info(f"Cleaned up agent folder: {agent_folder}")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up files: {cleanup_error}")

        return AgentDeployResponse(success=False, error=f"Failed to deploy agent: {str(e)}")


@router.post("/run-na-file", response_model=RunNAFileResponse)
def run_na_file(request: RunNAFileRequest):
    return run_na_file_service(request)


@router.post("/generate", response_model=AgentGenerationResponse)
async def generate_agent(request: AgentGenerationRequest, db: Session = Depends(db.get_db)):
    """
    Generate Dana agent code from user conversation messages.
    
    This endpoint now supports two-phase generation:
    - Phase 1 (description): Focus on agent description refinement
    - Phase 2 (code_generation): Generate actual .na files
    
    Args:
        request: AgentGenerationRequest with phase and messages
        db: Database session for storing agent data
    
    Returns:
        AgentGenerationResponse with phase-appropriate data
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received agent generation request with {len(request.messages)} messages, phase: {request.phase}")

        # Convert Pydantic models to dictionaries
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        logger.info(f"Converted messages: {messages}")

        if request.phase == "description":
            # Phase 1: Focus on description refinement
            return await _handle_phase_1_generation(request, messages, db)
        elif request.phase == "code_generation":
            # Phase 2: Generate actual code
            return await _handle_phase_2_generation(request, messages, db, logger)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {request.phase}. Must be 'description' or 'code_generation'")

    except Exception as e:
        logger.error(f"Error in generate_agent endpoint: {e}", exc_info=True)
        return AgentGenerationResponse(success=False, dana_code="", error=f"Failed to generate agent code: {str(e)}")


async def _handle_phase_1_generation(
    request: AgentGenerationRequest, 
    messages: list[dict], 
    db: Session, 
) -> AgentGenerationResponse:
    """
    Handle Phase 1 generation: Focus on agent description refinement
    
    Note: In Phase 1, we don't store the agent to the database yet.
    We just return the agent object to the client, and the client will
    send the full agent object in the next chat message.
    """
    
    logger = logging.getLogger(__name__)
    logger.info("Processing Phase 1: Agent description refinement")
    
    # Use AgentManager for consistent handling
    from ..agent_manager import get_agent_manager
    agent_manager = get_agent_manager()
    
    # Convert messages to the format expected by AgentManager
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Create agent description using AgentManager
    result = await agent_manager.create_agent_description(
        messages=messages_dict,
        agent_id=request.agent_id,
        existing_agent_data=request.agent_data
    )
    
    # Convert result to AgentGenerationResponse
    return AgentGenerationResponse(
        success=result["success"],
        dana_code=None,  # No code in Phase 1
        agent_name=result["agent_name"],
        agent_description=result["agent_description"],
        capabilities=result["capabilities"],
        agent_id=result["agent_id"],
        agent_folder=result["agent_folder"],
        phase="description",
        ready_for_code_generation=result["ready_for_code_generation"],
        needs_more_info=result["needs_more_info"],
        follow_up_message=result["follow_up_message"],
        suggested_questions=result["suggested_questions"],
        error=None,
        temp_agent_data=result["agent_metadata"]
    )


async def _handle_phase_2_generation(
    request: AgentGenerationRequest, 
    messages: list[dict], 
    db: Session, 
    logger: logging.Logger
) -> AgentGenerationResponse:
    """
    Handle Phase 2 generation: Generate actual .na files and store in Phase 1 folder
    
    Note: In Phase 2, we don't touch the database yet. We just generate the .na files
    and store them in the same folder that was created in Phase 1.
    """
    logger.info("Processing Phase 2: Code generation (no database operations)")
    
    # Get agent data from client (no database operations in Phase 2)
    agent_name = None
    agent_description = None
    conversation_context = []
    agent_folder = None
    agent_id = None
    
    if request.agent_data:
        agent_name = request.agent_data.get("name", "Custom Agent")
        agent_description = request.agent_data.get("description", "A specialized agent for your needs")
        conversation_context = request.agent_data.get("generation_metadata", {}).get("conversation_context", [])
        agent_id = request.agent_data.get("id")
        agent_folder = request.agent_data.get("folder_path")
        logger.info(f"Using agent data from client: {agent_name}")
    else:
        raise HTTPException(status_code=400, detail="agent_data must be provided for Phase 2 generation")
    
    # Combine conversation context with new messages
    all_messages = conversation_context + messages
    
    # Generate Dana code
    logger.info("Calling generate_agent_code_from_messages...")
    dana_code, syntax_error, conversation_analysis, multi_file_project = await generate_agent_code_from_messages(
        all_messages, request.current_code or "", True
    )
    logger.info(f"Generated Dana code length: {len(dana_code)}")
    
    if syntax_error:
        logger.error(f"Syntax error in generated code: {syntax_error}")
        return AgentGenerationResponse(success=False, dana_code="", error=syntax_error)
    
    # Extract agent name and description from the generated code
    extracted_name, extracted_description = _extract_agent_info_from_code(dana_code, logger)
    
    # Use extracted info or fall back to existing info
    final_agent_name = extracted_name or agent_name
    final_agent_description = extracted_description or agent_description
    
    # Store generated files in the Phase 1 folder (no database operations)
    stored_files = []
    if agent_folder:
        try:
            if multi_file_project:
                logger.info(f"Storing multi-file project in Phase 1 folder: {agent_folder}")
                stored_files = await _store_multi_file_in_phase1_folder(
                    agent_folder, final_agent_name, final_agent_description, multi_file_project
                )
            else:
                logger.info(f"Storing single-file agent in Phase 1 folder: {agent_folder}")
                stored_files = await _store_single_file_in_phase1_folder(
                    agent_folder, final_agent_name, final_agent_description, dana_code
                )
            logger.info(f"Stored files in Phase 1 folder: {stored_files}")
        except Exception as e:
            logger.error(f"Failed to store files in Phase 1 folder: {e}", exc_info=True)
            return AgentGenerationResponse(success=False, dana_code="", error=f"Failed to store files: {str(e)}")
    else:
        logger.warning("No agent folder provided, cannot store files")
    
    # Analyze agent capabilities
    capabilities = None
    try:
        logger.info("Analyzing agent capabilities...")
        capabilities_data = await analyze_agent_capabilities(dana_code, all_messages, multi_file_project)
        capabilities = AgentCapabilities(
            summary=capabilities_data.get("summary"),
            knowledge=capabilities_data.get("knowledge", []),
            workflow=capabilities_data.get("workflow", []),
            tools=capabilities_data.get("tools", []),
        )
        logger.info(f"Generated capabilities summary: {capabilities.summary}")
    except Exception as e:
        logger.warning(f"Failed to analyze capabilities (non-critical): {e}")
        capabilities = None
    
    # Create multi-file project object if available
    multi_file_project_obj = None
    if multi_file_project:
        dana_files = [
            DanaFile(
                filename=file_info["filename"],
                content=file_info["content"],
                file_type=file_info["file_type"],
                description=file_info.get("description"),
                dependencies=file_info.get("dependencies", []),
            )
            for file_info in multi_file_project["files"]
        ]
        multi_file_project_obj = MultiFileProject(
            name=multi_file_project["name"],
            description=multi_file_project["description"],
            files=dana_files,
            main_file=multi_file_project["main_file"],
            structure_type=multi_file_project.get("structure_type", "complex"),
        )
    
    return AgentGenerationResponse(
        success=True,
        dana_code=dana_code,
        agent_name=final_agent_name,
        agent_description=final_agent_description,
        capabilities=capabilities,
        auto_stored_files=stored_files if stored_files else None,
        multi_file_project=multi_file_project_obj,
        agent_id=agent_id,
        agent_folder=agent_folder,
        phase="code_generated",
        ready_for_code_generation=True,
        error=None
    )


async def _extract_agent_requirements(messages: list[dict]) -> dict:
    """
    Extract agent requirements from conversation messages using LLM for better alignment
    """
    logger = logging.getLogger(__name__)
    
    # Default requirements
    requirements = {
        "name": "Custom Agent",
        "description": "A specialized agent for your needs",
        "capabilities": [],
        "knowledge_domains": [],
        "workflows": [],
        "tools": [],
        "is_complete": False
    }
    
    try:
        # Try to use LLM for intelligent extraction
        from dana.common.resource.llm.llm_resource import LLMResource
        from dana.common.types import BaseRequest

        # Create LLM resource
        llm_config = {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 800}
        llm = LLMResource(
            name="agent_requirements_extractor", 
            description="LLM for extracting agent requirements from conversation", 
            config=llm_config
        )

        # Initialize the LLM resource
        await llm.initialize()

        # Check if LLM is available
        if not hasattr(llm, "_is_available") or not llm._is_available:
            logger.warning("LLM resource is not available, falling back to regex extraction")
            raise Exception("LLM not available")

        # Create conversation text
        conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

        # Create prompt for intelligent extraction
        prompt = f"""
You are an expert at analyzing conversations to extract agent requirements. Based on the conversation below, extract the agent name and description that best aligns with what the user wants.

Conversation:
{conversation_text}

Please extract:
1. **Agent Name**: A clear, descriptive name that reflects what the agent does (e.g., "Data Analysis Agent", "Customer Support Bot", "Code Review Assistant")
2. **Agent Description**: A concise description (1-2 sentences) that explains what the agent does and its main purpose

Guidelines:
- The name should be specific and descriptive, not generic like "Custom Agent"
- The description should capture the essence of what the user wants the agent to do
- If the user mentions specific domains, tools, or workflows, include those in the description
- Keep the description focused and actionable
- If the user hasn't provided enough information, use reasonable defaults but make them more specific than "Custom Agent"

Respond in this exact JSON format:
{{
    "name": "Specific Agent Name",
    "description": "Clear description of what the agent does and its purpose"
}}

Only return the JSON, no additional text or explanations.
"""

        # Create request for LLM
        request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})

        result = await llm.query(request)

        if result and result.success:
            # Extract content from response
            response_text = ""
            if hasattr(result, "content") and result.content:
                if isinstance(result.content, dict):
                    if "choices" in result.content:
                        response_text = result.content["choices"][0]["message"]["content"]
                    elif "response" in result.content:
                        response_text = result.content["response"]
                    elif "content" in result.content:
                        response_text = result.content["content"]
                elif isinstance(result.content, str):
                    response_text = result.content

            if response_text:
                # Try to parse JSON response
                try:
                    import json
                    extracted_data = json.loads(response_text.strip())
                    
                    if "name" in extracted_data and extracted_data["name"]:
                        requirements["name"] = extracted_data["name"]
                        logger.info(f"LLM extracted agent name: {requirements['name']}")
                    
                    if "description" in extracted_data and extracted_data["description"]:
                        requirements["description"] = extracted_data["description"]
                        logger.info(f"LLM extracted agent description: {requirements['description']}")
                    
                    logger.info("Successfully extracted agent requirements using LLM")
                    return requirements
                    
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Failed to parse LLM JSON response: {json_error}")
                    logger.debug(f"Raw LLM response: {response_text}")

    except Exception as llm_error:
        logger.warning(f"LLM extraction failed: {llm_error}")

    # Fallback to regex-based extraction
    logger.info("Using fallback regex extraction")
    conversation_text = " ".join([msg["content"] for msg in messages])
    
    # Extract potential agent name
    if "agent" in conversation_text.lower():
        # Look for patterns like "create a [name] agent" or "I need a [name]"
        name_match = re.search(r'(?:create|need|want)\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\s+agent|\s+that|\s+to)', conversation_text, re.IGNORECASE)
        if name_match:
            extracted_name = name_match.group(1).strip().title()
            if extracted_name and extracted_name != "Custom":
                requirements["name"] = extracted_name
    
    # Extract description from user messages
    user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
    if user_messages:
        last_user_message = user_messages[-1]
        if len(last_user_message) > 50:  # Only use if it's substantial
            requirements["description"] = last_user_message[:200] + "..." if len(last_user_message) > 200 else last_user_message
    
    # Simple completeness check
    requirements["is_complete"] = len(conversation_text) > 50  # Basic heuristic
    
    return requirements


async def _generate_intelligent_response(messages: list[dict], agent_requirements: dict, conversation_analysis: dict) -> str:
    """
    Generate an intelligent response message using LLM based on the conversation context.
    """
    logger = logging.getLogger(__name__)
    try:
        # Extract conversation context
        conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])
        
        # Get analysis details
        needs_more_info = conversation_analysis.get("needs_more_info", False)
        analysis_details = conversation_analysis.get("analysis", {})
        
        # Create context for LLM
        context = f"""
Conversation History:
{conversation_text}

Extracted Agent Requirements:
- Name: {agent_requirements.get('name', 'Custom Agent')}
- Description: {agent_requirements.get('description', 'A specialized agent')}
- Capabilities: {', '.join(agent_requirements.get('capabilities', []))}
- Knowledge Domains: {', '.join(agent_requirements.get('knowledge_domains', []))}
- Workflows: {', '.join(agent_requirements.get('workflows', []))}

Analysis Results:
- Needs More Info: {needs_more_info}
- Word Count: {analysis_details.get('word_count', 0)}
- Vague Terms: {analysis_details.get('vague_count', 0)}
- Specific Terms: {analysis_details.get('specific_count', 0)}
"""

        # Try to use LLM to generate intelligent response
        try:
            from dana.common.resource.llm.llm_resource import LLMResource
            from dana.common.types import BaseRequest

            # Create LLM resource
            llm_config = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000}
            llm = LLMResource(
                name="intelligent_response_generator", 
                description="LLM for generating intelligent agent creation responses", 
                config=llm_config
            )

            # Initialize the LLM resource
            await llm.initialize()

            # Check if LLM is available
            if not hasattr(llm, "_is_available") or not llm._is_available:
                logger.warning("LLM resource is not available, falling back to template response")
                raise Exception("LLM not available")

            # Create prompt for intelligent response
            if needs_more_info:
                prompt = f"""
You are an AI assistant helping users create Dana agents. Based on the conversation context below, generate a brief understanding of what the user wants and provide ONE specific follow-up question to gather more information.

Context:
{context}

Requirements:
1. Start with a brief understanding of what the user has described so far, using the extracted agent name "{agent_requirements.get('name', 'Custom Agent')}" and description "{agent_requirements.get('description', 'A specialized agent')}"
2. Acknowledge their request positively and specifically reference their agent concept
3. Ask ONE specific, relevant question to gather missing information
4. Keep the tone friendly and helpful
5. Make the question specific to their domain/use case and the agent they're describing
6. Don't ask generic questions like "What specific area would you like help with?"
7. Use the agent name and description to make the question more personalized

Generate a natural, conversational response that flows well and guides the user to provide more specific details about their {agent_requirements.get('name', 'agent')}.
"""
            else:
                prompt = f"""
You are an AI assistant helping users create Dana agents. Based on the conversation context below, generate a brief summary of what you understand about their agent requirements and confirm that you have enough information to proceed.

Context:
{context}

Requirements:
1. Briefly summarize what you understand about their {agent_requirements.get('name', 'agent')} that {agent_requirements.get('description', 'A specialized agent')}
2. Confirm that you have enough information to generate the agent
3. Mention that they can proceed to generate the code by clicking the "Build Agent" button
4. Keep it concise and positive
5. End with a clear call-to-action about building the agent
6. Use the specific agent name and description to make the response more personalized

Generate a natural, conversational response that encourages them to proceed with code generation for their {agent_requirements.get('name', 'agent')}.
"""

            # Create request for LLM
            request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})

            result = await llm.query(request)

            if result and result.success:
                # Extract content from response
                response_text = ""
                if hasattr(result, "content") and result.content:
                    if isinstance(result.content, dict):
                        if "choices" in result.content:
                            response_text = result.content["choices"][0]["message"]["content"]
                        elif "response" in result.content:
                            response_text = result.content["response"]
                        elif "content" in result.content:
                            response_text = result.content["content"]
                    elif isinstance(result.content, str):
                        response_text = result.content

                if response_text:
                    logger.info("Successfully generated intelligent response using LLM")
                    return response_text.strip()

        except Exception as llm_error:
            logger.warning(f"LLM response generation failed: {llm_error}")

        # Fallback to template-based response
        return _generate_fallback_response(agent_requirements, needs_more_info, analysis_details)

    except Exception as e:
        logger.error(f"Error generating intelligent response: {e}")
        return _generate_fallback_response(agent_requirements, True, {})


def _generate_fallback_response(agent_requirements: dict, needs_more_info: bool, analysis_details: dict) -> str:
    """
    Generate a fallback response when LLM is not available.
    """
    agent_name = agent_requirements.get('name', 'Custom Agent')
    agent_description = agent_requirements.get('description', 'A specialized agent')
    
    if needs_more_info:
        word_count = analysis_details.get('word_count', 0)
        if word_count < 10:
            return f"I understand you want to create a {agent_name}. To make this agent truly useful for you, could you tell me more about what specific tasks it should help you with?"
        else:
            return f"Thanks for sharing your idea for a {agent_name}! I can see you want {agent_description}. To create the best possible agent for your needs, could you provide a bit more detail about the specific workflows, data sources, or tools it should work with?"
    else:
        return f"Perfect! I understand you want to create a {agent_name} that {agent_description}. I have enough information to generate your agent code. You can now proceed to build the agent by clicking the 'Build Agent' button."


def _extract_agent_info_from_code(dana_code: str, logger: logging.Logger) -> tuple[str | None, str | None]:
    """
    Extract agent name and description from generated Dana code
    """
    agent_name = None
    agent_description = None

    lines = dana_code.split("\n")
    for i, line in enumerate(lines):
        # Look for agent keyword syntax: agent AgentName:
        if line.strip().startswith("agent ") and line.strip().endswith(":"):
            # Next few lines should contain name and description
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if "name : str =" in next_line:
                    agent_name = next_line.split("=")[1].strip().strip('"')
                    logger.info(f"Extracted agent name: {agent_name}")
                elif "description : str =" in next_line:
                    agent_description = next_line.split("=")[1].strip().strip('"')
                    logger.info(f"Extracted agent description: {agent_description}")
                elif next_line.startswith("#"):  # Skip comments
                    continue
                elif next_line == "":  # Skip empty lines
                    continue
                elif not next_line.startswith("    "):  # Stop at non-indented lines
                    break
            break
        # Fallback: also check for old system: syntax
        elif "system:agent_name" in line:
            agent_name = line.split("=")[1].strip().strip('"')
            logger.info(f"Extracted agent name (old format): {agent_name}")
        elif "system:agent_description" in line:
            agent_description = line.split("=")[1].strip().strip('"')
            logger.info(f"Extracted agent description (old format): {agent_description}")

    return agent_name, agent_description


def _extract_agent_paths_from_files(auto_stored_files: list[str], logger: logging.Logger) -> tuple[int | None, str | None]:
    """
    Extract agent_id and agent_folder from auto-stored files
    """
    agent_id = None
    agent_folder = None

    if auto_stored_files:
        logger.info(f"Auto-stored files: {auto_stored_files}")

        # Look for metadata.json file
        metadata_file_path = None
        for f in auto_stored_files:
            if f.endswith("metadata.json") and os.path.exists(f):
                metadata_file_path = f
                break

        if metadata_file_path:
            try:
                logger.info(f"Reading metadata from: {metadata_file_path}")
                with open(metadata_file_path, "r", encoding="utf-8") as meta_f:
                    meta = json.load(meta_f)
                    agent_folder = meta.get("folder_path")
                    agent_id = meta.get("agent_id")

                    logger.info(f"Extracted from metadata - agent_folder: {agent_folder}, agent_id: {agent_id}")

                    # If no agent_id in metadata, try to extract from folder path pattern
                    if not agent_id and agent_folder:
                        # Try pattern for deployed agents: agent_123_name
                        m = re.search(r"agent_(\d+)_", str(agent_folder))
                        if m:
                            agent_id = int(m.group(1))
                            logger.info(f"Extracted agent_id from folder pattern: {agent_id}")

            except Exception as e:
                logger.error(f"Failed to parse metadata.json at {metadata_file_path}: {e}")
        else:
            # Fallback: try to get folder from the first non-metadata file
            for f in auto_stored_files:
                if not f.endswith("metadata.json") and os.path.exists(f):
                    # Get the parent directory of the file
                    file_path = Path(f)
                    agent_folder = str(file_path.parent)
                    logger.info(f"Fallback: extracted agent_folder from file path: {agent_folder}")
                    break

    # Ensure agent_folder is an absolute path
    if agent_folder and not os.path.isabs(agent_folder):
        agent_folder = str(Path.cwd() / agent_folder)
        logger.info(f"Converted to absolute path: {agent_folder}")

    return agent_id, agent_folder


@router.post("/describe", response_model=AgentDescriptionResponse)
async def describe_agent(request: AgentDescriptionRequest, db: Session = Depends(db.get_db)):
    """
    Phase 1 specific endpoint for agent description refinement.
    
    This endpoint focuses on understanding user requirements and refining
    the agent description without generating code.
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received agent description request with {len(request.messages)} messages")
        
        # Use AgentManager for consistent handling
        from ..agent_manager import get_agent_manager
        agent_manager = get_agent_manager()
        
        # Convert messages to the format expected by AgentManager
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Create agent description using AgentManager
        result = await agent_manager.create_agent_description(
            messages=messages_dict,
            agent_id=request.agent_id,
            existing_agent_data=request.agent_data
        )
        
        # Convert to AgentDescriptionResponse
        return AgentDescriptionResponse(
            success=result["success"],
            agent_id=result["agent_id"] or 0,
            agent_name=result["agent_name"],
            agent_description=result["agent_description"],
            capabilities=result["capabilities"],
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


@router.post("/{agent_id}/generate-code", response_model=AgentGenerationResponse)
async def generate_agent_code(agent_id: int, request: AgentCodeGenerationRequest, db: Session = Depends(db.get_db)):
    """
    Phase 2 specific endpoint for generating code from existing agent description.
    
    This endpoint takes an existing agent description and generates the actual .na files.
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received code generation request for agent {agent_id}")
        
        # Get existing agent
        agent = services.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if agent.generation_phase != "description":
            raise HTTPException(status_code=400, detail="Agent must be in description phase before code generation")
        
        # Convert to AgentGenerationRequest format for reuse
        generation_request = AgentGenerationRequest(
            messages=[],  # Will use stored conversation context
            phase="code_generation",
            agent_id=agent_id,
            multi_file=request.multi_file
        )
        
        # Use the Phase 2 logic
        return await _handle_phase_2_generation(generation_request, [], db, logger)
        
    except Exception as e:
        logger.error(f"Error in generate_agent_code endpoint: {e}", exc_info=True)
        return AgentGenerationResponse(
            success=False,
            dana_code="",
            error=f"Failed to generate agent code: {str(e)}"
        )


@router.post("/{agent_id}/update-description", response_model=AgentDescriptionResponse)
async def update_agent_description(
    agent_id: int, 
    request: AgentDescriptionRequest, 
    db: Session = Depends(db.get_db)
):
    """
    Update agent description during Phase 1.
    
    This endpoint allows updating the agent description and conversation context
    during the description refinement phase.
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received description update request for agent {agent_id}")
        
        # Get existing agent
        agent = services.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if agent.generation_phase != "description":
            raise HTTPException(status_code=400, detail="Can only update description in description phase")
        
        # Convert to AgentGenerationRequest format for reuse
        generation_request = AgentGenerationRequest(
            messages=request.messages,
            phase="description",
            agent_id=agent_id
        )
        
        # Use the Phase 1 logic
        response = await _handle_phase_1_generation(generation_request, 
            [{"role": msg.role, "content": msg.content} for msg in request.messages], 
            db)
        
        # Convert to AgentDescriptionResponse
        return AgentDescriptionResponse(
            success=response.success,
            agent_id=response.agent_id or agent_id,
            agent_name=response.agent_name,
            agent_description=response.agent_description,
            capabilities=response.capabilities,
            follow_up_message=response.follow_up_message,
            suggested_questions=response.suggested_questions,
            ready_for_code_generation=response.ready_for_code_generation,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Error in update_agent_description endpoint: {e}", exc_info=True)
        return AgentDescriptionResponse(
            success=False,
            agent_id=agent_id,
            error=f"Failed to update agent description: {str(e)}"
        )


@router.post("/syntax-check", response_model=DanaSyntaxCheckResponse)
def syntax_check(request: DanaSyntaxCheckRequest):
    """
    Check the syntax of Dana code using DanaSandbox.eval.
    Returns success status and error message if any.
    """
    try:
        result = DanaSandbox.quick_eval(request.dana_code)
        if result.success:
            return DanaSyntaxCheckResponse(success=True, output=result.output)
        else:
            return DanaSyntaxCheckResponse(success=False, error=str(result.error), output=result.output)
    except Exception as e:
        return DanaSyntaxCheckResponse(success=False, error=str(e))


@router.post("/validate", response_model=CodeValidationResponse)
async def validate_code(request: CodeValidationRequest):
    """
    Validate Dana agent code and provide detailed feedback.
    Supports both single-file and multi-file validation.
    Returns validation status, errors, warnings, and suggestions.
    """

    logger = logging.getLogger(__name__)

    try:
        # Handle multi-file validation
        if request.multi_file_project:
            print("validate multi file project")
            logger.info(f"Validating multi-file project: {request.multi_file_project.name}")

            # Create temporary directory for multi-file validation
            temp_dir = tempfile.mkdtemp(prefix=f"dana_validation_{request.multi_file_project.name.replace(' ', '_')}_")
            print("temp_dir", temp_dir)

            try:
                # Set DANA_PATH to the temporary directory
                original_dana_path = os.environ.get("DANA_PATH")
                os.environ["DANA_PATH"] = temp_dir

                # Write all files to temporary directory
                for dana_file in request.multi_file_project.files:
                    file_path = Path(temp_dir) / dana_file.filename
                    logger.info(f"Writing file for validation: {file_path}")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(dana_file.content)

                # Run validation on the main file
                main_file_path = Path(temp_dir) / request.multi_file_project.main_file
                logger.info(f"Validating main file: {main_file_path}")

                with open(main_file_path, encoding="utf-8") as f:
                    main_file_content = f.read()

                # Basic syntax validation using DanaSandbox
                syntax_result = DanaSandbox.quick_eval(main_file_content)

                errors = []
                warnings = []
                suggestions = []

                if not syntax_result.success:
                    error_text = str(syntax_result.error)
                    errors.append({"line": 1, "column": 1, "message": error_text, "severity": "error", "code": error_text})

                # Call the multi-file validation function
                multi_file_result = await validate_multi_file_project(request.multi_file_project)

                # Combine results
                is_valid = len(errors) == 0 and multi_file_result.get("success", False)

                return CodeValidationResponse(
                    success=True,
                    is_valid=is_valid,
                    errors=errors,
                    warnings=warnings,
                    suggestions=suggestions,
                    file_results=multi_file_result.get("file_results", []),
                    dependency_errors=multi_file_result.get("dependency_errors", []),
                    overall_errors=multi_file_result.get("overall_errors", []),
                )

            finally:
                # Restore original DANA_PATH
                if original_dana_path is not None:
                    os.environ["DANA_PATH"] = original_dana_path
                elif "DANA_PATH" in os.environ:
                    del os.environ["DANA_PATH"]

                # Clean up temporary directory
                import shutil

                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary directory {temp_dir}: {cleanup_error}")

        # Handle single-file validation (backward compatibility)
        elif request.code:
            logger.info(f"Validating single-file code for agent: {request.agent_name}")

            # Basic syntax validation
            syntax_result = DanaSandbox.quick_eval(request.code)

            errors = []
            warnings = []
            suggestions = []

            if not syntax_result.success:
                error_text = str(syntax_result.error)
                errors.append({"line": 1, "column": 1, "message": error_text, "severity": "error", "code": error_text})

            # Check for common issues and provide suggestions
            lines = request.code.split("\n")
            for i, line in enumerate(lines, 1):
                stripped_line = line.strip()

                # Check for missing agent definition
                if i == 1 and not stripped_line.startswith("agent ") and not stripped_line.startswith("system:"):
                    suggestions.append(
                        {
                            "type": "syntax",
                            "message": "Consider adding an agent definition",
                            "code": 'agent MyAgent:\n    name: str = "My Agent"\n    description: str = "A custom agent"',
                            "description": "Add a proper agent definition at the beginning of your code",
                        }
                    )

                # Check for missing solve function
                if "def solve(" in stripped_line:
                    break
            else:
                suggestions.append(
                    {
                        "type": "best_practice",
                        "message": "Consider adding a solve function",
                        "code": 'def solve(query: str) -> str:\n    return reason(f"Process query: {query}")',
                        "description": "Add a solve function to make your agent functional",
                    }
                )

            # Check for proper imports
            if "reason(" in request.code and "import" not in request.code:
                suggestions.append(
                    {
                        "type": "syntax",
                        "message": "Consider importing required modules",
                        "code": "# Add imports if needed\n# import some_module",
                        "description": "Make sure all required modules are imported",
                    }
                )

            is_valid = len(errors) == 0
            logger.info(f"Single-file validation result: is_valid={is_valid}, errors={len(errors)}")

            return CodeValidationResponse(success=True, is_valid=is_valid, errors=errors, warnings=warnings, suggestions=suggestions)

        else:
            # Neither code nor multi_file_project provided
            return CodeValidationResponse(
                success=False,
                is_valid=False,
                errors=[
                    {
                        "line": 1,
                        "column": 1,
                        "message": "Either 'code' or 'multi_file_project' must be provided",
                        "severity": "error",
                        "code": "",
                    }
                ],
                warnings=[],
                suggestions=[],
            )

    except Exception as e:
        logger.error(f"Error in validate_code endpoint: {e}", exc_info=True)
        return CodeValidationResponse(
            success=False,
            is_valid=False,
            errors=[{"line": 1, "column": 1, "message": f"Validation failed: {str(e)}", "severity": "error", "code": ""}],
            warnings=[],
            suggestions=[],
        )


@router.post("/fix", response_model=CodeFixResponse)
async def fix_code(request: CodeFixRequest):
    """
    Automatically fix Dana code issues using iterative LLM approach.
    Returns fixed code and list of applied fixes.
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Fixing code for agent: {request.agent_name}")

        # Prepare initial error messages
        error_messages = "\n".join([f"- {error.message}" for error in request.errors])

        # Iterative fix with feedback
        max_attempts = 4
        current_code = request.code
        applied_fixes = []
        attempt_history = []

        for attempt in range(max_attempts):
            logger.info(f"LLM fix attempt {attempt + 1}/{max_attempts}")

            # Build prompt with attempt history
            prompt = _build_iterative_prompt(
                original_code=request.code,
                current_code=current_code,
                error_messages=error_messages,
                attempt_history=attempt_history,
                attempt_number=attempt + 1,
                max_attempts=max_attempts,
            )

            # Use LLM to fix the code
            try:
                from dana.common.resource.llm.llm_configuration_manager import LLMConfigurationManager
                from dana.common.resource.llm.llm_resource import LLMResource
                from dana.common.types import BaseRequest

                # Initialize LLM resource
                llm_config = LLMConfigurationManager().get_model_config()
                llm_resource = LLMResource(name="code_fix_llm", description="LLM for fixing Dana code errors", config=llm_config)

                # Create request for LLM
                request_data = BaseRequest(
                    arguments={
                        "messages": [{"role": "user", "content": prompt}],
                        "system_messages": [
                            "You are an expert Dana programming language developer.",
                            "Your task is to fix syntax errors in Dana code iteratively.",
                            "Return ONLY the corrected code, no explanations or markdown formatting.",
                            "Learn from previous attempts and feedback to improve your fixes.",
                        ],
                    }
                )

                # Get LLM response
                response = await llm_resource.query(request_data)

                if response.success and response.content:
                    # Extract the fixed code from response
                    fixed_code = _extract_code_from_response(response.content)

                    if fixed_code and fixed_code.strip():
                        # Validate the fixed code
                        syntax_result = DanaSandbox.quick_eval(fixed_code)

                        if syntax_result.success:
                            # Success! Code is valid
                            applied_fixes.append(f"LLM applied intelligent fixes (attempt {attempt + 1})")
                            return CodeFixResponse(success=True, fixed_code=fixed_code, applied_fixes=applied_fixes, remaining_errors=[])
                        else:
                            # Still has errors, add to history for next attempt
                            attempt_history.append(
                                {
                                    "attempt": attempt + 1,
                                    "code": fixed_code,
                                    "errors": str(syntax_result.error),
                                    "feedback": f"Attempt {attempt + 1} still has errors: {syntax_result.error}",
                                }
                            )
                            current_code = fixed_code
                            logger.info(f"Attempt {attempt + 1} failed, trying again with feedback")
                    else:
                        # Empty response, add to history
                        attempt_history.append(
                            {
                                "attempt": attempt + 1,
                                "code": current_code,
                                "errors": "LLM returned empty response",
                                "feedback": "LLM returned empty or invalid response",
                            }
                        )
                else:
                    # LLM failed, add to history
                    attempt_history.append(
                        {
                            "attempt": attempt + 1,
                            "code": current_code,
                            "errors": f"LLM failed: {response.error if hasattr(response, 'error') else 'Unknown error'}",
                            "feedback": "LLM request failed",
                        }
                    )

            except Exception as llm_error:
                logger.error(f"LLM fix attempt {attempt + 1} failed: {llm_error}")
                attempt_history.append(
                    {"attempt": attempt + 1, "code": current_code, "errors": str(llm_error), "feedback": f"LLM exception: {llm_error}"}
                )

        # All LLM attempts failed, fall back to rule-based fixes
        logger.warning("All LLM attempts failed, falling back to rule-based fixes")
        return await _apply_rule_based_fixes(request)

    except Exception as e:
        logger.error(f"Error in fix_code endpoint: {e}", exc_info=True)
        return CodeFixResponse(
            success=False,
            fixed_code=request.code,
            applied_fixes=[],
            remaining_errors=[{"line": 1, "column": 1, "message": f"Auto-fix failed: {str(e)}", "severity": "error", "code": ""}],
        )


def _build_iterative_prompt(
    original_code: str, current_code: str, error_messages: str, attempt_history: list, attempt_number: int, max_attempts: int
) -> str:
    """Build an iterative prompt that includes feedback from previous attempts."""

    # Reference Dana code examples
    reference_examples = """
REFERENCE DANA CODE EXAMPLES:

1. Basic Agent Structure:
```
agent WeatherAgent:
    name: str = "Weather Agent"
    description: str = "An agent that provides weather information"

def solve(query: str) -> str:
    return reason(f"Provide weather information for: {query}")
```

2. Agent with Variables:
```
agent CalculatorAgent:
    name: str = "Calculator Agent"
    description: str = "An agent that performs calculations"
    
    private:result = 0

def solve(query: str) -> str:
    private:calculation = reason(f"Calculate: {query}")
    return f"Result: {calculation}"
```

3. Agent with Imports:
```
# Import required modules
from dana.core.lang import reason
from dana.common.resource.llm import LLMResource

agent DataAnalyzer:
    name: str = "Data Analyzer"
    description: str = "An agent that analyzes data"

def solve(query: str) -> str:
    return reason(f"Analyze this data: {query}")
```

4. Agent with Functions:
```
agent TaskManager:
    name: str = "Task Manager"
    description: str = "An agent that manages tasks"
    
    private:task_list = []

def add_task(task: str):
    private:task_list.append(task)
    return f"Added task: {task}"

def solve(query: str) -> str:
    return reason(f"Manage tasks: {query}")
```

5. Agent with Error Handling:
```
agent SafeAgent:
    name: str = "Safe Agent"
    description: str = "An agent with error handling"
    
    private:error_count = 0

def solve(query: str) -> str:
    try:
        return reason(f"Process safely: {query}")
    except Exception as e:
        private:error_count += 1
        return f"Error occurred: {e}"
```

COMMON DANA SYNTAX RULES:
- Use `agent Name:` for agent definitions
- Use `name: str = "value"` for string variables
- Use `private:variable` for private variables
- Use `def function_name():` for function definitions
- Use proper indentation (4 spaces)
- Use `return` statements in functions
- Use `reason()` for AI reasoning
- Import modules with `from module import item`
- Use `try/except` for error handling
- Use `f"string {variable}"` for f-strings

COMMON ERROR PATTERNS AND FIXES:
- "No terminal matches" → Check for unclosed quotes, missing colons, or invalid syntax
- "expected ':'" → Add missing colon after function/class definitions
- "indentation" → Fix indentation (use 4 spaces, not tabs)
- "name 'reason' is not defined" → Add import: `from dana.core.lang import reason`
- "unexpected EOF" → Check for unclosed parentheses, brackets, or quotes
- "invalid syntax" → Check for missing colons, incorrect indentation, or malformed expressions
"""

    prompt = f"""You are an expert Dana programming language developer. Fix the following Dana code that has syntax errors.

{reference_examples}

ORIGINAL CODE:
```
{original_code}
```

CURRENT CODE (after {attempt_number - 1} previous attempts):
```
{current_code}
```

ORIGINAL ERRORS:
{error_messages}

ATTEMPT HISTORY:"""

    if attempt_history:
        for attempt in attempt_history:
            prompt += f"""

Attempt {attempt["attempt"]}:
- Code: {attempt["code"][:200]}{"..." if len(attempt["code"]) > 200 else ""}
- Errors: {attempt["errors"]}
- Feedback: {attempt["feedback"]}"""
    else:
        prompt += "\nNo previous attempts."

    prompt += f"""

CURRENT ATTEMPT ({attempt_number}/{max_attempts}):
Learn from the previous attempts and feedback above. Focus on:
1. Understanding why previous attempts failed
2. Addressing the specific error patterns shown
3. Making incremental improvements
4. Ensuring proper Dana syntax and structure

Return ONLY the corrected Dana code, no explanations:"""

    return prompt


def _extract_code_from_response(content) -> str:
    """Extract code from LLM response, handling various formats."""
    if isinstance(content, dict):
        if "choices" in content and content["choices"]:
            fixed_code = content["choices"][0]["message"]["content"]
        else:
            fixed_code = str(content)
    else:
        fixed_code = str(content)

    # Clean up the response (remove markdown if present)
    if "```" in fixed_code:
        # Extract code from markdown blocks
        start = fixed_code.find("```")
        if start != -1:
            start = fixed_code.find("\n", start) + 1
            end = fixed_code.find("```", start)
            if end != -1:
                fixed_code = fixed_code[start:end].strip()

    return fixed_code.strip()


async def _apply_rule_based_fixes(request: CodeFixRequest) -> CodeFixResponse:
    """Fallback rule-based fixes when LLM is not available"""
    fixed_code = request.code
    applied_fixes = []
    remaining_errors = []

    # Apply fixes based on error types
    for error in request.errors:
        error_msg = error.message.lower()

        # Fix unclosed strings
        if "no terminal matches" in error_msg and "in the current parser context" in error_msg:
            # Try to fix common string issues
            if '"' in fixed_code and fixed_code.count('"') % 2 != 0:
                # Add missing quote at the end
                fixed_code += '"'
                applied_fixes.append("Fixed unclosed string - added missing quote")
            elif "'" in fixed_code and fixed_code.count("'") % 2 != 0:
                # Add missing single quote at the end
                fixed_code += "'"
                applied_fixes.append("Fixed unclosed string - added missing single quote")

        # Fix missing agent definition
        elif "agent" in error_msg and "definition" in error_msg:
            if not fixed_code.strip().startswith("agent "):
                agent_name = request.agent_name or "CustomAgent"
                agent_def = f"""agent {agent_name}:
    name: str = "{agent_name}"
    description: str = "{request.description or "A custom agent"}"

"""
                fixed_code = agent_def + fixed_code
                applied_fixes.append("Added agent definition")

        # Fix missing solve function
        elif "solve" in error_msg and "function" in error_msg:
            if "def solve(" not in fixed_code:
                solve_func = """

def solve(query: str) -> str:
    return reason(f"Process query: {query}")
"""
                fixed_code += solve_func
                applied_fixes.append("Added solve function")

        # Fix missing imports
        elif "import" in error_msg:
            if "import" not in fixed_code:
                imports = """# Add required imports
# import some_module

"""
                fixed_code = imports + fixed_code
                applied_fixes.append("Added import section")

        # Fix indentation issues
        elif "indentation" in error_msg or "expected an indented block" in error_msg:
            # Add basic indentation fix
            lines = fixed_code.split("\n")
            fixed_lines = []
            for line in lines:
                if line.strip() and not line.startswith(" ") and ":" in line:
                    # This line should be indented
                    fixed_lines.append("    " + line)
                else:
                    fixed_lines.append(line)
            fixed_code = "\n".join(fixed_lines)
            applied_fixes.append("Fixed indentation issues")

        # Fix missing colons
        elif "expected ':'" in error_msg:
            lines = fixed_code.split("\n")
            fixed_lines = []
            for line in lines:
                if line.strip() and not line.endswith(":") and ("def " in line or "if " in line or "for " in line or "while " in line):
                    fixed_lines.append(line + ":")
                else:
                    fixed_lines.append(line)
            fixed_code = "\n".join(fixed_lines)
            applied_fixes.append("Added missing colons")

        # Fix undefined variables
        elif "name" in error_msg and "is not defined" in error_msg:
            # Add basic imports for common functions
            if "reason(" in fixed_code and "import" not in fixed_code:
                imports = """# Import required functions
from dana.core.lang import reason

"""
                fixed_code = imports + fixed_code
                applied_fixes.append("Added missing imports for undefined functions")

        else:
            # Keep track of errors that couldn't be fixed
            remaining_errors.append(error)

    # Validate the fixed code
    syntax_result = DanaSandbox.quick_eval(fixed_code)
    if not syntax_result.success:
        remaining_errors.append(
            {"line": 1, "column": 1, "message": f"Fixed code still has errors: {syntax_result.error}", "severity": "error", "code": ""}
        )

    return CodeFixResponse(
        success=len(remaining_errors) == 0, fixed_code=fixed_code, applied_fixes=applied_fixes, remaining_errors=remaining_errors
    )


@router.post("/write-files")
async def write_multi_file_project(project: MultiFileProject):
    """
    Write multi-file Dana project to temporary directory and return as ZIP.

    Args:
        project: MultiFileProject containing files to write

    Returns:
        ZIP file containing all project files
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Creating ZIP for project: {project.name}")

        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add each file to the ZIP
            for dana_file in project.files:
                logger.info(f"Adding file to ZIP: {dana_file.filename}")
                zip_file.writestr(dana_file.filename, dana_file.content)

            # Add project metadata
            metadata = f"""# {project.name}

{project.description}

## Project Structure
Structure Type: {project.structure_type}
Main File: {project.main_file}

## Files
"""
            for dana_file in project.files:
                metadata += f"- **{dana_file.filename}** ({dana_file.file_type}): {dana_file.description or 'Dana code file'}\n"
                if dana_file.dependencies:
                    metadata += f"  Dependencies: {', '.join(dana_file.dependencies)}\n"

            zip_file.writestr("README.md", metadata)
            logger.info("Added README.md to ZIP")

        zip_buffer.seek(0)

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={project.name.replace(' ', '_')}.zip"},
        )

    except Exception as e:
        logger.error(f"Error creating ZIP file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project files: {str(e)}")


@router.post("/write-files-temp")
async def write_multi_file_project_temp(project: MultiFileProject):
    """
    Write multi-file Dana project to temporary directory and return paths.

    Args:
        project: MultiFileProject containing files to write

    Returns:
        Dictionary with temporary directory path and file paths
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Creating temporary directory for project: {project.name}")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"dana_project_{project.name.replace(' ', '_')}_")
        file_paths = []

        # Write each file
        for dana_file in project.files:
            file_path = Path(temp_dir) / dana_file.filename
            logger.info(f"Writing file: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(dana_file.content)
            file_paths.append(str(file_path))

        # Write project metadata
        metadata_path = Path(temp_dir) / "README.md"
        metadata = f"""# {project.name}

{project.description}

## Project Structure
Structure Type: {project.structure_type}
Main File: {project.main_file}

## Files
"""
        for dana_file in project.files:
            metadata += f"- **{dana_file.filename}** ({dana_file.file_type}): {dana_file.description or 'Dana code file'}\n"
            if dana_file.dependencies:
                metadata += f"  Dependencies: {', '.join(dana_file.dependencies)}\n"

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(metadata)

        logger.info(f"Project written to: {temp_dir}")

        return {
            "success": True,
            "temp_directory": temp_dir,
            "file_paths": file_paths,
            "metadata_path": str(metadata_path),
            "main_file_path": str(Path(temp_dir) / project.main_file),
        }

    except Exception as e:
        logger.error(f"Error writing temporary files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to write project files: {str(e)}")


@router.post("/validate-multi-file")
async def validate_multi_file_project(project: MultiFileProject):
    """
    Validate all files in a multi-file Dana project.

    Args:
        project: MultiFileProject containing files to validate

    Returns:
        Dictionary with validation results for each file
    """

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Validating multi-file project: {project.name}")

        validation_results = {
            "success": True,
            "project_name": project.name,
            "file_results": [],
            "dependency_errors": [],
            "overall_errors": [],
        }

        # Validate each file individually
        for dana_file in project.files:
            logger.info(f"Validating file: {dana_file.filename}")

            file_result = {
                "filename": dana_file.filename,
                "file_type": dana_file.file_type,
                "success": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
            }

            try:
                # Use Dana sandbox to validate syntax
                syntax_result = DanaSandbox.quick_eval(dana_file.content)

                if not syntax_result.success:
                    file_result["success"] = False
                    file_result["errors"].append(
                        {"line": 1, "column": 1, "message": f"Syntax error: {syntax_result.error}", "severity": "error", "code": ""}
                    )
                    validation_results["success"] = False
                    logger.error(f"Syntax error in {dana_file.filename}: {syntax_result.error}")
                else:
                    logger.info(f"Syntax validation passed for {dana_file.filename}")

                # Check for file-specific patterns
                content = dana_file.content

                # Check for missing imports
                if "import" in content and not any(
                    line.strip().startswith("import") or line.strip().startswith("from") for line in content.split("\n")
                ):
                    file_result["warnings"].append(
                        {
                            "line": 1,
                            "column": 1,
                            "message": "File may be missing import statements",
                            "suggestion": "Add required imports at the top of the file",
                        }
                    )

                # Check for dependency consistency
                declared_deps = set(dana_file.dependencies)
                actual_imports = set()

                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("import ") and not line.endswith(".py"):
                        module = line.replace("import ", "").strip()
                        actual_imports.add(module)
                    elif line.startswith("from ") and " import " in line:
                        module = line.split(" import ")[0].replace("from ", "").strip()
                        if not module.endswith(".py"):
                            actual_imports.add(module)

                # Check for missing dependencies
                missing_deps = actual_imports - declared_deps
                if missing_deps:
                    file_result["warnings"].append(
                        {
                            "line": 1,
                            "column": 1,
                            "message": f"Missing dependencies: {', '.join(missing_deps)}",
                            "suggestion": "Update file dependencies in project structure",
                        }
                    )

                # Check for unused dependencies
                unused_deps = declared_deps - actual_imports
                if unused_deps:
                    file_result["warnings"].append(
                        {
                            "line": 1,
                            "column": 1,
                            "message": f"Unused dependencies: {', '.join(unused_deps)}",
                            "suggestion": "Remove unused dependencies from project structure",
                        }
                    )

                # File-type specific validation
                if dana_file.file_type == "agent":
                    # Check for agent definition
                    if "agent " not in content:
                        file_result["errors"].append(
                            {
                                "line": 1,
                                "column": 1,
                                "message": "Agent file must contain an agent definition",
                                "severity": "error",
                                "code": "",
                            }
                        )
                        validation_results["success"] = False

                    # Check for solve function
                    if "def solve(" not in content:
                        file_result["suggestions"].append(
                            {
                                "type": "best_practice",
                                "message": "Agent should have a solve function",
                                "code": 'def solve(problem: str) -> str:\n    return reason(f"Handle: {problem}")',
                                "description": "Add a solve function to make the agent functional",
                            }
                        )

                elif dana_file.file_type == "resources":
                    # Check for resource usage patterns
                    if "use(" not in content:
                        file_result["warnings"].append(
                            {
                                "line": 1,
                                "column": 1,
                                "message": "Resources file should define resource usage",
                                "suggestion": "Add resource definitions using use() function",
                            }
                        )

                elif dana_file.file_type == "workflow":
                    # Check for workflow patterns
                    if "def " not in content:
                        file_result["warnings"].append(
                            {
                                "line": 1,
                                "column": 1,
                                "message": "Workflow file should define workflow functions",
                                "suggestion": "Add workflow function definitions",
                            }
                        )

                elif dana_file.file_type == "methods":
                    # Check for method definitions
                    if "def " not in content:
                        file_result["warnings"].append(
                            {
                                "line": 1,
                                "column": 1,
                                "message": "Methods file should define utility functions",
                                "suggestion": "Add utility function definitions",
                            }
                        )

            except Exception as e:
                logger.error(f"Error validating {dana_file.filename}: {e}")
                file_result["success"] = False
                file_result["errors"].append(
                    {"line": 1, "column": 1, "message": f"Validation error: {str(e)}", "severity": "error", "code": ""}
                )
                validation_results["success"] = False

            validation_results["file_results"].append(file_result)

        # Validate project-level dependencies
        all_filenames = {f.filename.replace(".na", "") for f in project.files}

        for dana_file in project.files:
            for dep in dana_file.dependencies:
                if dep not in all_filenames:
                    validation_results["dependency_errors"].append(
                        {
                            "file": dana_file.filename,
                            "missing_dependency": dep,
                            "message": f"File {dana_file.filename} depends on {dep} but {dep}.na is not in the project",
                        }
                    )
                    validation_results["success"] = False

        # Check for circular dependencies
        def has_circular_deps(filename, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []

            if filename in path:
                return True

            if filename in visited:
                return False

            visited.add(filename)
            path.append(filename)

            # Find file and check its dependencies
            for f in project.files:
                if f.filename.replace(".na", "") == filename:
                    for dep in f.dependencies:
                        if has_circular_deps(dep, visited, path.copy()):
                            return True

            path.pop()
            return False

        for dana_file in project.files:
            filename = dana_file.filename.replace(".na", "")
            if has_circular_deps(filename):
                validation_results["overall_errors"].append(
                    {
                        "type": "circular_dependency",
                        "message": f"Circular dependency detected involving {dana_file.filename}",
                        "file": dana_file.filename,
                    }
                )
                validation_results["success"] = False

        logger.info(f"Validation complete. Success: {validation_results['success']}")
        return validation_results

    except Exception as e:
        logger.error(f"Error validating multi-file project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to validate project: {str(e)}")


# Auto-storage helper functions for agent generation
async def _auto_store_single_file_agent(agent_name: str, agent_description: str, dana_code: str) -> list[str]:
    """
    Auto-store a single-file agent to temporary generation folder.

    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        dana_code: Dana code content

    Returns:
        List of file paths created
    """
    from datetime import datetime

    logger = logging.getLogger(__name__)

    # Create unique folder for this generation
    sanitized_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", agent_name.lower())
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"generated_{sanitized_name}_{unique_id}"

    # Create generation directory if it doesn't exist
    generation_dir = Path("generated")
    generation_dir.mkdir(exist_ok=True)

    # Create agent folder
    agent_folder = generation_dir / folder_name
    agent_folder.mkdir(exist_ok=True)

    file_paths = []

    # Create agent.na file
    agent_file = agent_folder / "agent.na"
    with open(agent_file, "w", encoding="utf-8") as f:
        f.write(dana_code)
    file_paths.append(str(agent_file))
    logger.info(f"Created agent.na file: {agent_file}")

    # Create metadata.json
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": ["agent.na"],
        "folder_path": str(agent_folder.resolve()),  # Store absolute path
        "generation_type": "single_file",
        "temporary": True,
    }

    metadata_file = agent_folder / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Created metadata.json: {metadata_file}")

    logger.info(f"Auto-storage completed. Created {len(file_paths)} files: {file_paths}")
    return file_paths


async def _auto_store_multi_file_agent(agent_name: str, agent_description: str, multi_file_project: dict) -> list[str]:
    """
    Auto-store a multi-file agent to temporary generation folder.

    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        multi_file_project: Multi-file project data

    Returns:
        List of file paths created
    """
    from datetime import datetime

    logger = logging.getLogger(__name__)

    # Create unique folder for this generation
    sanitized_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", agent_name.lower())
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"generated_{sanitized_name}_{unique_id}"

    # Create generation directory if it doesn't exist
    generation_dir = Path("generated")
    generation_dir.mkdir(exist_ok=True)

    # Create agent folder
    agent_folder = generation_dir / folder_name
    agent_folder.mkdir(exist_ok=True)
    logger.info(f"Created multi-file agent folder: {agent_folder}")

    # Always create docs folder inside agent folder
    docs_folder = agent_folder / "docs"
    docs_folder.mkdir(exist_ok=True)
    logger.info(f"Ensured docs folder exists: {docs_folder}")

    # Add a temp.txt file in the docs folder with a number
    temp_file = docs_folder / "temp.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("42\n")
    logger.info(f"Created temp.txt in docs folder: {temp_file}")

    file_paths = []

    # Create files from multi-file project
    for file_info in multi_file_project["files"]:
        filename = file_info["filename"]
        if not filename.endswith(".na"):
            filename += ".na"

        file_path = agent_folder / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"])
        file_paths.append(str(file_path))
        logger.info(f"Created file: {file_path}")

    # Create metadata.json
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": [Path(p).name for p in file_paths],
        "folder_path": str(agent_folder.resolve()),  # Store absolute path
        "generation_type": "multi_file",
        "main_file": multi_file_project.get("main_file", "agent.na"),
        "structure_type": multi_file_project.get("structure_type", "modular"),
        "temporary": True,
    }

    metadata_file = agent_folder / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Created metadata.json: {metadata_file}")

    logger.info(f"Multi-file auto-storage completed. Created {len(file_paths)} files: {file_paths}")
    return file_paths


@router.post("/open-agent-folder")
async def open_agent_folder(request: dict):
    """
    Open agent folder in file explorer.
    Accepts either agent_folder (absolute path) or agent_id.
    
    Args:
        request: Dict with either 'agent_folder' or 'agent_id'
    
    Returns:
        Success status
    """
    
    logger = logging.getLogger(__name__)
    
    try:
        agent_folder = request.get("agent_folder")
        agent_id = request.get("agent_id")
        
        if not agent_folder and not agent_id:
            raise HTTPException(status_code=400, detail="Either agent_folder or agent_id must be provided")
        
        # If agent_id provided, try to find the folder
        if agent_id and not agent_folder:
            # Try to find agent folder by ID
            agents_dir = Path("agents")
            generated_dir = Path("generated")
            
            found_folder = None
            
            # Check agents directory first
            if agents_dir.exists():
                for folder in agents_dir.iterdir():
                    if folder.is_dir() and folder.name.startswith(f"agent_{agent_id}_"):
                        found_folder = folder
                        break
            
            # Check generated directory
            if not found_folder and generated_dir.exists():
                for folder in generated_dir.iterdir():
                    if folder.is_dir() and f"_{agent_id}" in folder.name:
                        found_folder = folder
                        break
            
            if found_folder:
                agent_folder = str(found_folder)
            else:
                raise HTTPException(status_code=404, detail=f"Agent folder not found for ID: {agent_id}")
        
        # Validate agent_folder
        if not agent_folder:
            raise HTTPException(status_code=400, detail="agent_folder is required")
        
        # Convert to Path object
        folder_path = Path(agent_folder)
        
        # If relative path, make it absolute
        if not folder_path.is_absolute():
            folder_path = Path.cwd() / folder_path
        
        # Security check - ensure path is within allowed directories
        allowed_dirs = [Path("agents"), Path("generated"), Path("tmp")]
        is_allowed = any(
            str(folder_path.resolve()).startswith(str((Path.cwd() / allowed_dir).resolve())) 
            for allowed_dir in allowed_dirs
        )
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Access to this folder path is not allowed")
        
        # Check if folder exists
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
        
        if not folder_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        # Open folder based on platform
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(folder_path)], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(folder_path)], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Opening folders not supported on {system}")
        
        logger.info(f"Opened agent folder: {folder_path}")
        return {"success": True, "message": f"Opened {folder_path}"}
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open agent folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to open folder")
    except Exception as e:
        logger.error(f"Error opening agent folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-file/{file_path:path}")
async def open_file_location(file_path: str):
    """
    Open file location in Finder/Explorer.

    Args:
        file_path: Encoded file path to open

    Returns:
        Success status
    """

    logger = logging.getLogger(__name__)

    try:
        # Decode the file path
        decoded_path = urllib.parse.unquote(file_path)
        file_path_obj = Path(decoded_path)

        # Security check - ensure path is within allowed directories
        allowed_dirs = [Path("agents"), Path("generated"), Path("tmp")]
        is_allowed = any(str(file_path_obj.resolve()).startswith(str((Path.cwd() / allowed_dir).resolve())) for allowed_dir in allowed_dirs)

        if not is_allowed:
            raise HTTPException(status_code=403, detail="Access to this file path is not allowed")

        # Check if file exists, if not try pattern matching
        if not file_path_obj.exists():
            # Try pattern matching for wildcard paths (e.g., generated_agent*/agent.na)

            if "*" in decoded_path or "?" in decoded_path:
                logger.info(f"File not found, trying pattern matching for: {decoded_path}")
                matches = glob.glob(decoded_path)
                if matches:
                    # Use the first match
                    actual_file_path = matches[0]
                    file_path_obj = Path(actual_file_path)
                    logger.info(f"Pattern matched to: {actual_file_path}")

                    # Re-validate security for the resolved path
                    is_allowed = any(
                        str(file_path_obj.resolve()).startswith(str((Path.cwd() / allowed_dir).resolve())) for allowed_dir in allowed_dirs
                    )
                    if not is_allowed:
                        raise HTTPException(status_code=403, detail="Resolved file path is not allowed")
                else:
                    raise HTTPException(status_code=404, detail=f"No files match pattern: {decoded_path}")
            else:
                raise HTTPException(status_code=404, detail="File not found")

        # Get the directory containing the file
        directory = file_path_obj.parent if file_path_obj.is_file() else file_path_obj

        # Open based on platform
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(directory)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(directory)], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(directory)], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Opening files not supported on {system}")

        logger.info(f"Opened file location: {directory}")
        return {"success": True, "message": f"Opened {directory}"}

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open file location: {e}")
        raise HTTPException(status_code=500, detail="Failed to open file location")
    except Exception as e:
        logger.error(f"Error opening file location: {e}")
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

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Uploading knowledge file: {file.filename}")

        # Use AgentManager for consistent handling
        from ..agent_manager import get_agent_manager
        agent_manager = get_agent_manager()

        # Parse conversation context and agent info
        conv_context = json.loads(conversation_context) if conversation_context else []
        agent_data = json.loads(agent_info) if agent_info else {}
        if not agent_data.get('folder_path'):
            logger.error('Missing folder_path in agent_info for knowledge upload')
            return {"success": False, "error": "Missing folder_path in agent_info. Please complete agent creation before uploading knowledge files."}

        # Read file content
        file_content = await file.read()

        # Upload file using AgentManager
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


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background processing task.
    
    Returns:
        Task status including progress and messages
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return processing_status[task_id]


async def _update_agent_code_with_rag(
    agent_folder: Path,
    agent_data: dict | None = None,
    current_code: str | None = None,
    multi_file_project: dict | None = None
) -> tuple[str | None, dict | None]:
    """
    Update agent code files with RAG integration.
    
    Args:
        agent_folder: Path to the agent's folder
        agent_data: Current agent data
        current_code: Current single-file Dana code
        multi_file_project: Current multi-file project structure
        
    Returns:
        Tuple of (updated_code, updated_multi_file_project)
    """
    import logging
    import json
    from ..code_handler import CodeHandler
    
    logger = logging.getLogger(__name__)
    
    try:
        updated_code = None
        updated_multi_file_project = None
        
        # Handle multi-file project updates
        if multi_file_project:
            logger.info("Updating multi-file project with RAG integration")
            
            # Create a copy of the project
            updated_project = multi_file_project.copy()
            
            # Update knowledges.na to add contextual_knowledge if it doesn't exist
            knowledges_file = None
            for file_info in updated_project.get("files", []):
                if file_info.get("filename") == "knowledges.na":
                    knowledges_file = file_info
                    break
            
            if knowledges_file:
                current_content = knowledges_file.get("content", "")
                
                # Check if contextual_knowledge already exists
                if "contextual_knowledge" not in current_content:
                    # Add contextual_knowledge to existing content while preserving existing knowledge
                    if current_content.strip():
                        # Add to existing content with proper spacing
                        if not current_content.endswith("\n"):
                            current_content += "\n"
                        current_content += "\n# RAG resource for contextual knowledge retrieval from uploaded documents\n"
                        current_content += 'contextual_knowledge = use("rag", sources=["./knows"])'
                    else:
                        # Create new content if file is empty (shouldn't happen but handle gracefully)
                        current_content = '''"""Knowledge base/resource configurations."""

# Original knowledge resource
knowledge = use("rag", sources=["./docs"])

# RAG resource for contextual knowledge retrieval from uploaded documents
contextual_knowledge = use("rag", sources=["./knows"])'''
                    
                    knowledges_file["content"] = current_content
                    logger.info("Added contextual_knowledge to knowledges.na while preserving existing content")
                else:
                    logger.info("contextual_knowledge already exists in knowledges.na")
            
            # Update methods.na file to use contextual knowledge
            methods_file = None
            for file_info in updated_project.get("files", []):
                if file_info.get("filename") == "methods.na":
                    methods_file = file_info
                    break
            
            if methods_file:
                # Add RAG integration to methods
                current_content = methods_file.get("content", "")
                
                # Update imports to include both knowledge sources on separate lines
                if "from knowledges import contextual_knowledge" not in current_content:
                    lines = current_content.split("\n")
                    
                    # Find where to insert imports (after existing imports)
                    insert_index = 0
                    has_knowledge_import = False
                    
                    for i, line in enumerate(lines):
                        if "from knowledges import knowledge" in line:
                            has_knowledge_import = True
                            insert_index = i + 1
                        elif line.strip().startswith("from ") or line.strip().startswith("import "):
                            insert_index = i + 1
                        elif line.strip() and not line.strip().startswith("#"):
                            break
                    
                    # Add knowledge import if it doesn't exist
                    if not has_knowledge_import:
                        lines.insert(insert_index, "from knowledges import knowledge")
                        insert_index += 1
                    
                    # Add contextual_knowledge import
                    lines.insert(insert_index, "from knowledges import contextual_knowledge")
                    current_content = "\n".join(lines)
                
                # Modify existing search_document function to use both knowledge sources
                if "def search_document" in current_content:
                    # Find and replace the existing search_document function
                    import re
                    
                    # Pattern to match the search_document function
                    pattern = r'def search_document\([^)]*\)[^:]*:.*?(?=\n\ndef|\n\n[a-zA-Z]|\Z)'
                    
                    enhanced_search_function = '''def search_document(package: AgentPackage) -> AgentPackage:
    """Search documents using both knowledge sources and combine results."""
    package.retrieval_result = str(knowledge.query(package.query)) + str(contextual_knowledge.query(package.query))
    return package'''
                    
                    # Replace the existing function
                    updated_content = re.sub(pattern, enhanced_search_function, current_content, flags=re.DOTALL)
                    current_content = updated_content
                    logger.info("Modified existing search_document function to use both knowledge sources")
                elif "def search_document" not in current_content:
                    # Add the search_document function if it doesn't exist
                    search_method = '''
def search_document(package: AgentPackage) -> AgentPackage:
    """Search documents using both knowledge sources and combine results."""
    package.retrieval_result = str(knowledge.query(package.query)) + str(contextual_knowledge.query(package.query))
    return package'''
                    
                    current_content += search_method
                    logger.info("Added search_document function with combined knowledge sources")
                
                methods_file["content"] = current_content
                logger.info("Updated methods.na with combined knowledge sources and search function")
            
            # Note: Only modifying methods.na - not touching other .na files like workflows.na
            logger.info("Deep training enhancement complete - only modified methods.na file")
            
            # Write updated files to disk
            await _write_multi_file_project_to_disk(agent_folder, updated_project)
            updated_multi_file_project = updated_project
        
        # Handle single-file code updates (if needed)
        elif current_code:
            logger.info("Updating single-file code with RAG integration")
            # For single file, we could add RAG integration here
            # For now, return the current code as-is since multi-file is preferred
            updated_code = current_code
        
        return updated_code, updated_multi_file_project
        
    except Exception as e:
        logger.error(f"Error updating agent code with RAG: {e}", exc_info=True)
        return None, None


async def _write_multi_file_project_to_disk(agent_folder: Path, project: dict) -> None:
    """Write multi-file project to disk."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        for file_info in project.get("files", []):
            filename = file_info.get("filename")
            content = file_info.get("content", "")
            
            if filename:
                file_path = agent_folder / filename
                file_path.write_text(content, encoding="utf-8")
                logger.info(f"Written {filename} to {file_path}")
                
    except Exception as e:
        logger.error(f"Error writing project files to disk: {e}", exc_info=True)


@router.post("/process-agent-documents", response_model=ProcessAgentDocumentsResponse)
async def process_agent_documents(request: ProcessAgentDocumentsRequest, background_tasks: BackgroundTasks):
    """
    Process uploaded documents with conversation context to enhance agent creation.
    Also updates agent code files with RAG integration.
    
    Args:
        request: Contains document_folder, conversation, summary, agent_data, and current_code
        
    Returns:
        Processing results with updated agent code
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Processing agent documents from: {request.document_folder}")
        
        # Validate document folder exists
        doc_folder = Path(request.document_folder).absolute()
        if not doc_folder.exists() or not doc_folder.is_dir():
            raise HTTPException(status_code=404, detail=f"Document folder not found: {request.document_folder}")
        
        # Get agent folder (parent of docs folder)
        agent_folder = doc_folder.parent
        logger.info(f"Agent folder: {agent_folder}")
        
        # Update agent code files with RAG integration if agent data is provided
        updated_code = None
        updated_multi_file_project = None
        
        if request.agent_data or request.current_code or request.multi_file_project:
            logger.info("Updating agent code with RAG integration...")
            updated_code, updated_multi_file_project = await _update_agent_code_with_rag(
                agent_folder=agent_folder,
                agent_data=request.agent_data,
                current_code=request.current_code,
                multi_file_project=request.multi_file_project
            )
        
        # Process conversation (normalize to list)
        conversation_list = []
        if isinstance(request.conversation, str):
            conversation_list = [request.conversation]
        else:
            conversation_list = request.conversation
        
        # Generate task ID for tracking background document processing
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        processing_status[task_id] = {
            "status": "pending",
            "message": "Starting document processing...",
            "progress": 0
        }
        
        # Start background task for document processing (curate.na workflow)
        import threading

        def run_in_thread():
            import asyncio
            try:
                asyncio.run(_process_documents_with_context(
                    task_id,
                    doc_folder,
                    conversation_list,
                    request.summary
                ))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in threaded document processing: {e}", exc_info=True)

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        
        # Return updated agent code immediately while document processing continues in background
        response_data = {
            "success": True,
            "message": "Agent code updated with RAG integration. Document processing started in background.",
            "processing_details": {
                "task_id": task_id,
                "status_url": f"/agents/task-status/{task_id}",
                "document_folder": str(doc_folder),
                "agent_folder": str(agent_folder)
            }
        }
        
        # Include updated code in response
        if updated_code:
            response_data["dana_code"] = updated_code
        if updated_multi_file_project:
            response_data["multi_file_project"] = updated_multi_file_project
            
        return ProcessAgentDocumentsResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting document processing: {e}", exc_info=True)
        return ProcessAgentDocumentsResponse(
            success=False,
            message=f"Failed to start document processing: {str(e)}",
            processing_details={"error": str(e)}
        )


async def _process_documents_with_context(
    task_id: str,
    doc_folder: Path,
    conversation: list[str],
    summary: str
) -> dict:
    """
    Process documents with conversation context using the curate.na script.
    """
    import logging
    import shutil
    import subprocess
    import re
    from pathlib import Path as PyPath
    
    logger = logging.getLogger(__name__)
    
    # Get list of documents in folder
    documents = []
    for file_path in doc_folder.iterdir():
        if file_path.is_file():
            documents.append(file_path.name)

    print(f"Documents: {documents}")
    
    logger.info(f"Found {len(documents)} documents to process")
    
    # Update task status
    processing_status[task_id] = {
        "status": "processing",
        "message": "Extracting role and topic from conversation...",
        "progress": 20
    }
    
    # Extract role and topic from conversation and summary
    role, topic = await _extract_role_and_topic(conversation, summary)
    logger.info(f"Extracted role: {role}, topic: {topic}")
    
    # Update task status
    processing_status[task_id] = {
        "status": "processing",
        "message": f"Preparing curate script for role: {role}, topic: {topic}",
        "progress": 40
    }
    
    # Use __file__ to find the curate.na path relative to this module
    current_file = PyPath(__file__)
    # Go up from routers/api.py to the project root
    project_root = current_file.parent.parent.parent.parent.parent  # dana/api/server/routers -> project root
    curate_path = project_root / "dana" / "frameworks" / "knows" / "corral" / "curate" / "curate.na"
    
    if not curate_path.exists():
        raise FileNotFoundError(f"curate.na not found at {curate_path}")
    
    curate_content = curate_path.read_text()
    
    # Replace topic and role in the content
    # Find and replace the topic line
    curate_content = re.sub(
        r'^topic = ".*"$',
        f'topic = """{topic}"""',
        curate_content,
        flags=re.MULTILINE
    )
    
    # Find and replace the role line
    curate_content = re.sub(
        r'^role = ".*"$', 
        f'role = "{role}"',
        curate_content,
        flags=re.MULTILINE
    )
    
    # Also update the output folder to use the document folder
    curate_content = re.sub(
        r'^output_folder_name = .*$',
        f'output_folder_name = "{doc_folder.parent.absolute()}/knows"',
        curate_content,
        flags=re.MULTILINE
    )
    
    # Create curate folder at the same level as doc_folder
    curate_target_dir = doc_folder.parent / "curate"
    curate_target_dir.mkdir(exist_ok=True)
    logger.info(f"Created curate directory at: {curate_target_dir}")
    
    # Create a temporary modified curate.na file in the curate folder
    temp_curate_path = curate_target_dir / "curate_modified.na"
    temp_curate_path.write_text(curate_content)
    logger.info(f"Created modified curate.na at {temp_curate_path}")
    
    # Update task status
    processing_status[task_id] = {
        "status": "processing",
        "message": "Copying utility files...",
        "progress": 60
    }
    
    # Copy all .na files from the curate directory to the curate folder
    curate_dir = curate_path.parent  # Get the directory containing curate.na
    
    # Use glob to find all .na files in the curate directory
    import glob
    na_files = glob.glob(str(curate_dir / "*.na"))
    
    for na_file_path in na_files:
        src = PyPath(na_file_path)
        # Skip the main curate.na file since we're creating a modified version
        if src.name == "curate.na":
            continue
            
        dst = curate_target_dir / src.name
        
        # Special handling for senior_agent.na to replace document_folder path
        if src.name == "senior_agent.na":
            content = src.read_text()
            # Replace document_folder assignment with the actual doc_folder path
            content = re.sub(
                r'document_folder\s*=\s*["\'].*?["\']',
                f'document_folder = "{doc_folder}"',
                content
            )
            dst.write_text(content)
            logger.info(f"Modified and copied {src.name} with doc_folder path: {doc_folder}")
        else:
            shutil.copy2(src, dst)
            logger.info(f"Copied {src.name} to curate folder")
    
    # Update task status
    processing_status[task_id] = {
        "status": "processing",
        "message": "Running dana curate script...",
        "progress": 80
    }
    
    # Run the modified curate.na script using subprocess
    try:
        # Set DANAPATH to include the curate folder
        import os
        import subprocess
        env = os.environ.copy()
        env["DANAPATH"] = str(curate_target_dir.absolute())
        
        # Run dana with the modified script
        result = subprocess.run(
            ["dana", str(temp_curate_path.absolute())],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(curate_target_dir.absolute())
        )
        
        if result.returncode != 0:
            logger.error(f"Dana script failed: {result.stderr}")
            processing_status[task_id] = {
                "status": "failed",
                "message": f"Dana script execution failed: {result.stderr}",
                "progress": 0
            }
            raise RuntimeError(f"Dana script execution failed: {result.stderr}")
        
        logger.info(f"Dana script output: {result.stdout}")
        
    except Exception as e:
        logger.error(f"Error running curate.na: {e}")
        processing_status[task_id] = {
            "status": "failed",
            "message": f"Error running curate.na: {str(e)}",
            "progress": 0
        }
        raise
    
    # Extract agent details from the processing
    agent_name = f"{role} Expert"
    agent_description = f"An expert {role} specializing in {topic}"
    
    # Read generated files if any
    processed_folder = doc_folder / "processed"
    generated_files = []
    if processed_folder.exists():
        for file_path in processed_folder.iterdir():
            if file_path.is_file():
                generated_files.append(file_path.name)
    
    processing_results = {
        "documents_processed": len(documents),
        "document_list": documents,
        "conversation_length": len(conversation),
        "summary_provided": summary,
        "agent_name": agent_name,
        "agent_description": agent_description,
        "role": role,
        "topic": topic,
        "generated_files": generated_files,
        "output_folder": str(processed_folder) if processed_folder.exists() else None
    }
    
    # Update task status to completed
    processing_status[task_id] = {
        "status": "completed",
        "message": f"Successfully processed {len(documents)} documents for {agent_name}",
        "progress": 100,
        "result": processing_results
    }
    
    logger.info(f"Processing complete: {processing_results}")
    
    return processing_results


async def _extract_role_and_topic(conversation: list[str], summary: str) -> tuple[str, str]:
    """
    Extract role and topic from conversation and summary using LLM.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Combine conversation and summary for context
    context = "\n".join(conversation) + "\n\nSummary: " + summary
    
    # Use LLMResource to extract role and topic
    extraction_prompt = f"""
You will receive **{context}** — a conversation transcript and its summary.

### Task
1. **ROLE** – Extract the single most relevant professional role the assistant should adopt  
   (e.g., “AML/BSA Compliance Specialist”, “Process Engineer”).

2. **TOPIC** – Extract the full topic the user cares about.  
   • Capture every major facet mentioned (sub-topics, scope notes, timelines, carve-outs, acronyms, etc.).  
   • Separate distinct facets with semicolons “;” to keep the string readable yet complete.  
   • Do not omit any detail that could affect relevance or compliance.

### Output
Return **exactly** this JSON object—no extra text, markdown, or code fencing:

{{
  "role": "<extracted role>",
  "topic": "<extracted topic with all facets; separated by semicolons>"
}}
"""
    
    try:
        from dana.common.resource.llm.llm_resource import LLMResource
        from dana.common.resource.llm.llm_configuration_manager import LLMConfigurationManager
        from dana.common.types import BaseRequest
        
        # Initialize LLM resource
        llm_config = LLMConfigurationManager().get_model_config()
        llm_resource = LLMResource(
            name="role_topic_extractor",
            description="LLM for extracting role and topic",
            config=llm_config
        )
        
        # Create request
        request_data = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing conversations and extracting key information.",
                    },
                    {"role": "user", "content": extraction_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        # Use query_sync for synchronous execution
        response = llm_resource.query_sync(request_data)
        
        if response.success and response.content:
            # Parse the response using Misc.text_to_dict
            from dana.common.utils import Misc
            
            result = Misc.get_response_content(response)
            if isinstance(result, str):
                # Use text_to_dict to parse the JSON
                extracted = Misc.text_to_dict(result)
            else:
                extracted = result
                
            role = extracted.get("role", "Expert")
            topic = extracted.get("topic", "General Knowledge Processing")
            
            logger.info(f"Extracted role: {role}, topic: {topic}")
            return role, topic
        else:
            raise Exception(f"LLM query failed: {response.error if hasattr(response, 'error') else 'Unknown error'}")
        
    except Exception as e:
        logger.warning(f"Failed to extract role and topic using LLM: {e}")
        # Fallback extraction from summary
        role = "Expert"
        topic = summary[:100] if len(summary) > 100 else summary
        
        # Simple heuristic extraction
        if "engineer" in summary.lower():
            role = "Engineer"
        elif "scientist" in summary.lower():
            role = "Scientist"
        elif "analyst" in summary.lower():
            role = "Analyst"
        elif "developer" in summary.lower():
            role = "Developer"
            
        return role, topic


async def _update_tools_with_rag(agent_folder_path: Path):
    """
    Ensure tools.na contains a single rag_resource = use("rag", sources=["./docs"]) declaration.
    Idempotent: only adds if not present.
    """

    logger = logging.getLogger(__name__)

    try:
        tools_file = agent_folder_path / "tools.na"
        rag_declaration = 'rag_resource = use("rag", sources=["./docs"])'  # No trailing newline
        # Read existing tools.na content
        if tools_file.exists():
            with open(tools_file, "r", encoding="utf-8") as f:
                content = f.read()
            if rag_declaration not in content:
                # Remove any old rag_resource lines

                content = re.sub(r"^.*rag_resource\s*=.*$", "", content, flags=re.MULTILINE)
                # Add the correct rag_resource at the end
                if not content.endswith("\n"):
                    content += "\n"
                content += rag_declaration + "\n"
                with open(tools_file, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Updated tools.na with RAG resource for ./docs")
            else:
                logger.info(f"tools.na already contains correct RAG resource")
        else:
            with open(tools_file, "w", encoding="utf-8") as f:
                f.write(rag_declaration + "\n")
            logger.info(f"Created tools.na with RAG resource for ./docs")
    except Exception as e:
        logger.error(f"Error updating tools.na with RAG: {e}")


async def process_knowledge_in_background(task_id: str, agent_folder_path: Path, filename: str):
    """
    Background task to process uploaded knowledge files.
    This is where you can add your long preprocessing script.
    """
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    try:
        # Update status to processing
        processing_status[task_id] = {
            "status": "processing",
            "message": f"Processing {filename}...",
            "progress": 0
        }
        
        # Simulate long preprocessing - replace this with your actual script
        logger.info(f"Starting preprocessing for {filename}")
        
        # Example: simulate progress updates
        for i in range(5):
            time.sleep(2)  # Replace with actual processing
            processing_status[task_id] = {
                "status": "processing",
                "message": f"Processing {filename}... Step {i+1}/5",
                "progress": (i + 1) * 20
            }
            logger.info(f"Processing progress: {(i + 1) * 20}%")
        
        # Add your actual preprocessing logic here
        # For example:
        # - Extract text from documents
        # - Generate embeddings
        # - Update vector database
        # - Process with NLP models
        # - etc.
        
        # Mark as completed
        processing_status[task_id] = {
            "status": "completed",
            "message": f"Successfully processed {filename}",
            "progress": 100
        }
        logger.info(f"Completed preprocessing for {filename}")
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}", exc_info=True)
        processing_status[task_id] = {
            "status": "failed",
            "message": f"Failed to process {filename}: {str(e)}",
            "progress": 0
        }
async def _regenerate_agent_with_knowledge(
    conversation_context: list[dict], 
    agent_data: dict, 
    agent_folder_path: Path,
    uploaded_filename: str
) -> dict | None:
    """
    Regenerate agent capabilities and summary after uploading knowledge files.
    This updates the agent's knowledge domains and capabilities based on new files.
    """

    logger = logging.getLogger(__name__)

    try:
        # Get the list of uploaded files
        docs_folder = agent_folder_path / "docs"
        if not docs_folder.exists():
            logger.warning("Docs folder does not exist")
            return None

        # Get all files in the folder
        all_files_in_folder = [f.name for f in docs_folder.iterdir() if f.is_file()]
        
        # For this specific regeneration, we want to focus on the newly uploaded file
        # and any files that were mentioned in the conversation context
        current_session_files = [uploaded_filename]
        
        # Check conversation context for other files uploaded in this session
        for message in conversation_context:
            if message.get('role') == 'user' and 'uploaded knowledge file:' in message.get('content', ''):
                content = message.get('content', '')
                prev_filename = content.split('uploaded knowledge file:')[-1].strip()
                if prev_filename and prev_filename not in current_session_files:
                    current_session_files.append(prev_filename)
        
        logger.info(f"Current session files: {current_session_files}")
        logger.info(f"All files in folder: {all_files_in_folder}")

        # Create a message about the new knowledge
        knowledge_message = {
            "role": "assistant",
            "content": f"I've uploaded the knowledge file '{uploaded_filename}' to your agent. This file contains additional information that will help your agent provide more accurate and comprehensive responses. The agent now has access to {len(current_session_files)} knowledge files from this session: {', '.join(current_session_files)}."
        }
        conversation_context.append(knowledge_message)

        # Use existing agent_data to maintain consistency
        existing_agent_name = agent_data.get("name", "Custom Agent")
        existing_agent_description = agent_data.get("description", "A specialized agent for your needs")
        existing_capabilities = agent_data.get("capabilities", {})
        
        # Merge new knowledge with existing agent requirements
        # Don't re-extract requirements from scratch - use existing ones and enhance them
        agent_requirements = {
            "name": existing_agent_name,
            "description": existing_agent_description,
            "capabilities": existing_capabilities.get("capabilities", []),
            "knowledge_domains": existing_capabilities.get("knowledge", []),
            "workflows": existing_capabilities.get("workflow", []),
            "tools": existing_capabilities.get("tools", []),
            "is_complete": True  # Assume complete since we're enhancing existing agent
        }
        
        # Add new knowledge domains from uploaded files
        for filename in current_session_files:
            file_knowledge = f"Knowledge from {filename}"
            if file_knowledge not in agent_requirements["knowledge_domains"]:
                agent_requirements["knowledge_domains"].append(file_knowledge)
        
        # Analyze conversation completeness with new knowledge
        conversation_analysis = await analyze_conversation_completeness(conversation_context)
        
        # Generate updated capabilities using existing agent context
        # Create enhanced Dana code that reflects the existing agent + new knowledge
        enhanced_dana_code = f'''
agent {existing_agent_name.replace(" ", "_").lower()}:
    description : str = "{existing_agent_description}"
    
    solve(input : str) -> str:
        # This agent has access to knowledge files in ./docs
        # Original capabilities: {", ".join(agent_requirements["capabilities"])}
        # Knowledge domains: {", ".join(agent_requirements["knowledge_domains"])}
        # Workflows: {", ".join(agent_requirements["workflows"])}
        # Tools: {", ".join(agent_requirements["tools"])}
        # Additional knowledge files: {", ".join(current_session_files)}
        return "Enhanced agent with additional knowledge capabilities"
'''
        
        updated_capabilities = await analyze_agent_capabilities(
            enhanced_dana_code,
            conversation_context,
            None  # No multi_file_project for this regeneration
        )

        # Update the knowledges.na file with new knowledge domains
        if updated_capabilities:
            # Preserve existing capabilities and merge with new ones
            existing_knowledge = existing_capabilities.get("knowledge", [])
            existing_workflow = existing_capabilities.get("workflow", [])
            existing_tools = existing_capabilities.get("tools", [])
            existing_summary = existing_capabilities.get("summary", "")
            
            # Merge new knowledge domains with existing ones
            merged_knowledge = list(set(existing_knowledge + agent_requirements["knowledge_domains"]))
            
            # Update the capabilities to preserve existing information
            updated_capabilities.update({
                "knowledge": merged_knowledge,
                "workflow": existing_workflow,  # Preserve existing workflows
                "tools": existing_tools,  # Preserve existing tools
                "summary": existing_summary if existing_summary else updated_capabilities.get("summary", "")  # Preserve existing summary
            })
            
            await _update_knowledges_file(agent_folder_path, merged_knowledge)
            
            logger.info(f"Preserved existing capabilities: {existing_capabilities}")
            logger.info(f"Updated capabilities: {updated_capabilities}")

        logger.info(f"Successfully regenerated agent capabilities with new knowledge")
        return updated_capabilities

    except Exception as e:
        logger.error(f"Error regenerating agent with knowledge: {e}", exc_info=True)
        return None


async def _update_knowledges_file(agent_folder_path: Path, knowledge_domains: list[str]):
    """
    Update the knowledges.na file with new knowledge domains.
    """

    logger = logging.getLogger(__name__)

    try:
        knowledges_file = agent_folder_path / "knowledges.na"
        
        # Create or update knowledges.na content
        content = '"""\n'
        content += 'Knowledge domains for this agent:\n\n'
        
        for domain in knowledge_domains:
            content += f"- {domain}\n"
        
        content += '\nThis agent has access to knowledge files in the ./docs folder.\n'
        content += '"""\n\n'
        content += '# Knowledge domains are automatically managed based on uploaded files\n'
        content += '# and conversation context.\n'

        with open(knowledges_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Updated knowledges.na with {len(knowledge_domains)} knowledge domains")
        
    except Exception as e:
        logger.error(f"Error updating knowledges.na: {e}")


async def _generate_upload_response(
    filename: str, 
    agent_folder_path: Path, 
    updated_capabilities: dict | None,
    conversation_context: list[dict] = None
) -> str:
    """
    Generate a simple response about the uploaded knowledge file and ask relevant questions.
    """

    logger = logging.getLogger(__name__)

    try:
        # Simple confirmation
        response = f"✅ I received your knowledge file: `{filename}`\n\n"
        
        # Ask relevant questions to complete the description phase
        response += "**To help complete your agent description, please tell me:**\n\n"
        
        # Generate contextual questions based on the file type
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension in ['pdf', 'doc', 'docx']:
            response += "• What specific information from this document should Georgia focus on?\n"
            response += "• How should Georgia use this knowledge to help users?\n"
        elif file_extension in ['csv', 'json']:
            response += "• What kind of data analysis should Georgia perform with this information?\n"
            response += "• What insights should Georgia provide from this data?\n"
        elif file_extension in ['txt', 'md']:
            response += "• What key topics or concepts from this text should Georgia understand?\n"
            response += "• How should Georgia apply this knowledge in conversations?\n"
        else:
            response += "• What specific capabilities should Georgia have with this knowledge?\n"
            response += "• How should Georgia use this information to help users?\n"
        
        response += "\nOnce you provide these details, we can proceed to build your agent!"
        
        return response

    except Exception as e:
        logger.error(f"Error generating upload response: {e}")
        return f"✅ I received your knowledge file: `{filename}`. Please tell me how your agent should use this information."


@router.post("/generate-from-prompt", response_model=AgentGenerationResponse)
async def generate_agent_from_prompt(request: dict, db: Session = Depends(db.get_db)):
    """
    Phase 2 specific endpoint for generating agent files from a prompt.
    
    This endpoint takes a prompt, conversation messages, and agent summary to generate
    the actual .na files for Phase 2 of the agent generation flow.
    
    Expected request format:
    {
        "prompt": "Specific prompt for generating agent files",
        "messages": [{"role": "user", "content": "..."}, ...],
        "agent_summary": {
            "name": "Agent Name",
            "description": "Agent description",
            "capabilities": {
                "knowledge": ["domain1", "domain2"],
                "workflow": ["step1", "step2"],
                "tools": ["tool1", "tool2"]
            }
        },
        "multi_file": false
    }
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Received Phase 2 generation request with prompt")
        
        # Extract request data
        prompt = request.get("prompt", "")
        messages = request.get("messages", [])
        agent_summary = request.get("agent_summary", {})
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required for Phase 2 generation")
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required for Phase 2 generation")
        
        if not agent_summary:
            raise HTTPException(status_code=400, detail="Agent summary is required for Phase 2 generation")
        
        logger.info(f"Processing Phase 2 generation with prompt: {prompt[:100]}...")
        logger.info(f"Agent summary: {agent_summary.get('name', 'Unknown')}")
        
        # Use AgentManager for consistent handling
        from ..agent_manager import get_agent_manager
        agent_manager = get_agent_manager()
        
        # Generate agent code using AgentManager
        result = await agent_manager.generate_agent_code(
            agent_metadata=agent_summary,
            messages=messages,
            prompt=prompt
        )
        
        # Convert result to AgentGenerationResponse
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
        logger.error(f"Error in generate_agent_from_prompt endpoint: {e}", exc_info=True)
        return AgentGenerationResponse(
            success=False,
            dana_code="",
            error=f"Failed to generate agent from prompt: {str(e)}"
        )


async def _store_single_file_in_phase1_folder(
    agent_folder: str, 
    agent_name: str, 
    agent_description: str, 
    dana_code: str
) -> list[str]:
    """
    Store a single-file agent in the Phase 1 folder.
    
    Args:
        agent_folder: Path to the Phase 1 folder
        agent_name: Name of the agent
        agent_description: Description of the agent
        dana_code: Dana code content
        
    Returns:
        List of file paths created
    """
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Create agent folder if it doesn't exist
    agent_folder_path = Path(agent_folder)
    agent_folder_path.mkdir(parents=True, exist_ok=True)
    
    file_paths = []
    
    # Create agent.na file
    agent_file = agent_folder_path / "agent.na"
    with open(agent_file, "w", encoding="utf-8") as f:
        f.write(dana_code)
    file_paths.append(str(agent_file))
    logger.info(f"Created agent.na file: {agent_file}")
    
    # Create or update metadata.json
    metadata_file = agent_folder_path / "metadata.json"
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": ["agent.na"],
        "folder_path": str(agent_folder_path.resolve()),
        "generation_type": "single_file",
        "phase": "code_generated",
        "phase_1_folder": True
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Updated metadata.json: {metadata_file}")
    
    logger.info(f"Stored single-file agent in Phase 1 folder. Created {len(file_paths)} files: {file_paths}")
    return file_paths


async def _store_multi_file_in_phase1_folder(
    agent_folder: str, 
    agent_name: str, 
    agent_description: str, 
    multi_file_project: dict
) -> list[str]:
    """
    Store a multi-file agent in the Phase 1 folder.
    
    Args:
        agent_folder: Path to the Phase 1 folder
        agent_name: Name of the agent
        agent_description: Description of the agent
        multi_file_project: Multi-file project data
        
    Returns:
        List of file paths created
    """
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Create agent folder if it doesn't exist
    agent_folder_path = Path(agent_folder)
    agent_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure docs folder exists
    docs_folder = agent_folder_path / "docs"
    docs_folder.mkdir(exist_ok=True)
    logger.info(f"Ensured docs folder exists: {docs_folder}")
    
    file_paths = []
    
    # Create files from multi-file project
    for file_info in multi_file_project["files"]:
        filename = file_info["filename"]
        if not filename.endswith(".na"):
            filename += ".na"
        
        file_path = agent_folder_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"])
        file_paths.append(str(file_path))
        logger.info(f"Created file: {file_path}")
    
    # Create or update metadata.json
    metadata_file = agent_folder_path / "metadata.json"
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": [str(Path(p).name) for p in file_paths],
        "folder_path": str(agent_folder_path.resolve()),
        "generation_type": "multi_file",
        "phase": "code_generated",
        "phase_1_folder": True,
        "main_file": multi_file_project.get("main_file", "main.na"),
        "structure_type": multi_file_project.get("structure_type", "complex")
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Updated metadata.json: {metadata_file}")
    
    logger.info(f"Stored multi-file agent in Phase 1 folder. Created {len(file_paths)} files: {file_paths}")
    return file_paths


@router.post("/deep-train")
async def deep_train_agent(request: dict):
    """
    Deep Training endpoint for Georgia - placeholder for future implementation.
    
    This endpoint will eventually implement advanced training techniques for Georgia
    including reinforcement learning, advanced pattern recognition, and enhanced
    reasoning capabilities.
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Received deep training request for Georgia")
        
        # Extract request parameters
        agent_id = request.get("agent_id")
        agent_folder = request.get("agent_folder")
        training_type = request.get("training_type", "deep")
        training_parameters = request.get("training_parameters", {})
        
        # Validate required parameters
        if not agent_id and not agent_folder:
            raise HTTPException(
                status_code=400,
                detail="Either agent_id or agent_folder must be provided"
            )
        
        # Generate unique training ID
        training_id = f"deep_training_{int(time.time() * 1000)}"
        
        # TODO: Implement actual deep training logic here
        # This is where the advanced training algorithms would be implemented:
        # - Reinforcement learning from user feedback
        # - Advanced pattern recognition training
        # - Knowledge graph enhancement
        # - Multi-modal learning capabilities
        # - Continuous learning from conversations
        
        logger.info(f"Deep training initiated for agent {agent_id} with training ID: {training_id}")
        
        # For now, return a placeholder response
        return {
            "success": True,
            "training_id": training_id,
            "message": "Deep training has been initiated for Georgia. This process will enhance her capabilities through advanced machine learning techniques.",
            "estimated_duration": 300,  # 5 minutes in seconds
            "training_parameters": training_parameters,
            "status": "initiated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deep training endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Deep training failed: {str(e)}"
        )
