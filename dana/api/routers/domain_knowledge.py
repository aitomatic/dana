"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import (
    DomainKnowledgeTree,
    IntentDetectionRequest,
    IntentDetectionResponse,
    DomainKnowledgeUpdateRequest,
    DomainKnowledgeUpdateResponse,
    ChatWithIntentRequest,
    ChatWithIntentResponse,
)
from dana.api.services.domain_knowledge_service import get_domain_knowledge_service, DomainKnowledgeService
from dana.api.services.intent_detection_service import get_intent_detection_service, IntentDetectionService
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["domain-knowledge"])


@router.get("/{agent_id}/domain-knowledge", response_model=DomainKnowledgeTree | dict)
async def get_agent_domain_knowledge(
    agent_id: int, domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service), db: Session = Depends(get_db)
):
    """
    Get the current domain knowledge tree for an agent.

    Args:
        agent_id: Agent ID
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        DomainKnowledgeTree or empty dict if none exists
    """
    try:
        logger.info(f"Fetching domain knowledge for agent {agent_id}")

        tree = await domain_service.get_agent_domain_knowledge(agent_id, db)

        if tree:
            return tree
        else:
            return {"message": "No domain knowledge found for this agent"}

    except Exception as e:
        logger.error(f"Error fetching domain knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/domain-knowledge/initialize", response_model=DomainKnowledgeTree)
async def initialize_agent_domain_knowledge(
    agent_id: int, domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service), db: Session = Depends(get_db)
):
    """
    Initialize domain knowledge tree for an agent based on its description.

    Args:
        agent_id: Agent ID
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        DomainKnowledgeTree: Newly created domain knowledge tree
    """
    try:
        logger.info(f"Initializing domain knowledge for agent {agent_id}")

        # Get agent info
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create initial domain knowledge
        tree = await domain_service.create_initial_domain_knowledge(
            agent_id=agent_id, agent_name=agent.name, agent_description=agent.description or "", db=db
        )

        if not tree:
            raise HTTPException(status_code=500, detail="Failed to create domain knowledge tree")

        return tree

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing domain knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/domain-knowledge/detect-intent", response_model=IntentDetectionResponse)
async def detect_intent(
    agent_id: int,
    request: IntentDetectionRequest,
    intent_service: IntentDetectionService = Depends(get_intent_detection_service),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Detect user intent for domain knowledge management.

    Args:
        agent_id: Agent ID
        request: Intent detection request
        intent_service: Intent detection service
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        IntentDetectionResponse: Detected intent and extracted entities
    """
    try:
        logger.info(f"Detecting intent for agent {agent_id}: {request.user_message[:100]}...")

        # Get current domain knowledge for context
        if not request.current_domain_tree:
            request.current_domain_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)

        # Set agent_id in request
        request.agent_id = agent_id

        # Detect intent
        response = await intent_service.detect_intent(request)

        logger.info(f"Detected intent: {response.intent} for agent {agent_id}")
        return response

    except Exception as e:
        logger.error(f"Error detecting intent for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/domain-knowledge/update", response_model=DomainKnowledgeUpdateResponse)
async def update_domain_knowledge(
    agent_id: int,
    request: DomainKnowledgeUpdateRequest,
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Update domain knowledge tree based on detected intent.

    Args:
        agent_id: Agent ID
        request: Update request with intent and entities
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        DomainKnowledgeUpdateResponse: Update result and new tree
    """
    try:
        logger.info(f"Updating domain knowledge for agent {agent_id}, intent: {request.intent}")

        # Set agent_id in request
        request.agent_id = agent_id

        if request.intent == "add_information":
            topic = request.entities.get("topic")
            parent = request.entities.get("parent")

            if not topic:
                return DomainKnowledgeUpdateResponse(success=False, error="No topic specified for adding information")

            response = await domain_service.add_knowledge_node(agent_id=agent_id, topic=topic, parent_topic=parent, db=db)

        elif request.intent == "refresh_domain_knowledge":
            response = await domain_service.refresh_domain_knowledge(agent_id=agent_id, context=request.user_message, db=db)

        else:
            return DomainKnowledgeUpdateResponse(success=False, error=f"Unsupported intent for domain knowledge update: {request.intent}")

        return response

    except Exception as e:
        logger.error(f"Error updating domain knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/chat-with-intent", response_model=ChatWithIntentResponse)
async def chat_with_intent_detection(
    agent_id: int,
    request: ChatWithIntentRequest,
    intent_service: IntentDetectionService = Depends(get_intent_detection_service),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Enhanced chat endpoint with intent detection and domain knowledge management.

    This endpoint:
    1. Detects user intent (if enabled)
    2. Updates domain knowledge if needed
    3. Processes the chat message
    4. Returns enhanced response with intent info

    Args:
        agent_id: Agent ID
        request: Chat request with intent detection enabled
        intent_service: Intent detection service
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        ChatWithIntentResponse: Chat response with intent detection results
    """
    try:
        logger.info(f"Processing chat with intent detection for agent {agent_id}")

        detected_intent = None
        domain_tree_updated = False
        updated_tree = None

        # Step 1: Intent detection (if enabled)
        if request.detect_intent:
            # Get current domain tree
            current_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)

            # Detect intent
            intent_request = IntentDetectionRequest(
                user_message=request.message,
                chat_history=[],  # Could be populated from conversation history
                current_domain_tree=current_tree,
                agent_id=agent_id,
            )

            intent_response = await intent_service.detect_intent(intent_request)
            detected_intent = intent_response.intent

            # Step 2: Update domain knowledge if needed
            if detected_intent in ["add_information", "refresh_domain_knowledge"]:
                update_request = DomainKnowledgeUpdateRequest(
                    agent_id=agent_id, intent=detected_intent, entities=intent_response.entities, user_message=request.message
                )

                update_response = await domain_service.update_domain_knowledge(agent_id=agent_id, request=update_request, db=db)

                if update_response.success:
                    domain_tree_updated = True
                    updated_tree = update_response.updated_tree

        # Step 3: Process the chat message
        # For now, return a placeholder response
        # In the future, this would integrate with the existing chat service
        agent_response = (
            "I understand your message and have updated my knowledge accordingly." if domain_tree_updated else "Thank you for your message."
        )

        return ChatWithIntentResponse(
            success=True,
            message=request.message,
            conversation_id=request.conversation_id or 0,
            message_id=0,  # Would be generated by chat service
            agent_response=agent_response,
            context=request.context,
            detected_intent=detected_intent,
            domain_tree_updated=domain_tree_updated,
            updated_tree=updated_tree,
        )

    except Exception as e:
        logger.error(f"Error processing chat with intent for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/domain-knowledge")
async def delete_agent_domain_knowledge(
    agent_id: int, domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service), db: Session = Depends(get_db)
):
    """
    Delete domain knowledge tree for an agent.

    Args:
        agent_id: Agent ID
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting domain knowledge for agent {agent_id}")

        # Get agent
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Remove domain knowledge file path from config
        if agent.config:
            domain_knowledge_path = agent.config.get("domain_knowledge_path")
            if domain_knowledge_path:
                # Remove file
                from pathlib import Path

                file_path = Path(domain_knowledge_path)
                if file_path.exists():
                    file_path.unlink()

                # Update config
                config = agent.config.copy()
                del config["domain_knowledge_path"]
                agent.config = config
                db.commit()

        return {"message": f"Domain knowledge deleted for agent {agent_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting domain knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/domain-knowledge/versions")
async def get_domain_knowledge_versions(
    agent_id: int, domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service), db: Session = Depends(get_db)
):
    """
    Get available versions for agent's domain knowledge (last 5 versions).

    Args:
        agent_id: Agent ID
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        List of available versions with metadata
    """
    try:
        logger.info(f"Fetching version history for agent {agent_id}")

        # Check if agent exists
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        versions = await domain_service.get_version_history(agent_id)

        return {"agent_id": agent_id, "versions": versions, "total_versions": len(versions)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching version history for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/domain-knowledge/revert/{version}", response_model=DomainKnowledgeUpdateResponse)
async def revert_domain_knowledge_to_version(
    agent_id: int,
    version: int,
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Revert domain knowledge to a specific version.

    Args:
        agent_id: Agent ID
        version: Version number to revert to
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        DomainKnowledgeUpdateResponse: Revert result with restored tree
    """
    try:
        logger.info(f"Reverting domain knowledge for agent {agent_id} to version {version}")

        # Check if agent exists
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Validate version is positive
        if version <= 0:
            raise HTTPException(status_code=400, detail="Version must be a positive integer")

        # Perform the revert
        response = await domain_service.revert_to_version(agent_id, version, db)

        if not response.success:
            # Use appropriate HTTP status code based on error
            if "not found" in (response.error or "").lower():
                raise HTTPException(status_code=404, detail=response.error)
            elif "already the current" in (response.error or "").lower():
                raise HTTPException(status_code=400, detail=response.error)
            else:
                raise HTTPException(status_code=500, detail=response.error)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverting domain knowledge for agent {agent_id} to version {version}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/domain-knowledge/version/{version}", response_model=DomainKnowledgeTree)
async def get_specific_domain_knowledge_version(
    agent_id: int,
    version: int,
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Get a specific version of domain knowledge without reverting to it.

    Args:
        agent_id: Agent ID
        version: Version number to retrieve
        domain_service: Domain knowledge service
        db: Database session

    Returns:
        DomainKnowledgeTree: The requested version of the tree
    """
    try:
        logger.info(f"Fetching version {version} of domain knowledge for agent {agent_id}")

        # Check if agent exists
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Validate version is positive
        if version <= 0:
            raise HTTPException(status_code=400, detail="Version must be a positive integer")

        # Check if it's the current version
        current_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)
        if current_tree and current_tree.version == version:
            return current_tree

        # Try to load from version history
        version_dir = domain_service.get_version_history_dir(agent_id)
        version_file = version_dir / f"v{version}.json"

        if not version_file.exists():
            raise HTTPException(status_code=404, detail=f"Version {version} not found")

        # Load the version
        import json

        with open(version_file, encoding="utf-8") as f:
            data = json.load(f)

        return DomainKnowledgeTree(**data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching version {version} for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _load_flatten_knowledge_content(topic_path: str, folder_path: str) -> dict:
    """
    Load knowledge content from flattened file structure.

    The topic_path like 'Fundamental Analysis - Income Statement Analysis - Revenue Recognition'
    maps to a single JSON file in the knows/ folder with various naming conventions.
    """
    # Create safe filename variations
    safe_topic = (
        topic_path.replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(",", "_")
        .replace("'", "_")
        .replace('"', "_")
    )

    # Look for the knowledge file
    knows_folder = os.path.join(folder_path, "knows")
    if not os.path.exists(knows_folder):
        raise HTTPException(status_code=404, detail="Knowledge folder not found")

    # Try different filename formats
    possible_filenames = [
        f"{safe_topic}.json",
        f"{topic_path.replace(' - ', '___').replace(' ', '_')}.json",
        f"{topic_path.replace(' - ', '_').replace(' ', '_')}.json",
        f"{topic_path.replace(' ', '_').replace('-', '_')}.json",
        # Also try with different separators
        f"{topic_path.replace(' - ', '__').replace(' ', '_')}.json",
        f"{safe_topic.lower()}.json",
        f"{safe_topic.upper()}.json",
    ]

    knowledge_file_path = None
    for filename in possible_filenames:
        file_path = os.path.join(knows_folder, filename)
        if os.path.exists(file_path):
            knowledge_file_path = file_path
            break

    # If no exact match, try to find by partial matching
    if not knowledge_file_path:
        for filename in os.listdir(knows_folder):
            if filename.endswith(".json") and filename != "knowledge_status.json":
                # Check if the topic components are in the filename
                topic_parts = topic_path.split(" - ")
                filename_without_ext = filename[:-5]  # Remove .json

                # Check if all topic parts are present in filename
                parts_found = 0
                for part in topic_parts:
                    part_variations = [
                        part.replace(" ", "_"),
                        part.replace(" ", "_").lower(),
                        part.replace(" ", "_").upper(),
                        part.replace(" ", ""),
                        part.lower(),
                        part.upper(),
                    ]

                    if any(var in filename_without_ext for var in part_variations):
                        parts_found += 1

                # If most parts are found, consider it a match
                if parts_found >= len(topic_parts) * 0.8:  # 80% of parts found
                    knowledge_file_path = os.path.join(knows_folder, filename)
                    break

    if not knowledge_file_path:
        # List available files for debugging
        available_files = [f for f in os.listdir(knows_folder) if f.endswith(".json") and f != "knowledge_status.json"]

        return {
            "success": False,
            "message": "Knowledge content not found in flattened structure",
            "topic_path": topic_path,
            "available_files": available_files[:10],  # Limit to first 10 files
        }

    # Read the knowledge file
    try:
        with open(knowledge_file_path, encoding="utf-8") as f:
            knowledge_data = json.load(f)

        return {
            "success": True,
            "topic_path": topic_path,
            "content": knowledge_data,
            "file_path": knowledge_file_path,
            "structure_type": "flattened",
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in knowledge file {knowledge_file_path}: {e}")
        raise HTTPException(status_code=500, detail="Knowledge file is corrupted")
    except Exception as e:
        logger.error(f"Error reading knowledge file {knowledge_file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading knowledge file: {str(e)}")


def _load_hierarchical_knowledge_content(topic_path: str, folder_path: str) -> dict:
    """
    Load knowledge content from hierarchical folder structure.

    The topic_path like 'Fundamental Analysis - Income Statement Analysis - Revenue Recognition'
    maps to folder structure: knows/Fundamental_Analysis/Income_Statement_Analysis/Revenue_Recognition.json

    Note: The root topic (e.g., 'Fundamental Analysis') is the top-level folder under 'knows/'
    """
    # Split the topic path into components
    topic_parts = topic_path.split(" - ")

    # Convert each part to folder-safe format
    knows_folder = os.path.join(folder_path, "knows")

    root_know_dir = [fd for fd in os.listdir(knows_folder) if os.path.isdir(os.path.join(knows_folder, fd))]

    if len(root_know_dir) == 0:
        raise ValueError(f"No knowledge folder found in {knows_folder}")

    final_path = os.path.join(knows_folder, root_know_dir[0], *topic_parts, "knowledge.json")

    if not os.path.exists(final_path):
        raise FileNotFoundError(f"Knowledge file not found at {final_path}")

    with open(final_path, encoding="utf-8") as f:
        knowledge_data = json.load(f)

    return {"success": True, "topic_path": topic_path, "content": knowledge_data, "file_path": final_path, "structure_type": "hierarchical"}


@router.get("/{agent_id}/knowledge-content/{topic_path:path}")
async def get_topic_knowledge_content(agent_id: int, topic_path: str, db: Session = Depends(get_db)):
    """
    Get the generated knowledge content for a specific topic.

    Args:
        agent_id: Agent ID
        topic_path: The topic path (e.g., "Finance - Market Analysis")
        db: Database session

    Returns:
        dict: The knowledge content or error message
    """
    try:
        logger.info(f"Fetching knowledge content for agent {agent_id}, topic: {topic_path}")

        # Check if agent exists
        from dana.api.core.models import Agent

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get agent folder path
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = f"agents/agent_{agent_id}"

        logger.debug(f"Using folder path: {folder_path} for agent {agent_id}")

        # Log the topic path details for debugging
        topic_parts = topic_path.split(" - ")
        logger.debug(f"Topic path parts: {topic_parts} (total: {len(topic_parts)})")

        # Try hierarchical structure first (preferred)
        hierarchical_result = None
        flattened_result = None
        errors = []

        try:
            hierarchical_result = _load_hierarchical_knowledge_content(topic_path, folder_path)
            if hierarchical_result.get("success"):
                logger.info(f"Found knowledge content in hierarchical structure for agent {agent_id}, topic: {topic_path}")
                return hierarchical_result
        except Exception as e:
            errors.append(f"Hierarchical structure error: {str(e)}")
            logger.debug(f"Hierarchical structure failed for agent {agent_id}, topic {topic_path}: {e}")

        # Fall back to flattened structure
        try:
            flattened_result = _load_flatten_knowledge_content(topic_path, folder_path)
            if flattened_result.get("success"):
                logger.info(f"Found knowledge content in flattened structure for agent {agent_id}, topic: {topic_path}")
                return flattened_result
        except Exception as e:
            errors.append(f"Flattened structure error: {str(e)}")
            logger.debug(f"Flattened structure failed for agent {agent_id}, topic {topic_path}: {e}")

        # If both failed but we have results, return the one with more info
        if hierarchical_result and not hierarchical_result.get("success"):
            if flattened_result and not flattened_result.get("success"):
                # Both failed, return the hierarchical result with combined error info
                hierarchical_result["fallback_attempted"] = True
                hierarchical_result["flattened_error"] = flattened_result.get("message", "Unknown error")
                hierarchical_result["available_files_flattened"] = flattened_result.get("available_files", [])
                return hierarchical_result
            else:
                return hierarchical_result
        elif flattened_result and not flattened_result.get("success"):
            return flattened_result

        # If we get here, both structures failed with exceptions
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge content not found for topic '{topic_path}'. Tried both hierarchical and flattened structures. Errors: {'; '.join(errors)}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching knowledge content for agent {agent_id}, topic {topic_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
