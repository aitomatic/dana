"""Agent routers v2 - API endpoints for agent-knowledge pack associations."""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from dana.studio.api.core.database import get_db
from dana.studio.api.core.models import KnowledgePack
from dana.studio.api.repositories import (
    get_agent_repo,
    get_domain_knowledge_repo,
    AbstractAgentRepo,
    AbstractDomainKnowledgeRepo,
)
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Schemas
class AssociateKPRequest(BaseModel):
    """Request schema for associating a knowledge pack with an agent."""

    kp_id: int


class AssociateKPResponse(BaseModel):
    """Response schema for knowledge pack association."""

    success: bool
    message: str
    agent_id: int
    kp_id: int


# Endpoints
@router.post("/{agent_id}/associate", response_model=AssociateKPResponse)
async def associate_agent_with_kp(
    agent_id: int,
    request: AssociateKPRequest,
    agent_repo: type[AbstractAgentRepo] = Depends(get_agent_repo),
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Associate an agent with a knowledge pack.

    This endpoint:
    1. Validates that both agent and knowledge pack exist
    2. Replaces the agent's knows folder with the KP's knows folder
    3. Updates agent metadata to track the association

    Args:
        agent_id: The ID of the agent to associate
        request: Request body containing kp_id

    Returns:
        AssociateKPResponse with success status and details

    Raises:
        HTTPException 404: If agent or knowledge pack not found
        HTTPException 500: If file system operations fail
    """
    try:
        # 1. Validate agent exists
        agent = await agent_repo.get_agent(agent_id, db=db)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # 2. Validate knowledge pack exists in database
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == request.kp_id).first()
        if not kp:
            raise HTTPException(status_code=404, detail=f"Knowledge pack {request.kp_id} not found")

        # 3. Get KP folder and validate knows folder exists
        try:
            kp_folder = kb_repo.get_knowledge_pack_folder(request.kp_id)
            kp_knows_folder = kp_folder / KNOW_FOLDER_NAME
            if not kp_knows_folder.exists():
                raise HTTPException(status_code=404, detail=f"Knowledge pack {request.kp_id} knows folder not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting knowledge pack folder {request.kp_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to access knowledge pack folder: {str(e)}")

        # 4. Get agent folder path
        agent_folder_path = agent.config.get("folder_path") if agent.config is not None else None
        if not agent_folder_path:
            agent_folder_path = f"agents/agent_{agent_id}"

        agent_folder = Path(agent_folder_path)
        agent_folder.mkdir(parents=True, exist_ok=True)

        agent_knows_folder = agent_folder / KNOW_FOLDER_NAME

        kp_structure_file = kp_folder / "domain_knowledge.json"
        agent_structure_file = agent_folder / "domain_knowledge.json"

        kp_status_file = kp_folder / "knowledge_status.json"
        agent_status_file = agent_knows_folder / "knowledge_status.json"

        # COPY all_interview sessions
        kp_template_folder = kp_folder / "templates"
        interview_sessions = kp_template_folder.glob("**/interview_notes.md")
        # 5. Replace existing knows folder
        try:
            # Delete existing knows folder if it exists
            if agent_knows_folder.exists():
                shutil.rmtree(agent_knows_folder)
                logger.info(f"Deleted existing knows folder: {agent_knows_folder}")

            # Copy knows folder from KP to agent
            shutil.copytree(kp_knows_folder, agent_knows_folder)
            logger.info(f"Copied knows folder from {kp_knows_folder} to {agent_knows_folder}")
            # Copy domain_knowledge.json from KP to agent
            if kp_status_file.exists():
                shutil.copy(kp_structure_file, agent_structure_file)
                logger.info(f"Copied domain_knowledge.json from {kp_structure_file} to {agent_structure_file}")
            # Copy knowledge_status.json from KP to agent
            if kp_status_file.exists():
                shutil.copy(kp_status_file, agent_status_file)
                logger.info(f"Copied knowledge_status.json from {kp_status_file} to {agent_status_file}")

            for i, interview_file in enumerate(interview_sessions):
                target_file = agent_knows_folder / f"interview_notes_{i}.md"
                with open(str(target_file), "w") as f:
                    f.write(interview_file.read_text())
        except Exception as e:
            logger.error(f"Error copying knows folder: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to copy knows folder: {str(e)}")

        # 6. Update agent metadata
        config_updates = {"associated_kps": [request.kp_id], "folder_path": str(agent_folder_path)}
        await agent_repo.update_agent_config(agent_id, config_updates, db=db)
        logger.info(f"Updated agent {agent_id} metadata with KP {request.kp_id}")

        return AssociateKPResponse(
            success=True,
            message=f"Successfully associated agent {agent_id} with knowledge pack {request.kp_id}",
            agent_id=agent_id,
            kp_id=request.kp_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error associating agent {agent_id} with KP {request.kp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/disassociate", response_model=AssociateKPResponse)
async def disassociate_agent_from_kp(
    agent_id: int,
    request: AssociateKPRequest,
    agent_repo: type[AbstractAgentRepo] = Depends(get_agent_repo),
    db: Session = Depends(get_db),
):
    """
    Disassociate an agent from a knowledge pack.

    This endpoint:
    1. Validates that the agent exists and is associated with the KP
    2. Removes the agent's knows folder
    3. Clears the KP association from agent metadata

    Args:
        agent_id: The ID of the agent to disassociate
        request: Request body containing kp_id

    Returns:
        AssociateKPResponse with success status and details

    Raises:
        HTTPException 404: If agent not found
        HTTPException 400: If KP is not associated with the agent
        HTTPException 500: If file system operations fail
    """
    try:
        # 1. Validate agent exists
        agent = await agent_repo.get_agent(agent_id, db=db)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # 2. Check if KP is associated
        associated_kps = agent.config.get("associated_kps", []) if agent.config is not None else []
        if request.kp_id not in associated_kps:
            raise HTTPException(status_code=400, detail=f"Knowledge pack {request.kp_id} is not associated with agent {agent_id}")

        # 3. Get agent folder path
        agent_folder_path = agent.config.get("folder_path") if agent.config is not None else None
        if not agent_folder_path:
            agent_folder_path = f"agents/agent_{agent_id}"

        agent_folder = Path(agent_folder_path)
        agent_knows_folder = agent_folder / KNOW_FOLDER_NAME
        agent_structure_file = agent_folder / "domain_knowledge.json"
        agent_status_file = agent_knows_folder / "knowledge_status.json"

        # 4. Delete knows folder
        try:
            if agent_knows_folder.exists():
                shutil.rmtree(agent_knows_folder)
                logger.info(f"Deleted knows folder: {agent_knows_folder}")
            if agent_structure_file.exists():
                agent_structure_file.unlink()
                logger.info(f"Deleted domain_knowledge.json: {agent_structure_file}")
            if agent_status_file.exists():
                agent_status_file.unlink()
                logger.info(f"Deleted knowledge_status.json: {agent_status_file}")
        except Exception as e:
            logger.error(f"Error deleting knows folder: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete knows folder: {str(e)}")

        # 5. Clear association from metadata
        config_updates = {"associated_kps": []}
        await agent_repo.update_agent_config(agent_id, config_updates, db=db)
        logger.info(f"Cleared KP association for agent {agent_id}")

        return AssociateKPResponse(
            success=True,
            message=f"Successfully disassociated agent {agent_id} from knowledge pack {request.kp_id}",
            agent_id=agent_id,
            kp_id=request.kp_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error disassociating agent {agent_id} from KP {request.kp_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
